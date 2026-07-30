from datasets import load_dataset

dataset = load_dataset("thaoshibe/anonymous-captions-114k")
print(dataset)

# NOTE: must sample from the official "test" split, not the first split in
# dataset.keys() (that was "train" and produced a 400-row sample that had
# zero overlap with the test split -- caught via a manual split-overlap check).
split_name = "test"
df = dataset[split_name].to_pandas()
print("Columns:", df.columns.tolist())
print(df.head())

sample_df = df.sample(n=min(400, len(df)), random_state=42).reset_index(drop=True)
sample_df["relation_type"] = ""
import os
os.makedirs("data", exist_ok=True)
sample_df.to_csv("data/caption_sample_400.csv", index=False)
print(f"Saved {len(sample_df)} sampled rows from '{split_name}' split to data/caption_sample_400.csv")
