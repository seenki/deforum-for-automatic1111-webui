import os
import torch
from PIL import Image
from torchvision import transforms
from clipseg.models.clipseg import CLIPDensePredT

preclipseg_transform = transforms.Compose([
      transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
      transforms.Resize((512, 512)), #TODO: check if the size is hardcoded
])

def find_clipseg(root):
    for basedir in root.basedirs():
        pth = os.path.join(basedir, './clipseg/weights/rd64-uni.pth')
        if os.path.exists(pth):
            return pth
    raise Exception('CLIPseg weights not found!')

def setup_clipseg(root):
    model = CLIPDensePredT(version='ViT-B/16', reduce_dim=64)
    model.eval()
    model.load_state_dict(torch.load(find_clipseg(root), map_location=root.device), strict=False)

    if root.half_precision:
        model = model.half()
    model.to(root.device)
    root.clipseg_model = model

def get_word_mask(root, frame, word_mask):
    if root.clipseg_model is None:
        setup_clipseg(root)
    img = preclipseg_transform(frame).unsqueeze(0).to(root.device)
    word_masks = [word_mask]
    with torch.no_grad():
        preds = model(img.repeat(len(word_masks),1,1,1), word_masks)[0]
    return Image.fromarray(torch.sigmoid(preds[0][0]).multiply(255).to(dtype=int,device=cpu).numpy())