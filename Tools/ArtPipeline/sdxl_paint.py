#!/usr/bin/env python3
"""Local repaint of a Blender layout render into a hand-painted battlefield (fallback when Codex image_gen is out).

  C:/Users/Winka/Tools/sdxl/venv/Scripts/python.exe Tools/ArtPipeline/sdxl_paint.py \
      --layout ArtCache/EnvHaven/layout/flat_raw.png --out ArtCache/EnvHaven/sdxl --seeds 3

SDXL base 1.0 (CreativeML OpenRAIL++-M) + ControlNet canny SDXL (diffusers, OpenRAIL++), img2img: the layout's
edges lock walls, gates and roads; the denoise strength repaints surfaces. Writes <out>/paint_<seed>.png at the
layout's 16:9 aspect (1344 x 768 working size, resized to 1672 x 941) for paint_finish.py.
"""
import argparse
import os

import cv2
import numpy as np
import torch
from diffusers import ControlNetModel, StableDiffusionXLControlNetImg2ImgPipeline
from PIL import Image

PROMPT = ("hand-painted top-down fantasy strategy game battlefield, a stone castle keep with grey battlement walls, "
          "gate towers and an open south gatehouse, warm flagstone courtyard with a glowing rune circle, iron braziers "
          "with fire, lush green grass fields outside, dirt roads, scattered ruins and rocks, bold black ink outlines, "
          "cel shading, flat colors, rich saturated palette, dark fantasy mood, crisp clean game art, highly detailed")
NEGATIVE = ("photo, photorealistic, blurry, noisy, grain, text, letters, watermark, people, characters, soldiers, "
            "monsters, ui, frame, border, lowres, jpeg artifacts, 3d render, plastic")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--layout", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--seeds", type=int, default=3)
    p.add_argument("--strength", type=float, default=0.6)
    p.add_argument("--control", type=float, default=0.65)
    p.add_argument("--steps", type=int, default=34)
    a = p.parse_args()
    os.makedirs(a.out, exist_ok=True)
    W, H = 1344, 768
    base = Image.open(a.layout).convert("RGB").resize((W, H), Image.LANCZOS)
    edges = cv2.Canny(cv2.cvtColor(np.asarray(base), cv2.COLOR_RGB2GRAY), 80, 180)
    control = Image.fromarray(np.stack([edges] * 3, -1))
    control.save(os.path.join(a.out, "control.png"))
    cn = ControlNetModel.from_pretrained("diffusers/controlnet-canny-sdxl-1.0", torch_dtype=torch.float16, variant="fp16")
    pipe = StableDiffusionXLControlNetImg2ImgPipeline.from_pretrained(
        "stabilityai/stable-diffusion-xl-base-1.0", controlnet=cn, torch_dtype=torch.float16, variant="fp16").to("cuda")
    if hasattr(pipe, "vae") and hasattr(pipe.vae, "enable_slicing"): pipe.vae.enable_slicing()
    for s in range(a.seeds):
        g = torch.Generator("cuda").manual_seed(1000 + s)
        img = pipe(PROMPT, negative_prompt=NEGATIVE, image=base, control_image=control, strength=a.strength,
                   controlnet_conditioning_scale=a.control, num_inference_steps=a.steps, guidance_scale=6.5, generator=g).images[0]
        img = img.resize((1672, 941), Image.LANCZOS)
        dst = os.path.join(a.out, "paint_%d.png" % s)
        img.save(dst)
        print("wrote", dst)


if __name__ == "__main__":
    main()
