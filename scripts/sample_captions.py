from datasets import load_dataset

dataset = load_dataset("thaoshibe/anonymous-captions-114k")
print(dataset)

split_name = list(dataset.keys())[0]
df = dataset[split_name].to_pandas()
print("Columns:", df.columns.tolist())
print(df.head())

sample_df = df.sample(n=min(400, len(df)), random_state=42).reset_index(drop=True)
sample_df["relation_type"] = ""
sample_df.to_csv("caption_sample_400.csv", index=False)
print(f"Saved {len(sample_df)} sampled rows to caption_sample_400.csv")
