"""Batch-evaluate every triplet in review/triplet_manifest.csv with RelSim,
CLIP, and DINO.

This replaces the original single-hardcoded-triplet version of this script
from Phase A/B (three fixed local test images) now that a real triplet
manifest exists (scripts/build_triplet_manifest.py). Requires the relsim
package, its checkpoint, and a GPU -- run this in the same environment
where the original eval_triplet.py was validated (school GPU cluster), not
locally and not on a bare Colab CPU/T4 runtime.

For each triplet, computes sim(anchor, positive) and sim(anchor, negative)
for all three models, and records correct = int(sim_pos > sim_neg) and
margin = sim_pos - sim_neg.

Resilience notes (added after a mid-run CUDA OOM on an oversized source
image, likely from Qwen2.5-VL's dynamic-resolution vision encoder blowing
up on a very large photo -- CLIP/DINO are not vulnerable since their
processors already resize to a fixed shape):
  - every downloaded image is capped to MAX_IMAGE_DIM on its longest side
    before being handed to any model;
  - a CUDA OOM on one (triplet, model) pair is caught, logged, and skipped
    (with an empty_cache()) instead of crashing the whole run;
  - results are saved incrementally, and re-running this script skips
    triplet_ids already present in review/triplet_results.csv, so a crash
    (this kind or any other) does not throw away already-computed GPU work.

Outputs:
  review/triplet_results.csv           -- one row per (triplet, model)
  review/triplet_accuracy_summary.csv  -- accuracy by relation_family x condition x model
"""
import io
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import requests
import torch
from PIL import Image

MANIFEST_PATH = "review/triplet_manifest.csv"
RESULTS_PATH = "review/triplet_results.csv"
SUMMARY_PATH = "review/triplet_accuracy_summary.csv"
DOWNLOAD_TIMEOUT = 8
MAX_WORKERS = 16
MAX_IMAGE_DIM = 1024
SAVE_EVERY = 5

print("Loading relsim...")
from relsim.relsim_score import relsim
relsim_model, relsim_preprocess = relsim(pretrained=True, checkpoint_dir='thaoshibe/relsim-qwenvl25-lora')

print("Loading CLIP...")
from transformers import CLIPModel, CLIPProcessor
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32", use_safetensors=True).to("cuda")
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

print("Loading DINO...")
from transformers import AutoImageProcessor, AutoModel
dino_processor = AutoImageProcessor.from_pretrained("facebook/dinov2-base")
dino_model = AutoModel.from_pretrained("facebook/dinov2-base", use_safetensors=True).to("cuda")


def download_image(url, timeout=DOWNLOAD_TIMEOUT):
    try:
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content)).convert("RGB")
        # Cap resolution so an unusually large source photo can't blow up
        # Qwen2.5-VL's dynamic-resolution vision encoder. Shrinks only,
        # preserves aspect ratio.
        img.thumbnail((MAX_IMAGE_DIM, MAX_IMAGE_DIM), Image.LANCZOS)
        return img
    except Exception:
        return None


def clip_sim(img_a, img_b):
    inputs = clip_processor(images=[img_a, img_b], return_tensors="pt").to("cuda")
    with torch.no_grad():
        out = clip_model.get_image_features(**inputs)
    # NOTE: on some transformers versions, get_image_features() returns a raw
    # tensor directly; on others it returns a BaseModelOutputWithPooling
    # wrapper whose .pooler_output holds the projected 512-d embedding
    # (verified against self-similarity == 1.0). Handle both.
    embeds = out.pooler_output if hasattr(out, "pooler_output") else out
    embeds = embeds / embeds.norm(dim=-1, keepdim=True)
    return (embeds[0] @ embeds[1]).item()


def dino_sim(img_a, img_b):
    inputs = dino_processor(images=[img_a, img_b], return_tensors="pt").to("cuda")
    with torch.no_grad():
        outputs = dino_model(**inputs)
    embeds = outputs.pooler_output
    embeds = embeds / embeds.norm(dim=-1, keepdim=True)
    return (embeds[0] @ embeds[1]).item()


