"""Download images and compute CLIP embeddings for similarity retrieval.

This is step 1 of the retrieval pipeline used to propose (not decide!)
candidates for:
  - conflict-negative images (visually similar to a confirmed anchor, but
    not known to share its relation);
  - aligned-pair images (two confirmed same-family anchors that also turn
    out to look visually similar);
  - attribute-priority control triplets (pure appearance similarity, no
    relation-family logic involved at all).

Uses the same CLIP checkpoint as scripts/eval_triplet.py
(openai/clip-vit-base-patch32) so retrieval similarity stays consistent
with the actual scoring pipeline used later.

Per proposal Section 7.3, CLIP must never be used to auto-accept a
negative or positive -- it only proposes candidates. A human still has to
look at the actual images (via scripts/generate_similarity_gallery.py)
before anything is frozen into a triplet.

Anchors = every row in review/pool/confirmed_candidates.csv with decision=="fits".
Background pool = every row with decision=="boundary_reject" (these are
already human-vetted "looks related but isn't" cases -- excellent
conflict-negative material) plus a random sample from the full test split
to round out the pool, excluding anything already reviewed.

Outputs (under review/pool/):
  similarity_embeddings.npz        -- hashes + L2-normalized CLIP embeddings
  similarity_pool_metadata.csv     -- image_hash, group, family, url, caption, download_ok
  similarity_download_failures.csv -- rows that failed to download (link rot etc.)

Run this once. scripts/generate_similarity_gallery.py consumes the output
and can be re-run for free without re-downloading or re-embedding.
"""
import io
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd
import requests
import torch
from datasets import load_dataset
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

CONFIRMED_PATH = "review/pool/confirmed_candidates.csv"
OUT_DIR = "review/pool"
# Fixed draw size from the full test split (NOT a target background pool
# size -- see the stability note at the sampling call site). Some of these
# get filtered out post-hoc as confirmed_candidates.csv grows, so the actual
# background_random count will be a bit under this and shrink slowly over
# time; bump this constant (don't lower it) if that ever matters.
FIXED_BACKGROUND_DRAW = 700
RANDOM_STATE = 42
DOWNLOAD_TIMEOUT = 8
MAX_WORKERS = 16
BATCH_SIZE = 32

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def download_image(url, timeout=DOWNLOAD_TIMEOUT):
    try:
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        return Image.open(io.BytesIO(resp.content)).convert("RGB")
    except Exception:
        return None


def build_pool():
    confirmed = pd.read_csv(CONFIRMED_PATH)
    confirmed_hashes = set(confirmed["image_hash"])

    anchors = confirmed[confirmed["decision"] == "fits"].copy()
    anchors["group"] = "anchor"

    boundary = confirmed[confirmed["decision"] == "boundary_reject"].copy()
    boundary["group"] = "background_boundary"

    cols = ["image_hash", "family", "url_link", "caption", "group"]

    # NOTE: background_random must be APPEND-ONLY across reruns, not just a
    # fixed-seed resample -- a full fresh resample still silently drops
    # previously-included images every time this script's own output file
    # gets overwritten (this happened twice: once from a shrinking-frame
    # sample() call, once again from a "fixed seed but full regeneration"
    # version that looked stable but wasn't, since the whole file is
    # rewritten from scratch each run). Any already-used image that
    # vanishes from the pool breaks review/triplet_manifest.csv rows that
    # already have GPU-scored results in review/triplet_results.csv.
    # Carrying forward every previous background_random row (minus any since
    # promoted to anchor/boundary) and only sampling NEW rows to top up to
    # the target is the only version of this that is actually stable.
    existing_meta_path = os.path.join(OUT_DIR, "similarity_pool_metadata.csv")
    stable_background = pd.DataFrame(columns=cols)
    if os.path.exists(existing_meta_path):
        prev = pd.read_csv(existing_meta_path)
        stable_background = prev.loc[
            (prev["group"] == "background_random") & (~prev["image_hash"].isin(confirmed_hashes)), cols
        ].copy()
        print(f"Carrying forward {len(stable_background)} background_random rows from the existing pool file")

    dataset = load_dataset("thaoshibe/anonymous-captions-114k")
    test_df = dataset["test"].to_pandas()

    n_needed = max(0, FIXED_BACKGROUND_DRAW - len(stable_background))
    exclude_for_new_draw = confirmed_hashes | set(stable_background["image_hash"])
    remaining = test_df.loc[~test_df["image_hash"].isin(exclude_for_new_draw)]
    new_random_bg = remaining.sample(n=min(n_needed, len(remaining)), random_state=RANDOM_STATE).reset_index(drop=True)
    new_random_bg["family"] = ""
    new_random_bg["decision"] = ""
    new_random_bg["notes"] = ""
    new_random_bg["source_batch"] = "random_background"
    new_random_bg["group"] = "background_random"

    random_bg = pd.concat([stable_background, new_random_bg[cols]], ignore_index=True)

    pool = pd.concat([anchors[cols], boundary[cols], random_bg[cols]], ignore_index=True)
    pool = pool.drop_duplicates(subset="image_hash").reset_index(drop=True)

    print(
        f"Pool size: {len(pool)} "
        f"({(pool['group'] == 'anchor').sum()} anchors, "
        f"{(pool['group'] == 'background_boundary').sum()} boundary-reject background, "
        f"{(pool['group'] == 'background_random').sum()} random background)"
    )
    return pool


