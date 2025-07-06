import base64
import os
import time
import uuid
from os import mkdir

import streamlit as st
from PIL import Image

from image_generator import image_from_description
from model import save_state, State, load_state, Storyline, Page
from pdf_generator import generate_pdf
from storyline_creator import generate_image_description, TEXT_FROM_STRUCTURE_PROMPT_TEMPLATE, \
    generate_character_descriptions, generate_title, STRUCTURE_PROMPT_TEMPLATE, call
from topic_creator import suggest_book_topics

MODELS = ["gemma3n:e4b", "llama3.1:8b", "gemma3:12b", "phi4", "qwen3:14b"]
IMAGE_MODELS = ["sdxl", "sd35"]

st.set_page_config(page_title="Kinderbuch-Generator")
st.title("📖 Kinderbuch Generator")


def choose_model():
    st.header("0. Modell")
    st.selectbox("Welches Modell möchtest du verwenden?", MODELS, key="model")
    st.selectbox("Welches Text-To-Image-Modell möchtest du verwenden?", IMAGE_MODELS, key="image_model")
    if st.button("Modell bestätigen"):
        st.session_state.step = 1
        st.session_state.run_id = str(uuid.uuid4())
        print(f"Run ID: {st.session_state.run_id}")
        mkdir(st.session_state.run_id)
        state = State(model=st.session_state.model, image_model=st.session_state.image_model)
        save_state(state, st.session_state.run_id)
        st.rerun()


def choose_topic():
    state = load_state(st.session_state.run_id)
    st.header("1. Thema")
    if "topics_generated" not in st.session_state:
        with st.spinner("Schlage Themen vor..."):
            state = suggest_book_topics(state)
            st.session_state.topics_generated = True
            save_state(state, st.session_state.run_id)
    selected_topic = st.radio("Welches Thema gefällt dir am besten?", state.suggested_topics)
    custom_topic = st.text_input("Oder gib ein eigenes Thema ein:")

    if st.button("Thema bestätigen"):
        state.selected_topic = custom_topic.strip() if custom_topic else selected_topic
        st.session_state.step = 2
        save_state(state, st.session_state.run_id)
        st.rerun()


def stream_text_live(prompt: str, model: str):
    placeholder = st.empty()
    full_text = ""

    def update_ui(token):
        nonlocal full_text
        full_text += token
        placeholder.markdown(full_text + "▌")  # blinking cursor feel
        time.sleep(0.03)  # typing delay

    final_response = call(model, prompt, token_callback=update_ui)
    placeholder.markdown(final_response)  # remove cursor
    return final_response


def choose_storyline():
    state = load_state(st.session_state.run_id)
    st.header(f"2. {state.selected_topic or 'Storyline'}")

    if "storyline_generated" not in st.session_state:
        with st.spinner("Generiere Storyline..."):
            # Show prompt being answered
            st.subheader("Generierte Gliederung")
            prompt = STRUCTURE_PROMPT_TEMPLATE.format(theme=state.selected_topic)
            outline_text = stream_text_live(prompt, state.model)

            # Parse and continue
            title = generate_title(state.selected_topic, state.model)
            character_descriptions = generate_character_descriptions(state.selected_topic, state.model)

            pages = []
            for i in range(1, 8):
                st.subheader(f"Seite {i}")
                page_prompt = TEXT_FROM_STRUCTURE_PROMPT_TEMPLATE.format(theme=state.selected_topic, title=title,
                                                                         outline=outline_text, index=i)
                page_text = stream_text_live(page_prompt, state.model)
                prior_texts = "\n".join([f"{j + 1}. {p.text}" for j, p in enumerate(pages)])
                image_description = generate_image_description(state.selected_topic, title, prior_texts, i, page_text,
                                                               state.model, character_descriptions)
                pages.append(Page(text=page_text, image_description=image_description))

            state.storyline = Storyline(title=title, pages=pages)
            save_state(state, st.session_state.run_id)
            st.session_state.storyline_generated = True
            st.rerun()

    st.subheader("Titel")
    st.text_input("Titel", value=state.storyline.title)

    st.subheader("Seiten")
    for i, page in enumerate(state.storyline.pages, start=1):
        st.markdown(f"### Seite {i}")
        page.text = st.text_area(f"Text Seite {i}", value=page.text, key=f"text_{i}")
        page.image_description = st.text_area(f"Bildbeschreibung Seite {i}", value=page.image_description,
                                              key=f"image_{i}")

    if st.button("Storyline bestätigen"):
        save_state(state, st.session_state.run_id)
        st.session_state.step = 3
        st.rerun()


def choose_pictures():
    st.header(f"3. {st.session_state.get('selected_topic', 'Storyline')}")

    state = load_state(st.session_state.run_id)
    total_pages = len(state.storyline.pages)

    if "current_page_index" not in st.session_state:
        st.session_state.current_page_index = 0

    i = st.session_state.current_page_index

    if i < total_pages:
        with st.spinner(f"Generiere Bild {i + 1} von {total_pages}..."):
            filepath = os.path.join(st.session_state.run_id, f"page_{i:02d}.png")
            image_from_description(state.storyline.pages[i].image_description, state.image_model, filepath)
            state.storyline.pages[i].image_filepath = filepath
            save_state(state, st.session_state.run_id)
            st.session_state.current_page_index += 1
            st.rerun()
    else:
        # Show all generated images
        for j, page in enumerate(state.storyline.pages):
            st.subheader(f"Seite {j}")
            st.markdown(f"**Text:** {page.text}")
            image = Image.open(page.image_filepath)
            st.image(image, caption=f"Seite {j}", use_container_width=True)

            if st.button(f"❌ Bild für Seite {j} neu generieren", key=f"regen_{j}"):
                os.remove(page.image_filepath)
                del state.storyline.pages[j].image_filepath
                st.session_state.current_page_index = j  # Start generation from this index
                save_state(state, st.session_state.run_id)
                st.rerun()

        if st.button("Alle Bilder bestätigen und weiter"):
            st.session_state.step = 4
            st.rerun()


def show_bilderbuch():
    st.header("4. Buch")
    state = load_state(st.session_state.run_id)

    output_pdf_path = os.path.join(st.session_state.run_id, "kinderbuch.pdf")
    pdf_path = generate_pdf(state, output_path=output_pdf_path)

    st.success("📘 Das Buch wurde erfolgreich erstellt!")

    with open(pdf_path, "rb") as f:
        st.download_button(label="📥 Buch herunterladen", data=f, file_name="kinderbuch.pdf", mime="application/pdf")



if __name__ == "__main__":
    if "step" not in st.session_state:
        st.session_state.step = 0

    if st.session_state.step == 0:
        choose_model()
    elif st.session_state.step == 1:
        choose_topic()
    elif st.session_state.step == 2:
        choose_storyline()
    elif st.session_state.step == 3:
        choose_pictures()
    elif st.session_state.step == 4:
        show_bilderbuch()
