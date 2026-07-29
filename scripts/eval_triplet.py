from PIL import Image
import torch

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

anchor_img = Image.open("tests/images/test_1.jpg")
positive_img = Image.open("tests/images/test_2.jpg")
negative_img = Image.open("tests/images/test_3.jpg")

def clip_sim(img_a, img_b):
    inputs = clip_processor(images=[img_a, img_b], return_tensors="pt").to("cuda")
    with torch.no_grad():
        out = clip_model.get_image_features(**inputs)
    # NOTE: on some transformers versions, get_image_features() returns a raw
    # tensor directly; on others (5.14.1, confirmed here) it returns a
    # BaseModelOutputWithPooling wrapper whose .pooler_output holds the
    # projected 512-d embedding (verified against self-similarity == 1.0).
    # Handle both so this keeps working regardless of the installed version.
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

print("\n--- Triplet evaluation ---")
for name, sim_fn in [("relsim", relsim_sim), ("CLIP", clip_sim), ("DINO", dino_sim)]:
    sim_pos = sim_fn(anchor_img, positive_img)
    sim_neg = sim_fn(anchor_img, negative_img)
    correct = int(sim_pos > sim_neg)
    print(f"{name}: sim(anchor,pos)={sim_pos:.3f}  sim(anchor,neg)={sim_neg:.3f}  correct={correct}")