def relsim_sim(img_a, img_b):
    a = relsim_preprocess(img_a)
    b = relsim_preprocess(img_b)
    return relsim_model(a, b)


SIM_FNS = [("relsim", relsim_sim), ("CLIP", clip_sim), ("DINO", dino_sim)]


def is_oom_error(exc):
    return "out of memory" in str(exc).lower()


def main():
    manifest = pd.read_csv(MANIFEST_PATH)
    print(f"Loaded {len(manifest)} triplets from {MANIFEST_PATH}")

    results = []
    done_ids = set()
    if os.path.exists(RESULTS_PATH):
        prev = pd.read_csv(RESULTS_PATH)
        results = prev.to_dict("records")
        done_ids = set(prev["triplet_id"].unique())
        print(f"Found existing {RESULTS_PATH} with {len(done_ids)} already-scored triplets -- resuming.")

    remaining = manifest[~manifest["triplet_id"].isin(done_ids)].reset_index(drop=True)
    print(f"{len(remaining)} triplets left to score")

    if len(remaining) == 0:
        print("Nothing left to do -- all triplets already scored.")
    else:
        needed = {}
        for _, r in remaining.iterrows():
            for role in ("anchor", "positive", "negative"):
                needed[r[f"{role}_hash"]] = r[f"{role}_url"]

        print(f"Downloading {len(needed)} unique images with {MAX_WORKERS} workers...")
        images = {}
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            futures = {ex.submit(download_image, url): h for h, url in needed.items()}
            done = 0
            for fut in as_completed(futures):
                h = futures[fut]
                img = fut.result()
                if img is not None:
                    images[h] = img
                done += 1
                if done % 20 == 0 or done == len(needed):
                    print(f"  {done}/{len(needed)} processed, {len(images)} downloaded ok")

        skipped = []
        print("\nScoring triplets...")
        for i, r in remaining.iterrows():
            a_h, p_h, n_h = r["anchor_hash"], r["positive_hash"], r["negative_hash"]
            if a_h not in images or p_h not in images or n_h not in images:
                skipped.append(r["triplet_id"])
                continue
            img_a, img_p, img_n = images[a_h], images[p_h], images[n_h]
            for model_name, sim_fn in SIM_FNS:
                try:
                    sim_pos = sim_fn(img_a, img_p)
                    sim_neg = sim_fn(img_a, img_n)
                except RuntimeError as e:
                    if not is_oom_error(e):
                        raise
                    print(f"  [OOM] skipping {r['triplet_id']} / {model_name}, clearing cache and continuing")
                    torch.cuda.empty_cache()
                    continue
                results.append({
                    "triplet_id": r["triplet_id"],
                    "relation_family": r["relation_family"],
                    "condition": r["condition"],
                    "model": model_name,
                    "sim_pos": sim_pos,
                    "sim_neg": sim_neg,
                    "margin": sim_pos - sim_neg,
                    "correct": int(sim_pos > sim_neg),
                })

            if (i + 1) % SAVE_EVERY == 0 or (i + 1) == len(remaining):
                pd.DataFrame(results).to_csv(RESULTS_PATH, index=False)
                print(f"  scored {i + 1}/{len(remaining)} remaining triplets (checkpoint saved)")

        if skipped:
            print(f"Skipped {len(skipped)} triplets due to failed image downloads: {skipped}")

    results_df = pd.DataFrame(results)
    results_df.to_csv(RESULTS_PATH, index=False)
    n_triplets_scored = results_df["triplet_id"].nunique() if len(results_df) else 0
    print(f"\nWrote {RESULTS_PATH}: {len(results_df)} rows covering {n_triplets_scored}/{len(manifest)} triplets")

    print("\n--- Accuracy by relation_family x condition x model ---")
    summary = results_df.groupby(["relation_family", "condition", "model"])["correct"].mean().unstack("model")
    print(summary)
    summary.to_csv(SUMMARY_PATH)
    print(f"\nWrote {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
