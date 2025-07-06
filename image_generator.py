import os

import streamlit as st
import torch
from diffusers import StableDiffusionXLPipeline, StableDiffusion3Pipeline

from model import load_state, State, save_state

PROMPT_TEMPLATE = """
Style: hand-drawn, warm, and poetic—blending detailed, nature-rich backgrounds with simple, expressive characters. 
It captures everyday beauty, quiet magic, and emotional depth through soft colors, whimsical worlds, and gentle pacing.

Content: {content}
"""

NEGATIVE_PROMPT = "blurry, distorted, creepy, low quality, deformed, disfigured"

MODE_SETTINGS = {"sdxl": {"model": "stabilityai/sdxl-turbo", "steps": 1, "guidance": 0.0, "use_vae_tiling": False, },
                 "sd35": {"model": "stabilityai/stable-diffusion-3.5-medium", "steps": 20, "guidance": 7.5,
                          "use_vae_tiling": True, }}


def get_pipeline(model_name: str):
    if "pipeline_cache" not in st.session_state:
        st.session_state.pipeline_cache = {}

    if model_name in st.session_state.pipeline_cache:
        return st.session_state.pipeline_cache[model_name]

    settings = MODE_SETTINGS[model_name]
    model_id = settings["model"]

    if "sdxl" in model_name:
        pipe = StableDiffusionXLPipeline.from_pretrained(model_id, torch_dtype=torch.float16, variant="fp16")
        pipe.to("mps")
        if settings["use_vae_tiling"]:
            pipe.vae.enable_tiling()
    elif "sd35" in model_name:
        pipe = StableDiffusion3Pipeline.from_pretrained(model_id, torch_dtype=torch.float16)
        pipe.to("mps")
        if settings["use_vae_tiling"]:
            pipe.vae.enable_tiling()
    else:
        raise ValueError(f"Unknown model '{model_name}'.")

    st.session_state.pipeline_cache[model_name] = pipe
    return pipe


def image_from_description(prompt: str, model: str, image_path: str) -> None:
    if model.lower() not in MODE_SETTINGS:
        raise ValueError(f"Unknown mode '{model}'. Choose from: {', '.join(MODE_SETTINGS.keys())}")

    pipe = get_pipeline(model.lower())
    settings = MODE_SETTINGS[model.lower()]

    image = pipe(prompt=PROMPT_TEMPLATE.format(content=prompt), negative_prompt=NEGATIVE_PROMPT,
                 num_inference_steps=settings["steps"], guidance_scale=settings["guidance"]).images[0]

    image.save(image_path)


def generate_images_for_storyline(state: State, run_id: str) -> State:
    filepath = os.path.join(run_id, f"title.png")
    title = f"Make a cover for a children's book with this title: {state.storyline.title}"
    image_from_description(title, state.image_model, filepath)
    state.storyline.title_image_filepath = filepath

    for i, page in enumerate(state.storyline.pages, start=0):
        filepath = os.path.join(run_id, f"page_{i:02d}.png")
        print(f"Generiere Bild {i + 1}")
        image_from_description(page.image_description, state.image_model, filepath)
        state.storyline.pages[i].image_filepath = filepath

    return state


if __name__ == "__main__":
    run_id = "59c4a22d-d892-4fdc-9f20-8fdd05a323ae"
    state = generate_images_for_storyline(load_state(run_id), run_id)
    save_state(state, run_id)
    print(state)