def main():
    pool = build_pool()

    print("Loading CLIP (openai/clip-vit-base-patch32)...")
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32", use_safetensors=True).to(DEVICE)
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    model.eval()

    print(f"Downloading {len(pool)} images with {MAX_WORKERS} workers (device={DEVICE})...")
    images = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(download_image, row.url_link): row.image_hash for row in pool.itertuples()}
        done = 0
        for fut in as_completed(futures):
            h = futures[fut]
            img = fut.result()
            if img is not None:
                images[h] = img
            done += 1
            if done % 50 == 0 or done == len(pool):
                print(f"  {done}/{len(pool)} processed, {len(images)} downloaded ok")

    print(f"Downloaded {len(images)} / {len(pool)} images successfully")

    pool["download_ok"] = pool["image_hash"].isin(images.keys())
    os.makedirs(OUT_DIR, exist_ok=True)
    pool.loc[~pool["download_ok"]].to_csv(
        os.path.join(OUT_DIR, "similarity_download_failures.csv"), index=False
    )

    hashes = list(images.keys())
    all_embeddings = []
    print("Computing CLIP embeddings...")
    for i in range(0, len(hashes), BATCH_SIZE):
        batch_hashes = hashes[i:i + BATCH_SIZE]
        batch_imgs = [images[h] for h in batch_hashes]
        inputs = processor(images=batch_imgs, return_tensors="pt").to(DEVICE)
        with torch.no_grad():
            out = model.get_image_features(**inputs)
        # NOTE: on some transformers versions, get_image_features() returns a raw
        # tensor directly; on others (5.14.1, confirmed here) it returns a
        # BaseModelOutputWithPooling wrapper whose .pooler_output holds the
        # projected 512-d embedding (verified against self-similarity == 1.0).
        # Handle both so this keeps working regardless of the installed version.
        feats = out.pooler_output if hasattr(out, "pooler_output") else out
        feats = feats / feats.norm(dim=-1, keepdim=True)
        all_embeddings.append(feats.cpu().numpy())
        print(f"  embedded {min(i + BATCH_SIZE, len(hashes))}/{len(hashes)}")

    embeddings = np.concatenate(all_embeddings, axis=0).astype(np.float32)

    np.savez(
        os.path.join(OUT_DIR, "similarity_embeddings.npz"),
        hashes=np.array(hashes),
        embeddings=embeddings,
    )
    pool.to_csv(os.path.join(OUT_DIR, "similarity_pool_metadata.csv"), index=False)

    print(f"\nWrote {OUT_DIR}/similarity_embeddings.npz {embeddings.shape}")
    print(f"Wrote {OUT_DIR}/similarity_pool_metadata.csv")
    print(f"Wrote {OUT_DIR}/similarity_download_failures.csv "
          f"({(~pool['download_ok']).sum()} failures)")


if __name__ == "__main__":
    main()
