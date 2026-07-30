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

Outputs:
  review/triplet_results.csv           -- one row per (triplet, model)
  review/triplet_accuracy_summary.csv  -- accuracy by relation_family x condition x model
"""
import io
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
        return Image.open(io.BytesIO(resp.content)).convert("RGB")
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


def main():
    manifest = pd.read_csv(MANIFEST_PATH)
    print(f"Loaded {len(manifest)} triplets from {MANIFEST_PATH}")

    needed = {}
    for _, r in manifest.iterrows():
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

    results = []
    skipped = []
    print("\nScoring triplets...")
    for i, r in manifest.iterrows():
        a_h, p_h, n_h = r["anchor_hash"], r["positive_hash"], r["negative_hash"]
        if a_h not in images or p_h not in images or n_h not in images:
            skipped.append(r["triplet_id"])
            continue
        img_a, img_p, img_n = images[a_h], images[p_h], images[n_h]
        for model_name, sim_fn in SIM_FNS:
            sim_pos = sim_fn(img_a, img_p)
            sim_neg = sim_fn(img_a, img_n)
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
        if (i + 1) % 10 == 0:
            print(f"  scored {i + 1}/{len(manifest)} triplets")

    results_df = pd.DataFrame(results)
    results_df.to_csv(RESULTS_PATH, index=False)
    n_scored = len(manifest) - len(skipped)
    print(f"\nWrote {RESULTS_PATH}: {len(results_df)} rows ({n_scored}/{len(manifest)} triplets scored)")
    if skipped:
        print(f"Skipped {len(skipped)} triplets due to failed image downloads: {skipped}")

    print("\n--- Accuracy by relation_family x condition x model ---")
    summary = results_df.groupby(["relation_family", "condition", "model"])["correct"].mean().unstack("model")
    print(summary)
    summary.to_csv(SUMMARY_PATH)
    print(f"\nWrote {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
