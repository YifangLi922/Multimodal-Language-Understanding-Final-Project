"""Permanently archive every image referenced in the final triplet manifest.

review/triplet_manifest.csv only stores original web URLs -- eval_triplet.py
re-downloads from those URLs every time it runs. Link rot is a real,
observed risk in this dataset (roughly a quarter of URLs across various
batches have already gone dead), and once enough of the 235 unique images
in the final 175-triplet benchmark go missing, the exact benchmark can no
longer be reproduced or even re-inspected. This saves a permanent local
copy of every image (same 1024px-longest-side cap used during actual
scoring, so the archive matches what the models actually saw) plus an
index tying each file back to its hash, source URL, and caption.

Output:
  review/archive/images/<image_hash>.jpg
  review/archive/image_archive_index.csv
"""
import io
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import requests
from PIL import Image

MANIFEST_PATH = "review/triplet_manifest.csv"
OUT_DIR = "review/archive/images"
INDEX_PATH = "review/archive/image_archive_index.csv"
DOWNLOAD_TIMEOUT = 10
MAX_WORKERS = 16
MAX_IMAGE_DIM = 1024


def download_image(url, timeout=DOWNLOAD_TIMEOUT):
    try:
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content)).convert("RGB")
        img.thumbnail((MAX_IMAGE_DIM, MAX_IMAGE_DIM), Image.LANCZOS)
        return img
    except Exception as e:
        return None


def main():
    manifest = pd.read_csv(MANIFEST_PATH)

    needed = {}
    captions = {}
    for _, r in manifest.iterrows():
        for role in ("anchor", "positive", "negative"):
            h = r[f"{role}_hash"]
            needed[h] = r[f"{role}_url"]
            captions[h] = r[f"{role}_caption"]

    print(f"Archiving {len(needed)} unique images referenced in {MANIFEST_PATH}...")
    os.makedirs(OUT_DIR, exist_ok=True)

    rows = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(download_image, url): (h, url) for h, url in needed.items()}
        done = 0
        for fut in as_completed(futures):
            h, url = futures[fut]
            img = fut.result()
            ok = img is not None
            local_path = ""
            if ok:
                local_path = os.path.join(OUT_DIR, f"{h}.jpg")
                img.save(local_path, "JPEG", quality=90)
            rows.append({
                "image_hash": h, "local_path": local_path if ok else "",
                "url_link": url, "caption": captions[h], "download_ok": ok,
            })
            done += 1
            if done % 30 == 0 or done == len(needed):
                print(f"  {done}/{len(needed)} processed")

    index = pd.DataFrame(rows)
    index.to_csv(INDEX_PATH, index=False)

    n_ok = index["download_ok"].sum()
    print(f"\nArchived {n_ok} / {len(index)} images to {OUT_DIR}/")
    print(f"Wrote {INDEX_PATH}")
    if n_ok < len(index):
        failed = index.loc[~index["download_ok"], "image_hash"].tolist()
        print(f"Failed to archive {len(failed)} images (already dead, or dead by the time this ran): {failed}")


if __name__ == "__main__":
    main()
