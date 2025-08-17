# Bilderbuch

**Bilderbuch** is a hobby project that uses an interactive Streamlit app to generate illustrated books with a focus on local LLMs. 
The app guides users through topic selection, story outlining, page writing, illustration generation, and PDF export.

## Features

- Suggests popular children's book topics using LLMs.
- Generates story outlines and page texts with customizable models.
- Creates hand-drawn style illustrations for each page using Stable Diffusion models.
- Assembles the book into a downloadable PDF.
- All steps are interactive and editable.

## Technologies

- Python 3.11+
- Streamlit (UI)
- Ollama (LLM chat API)
- Diffusers, Torch (image generation)
- ReportLab (PDF generation)
- Pydantic (data models)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/John-Athan/bilderbuch.git
   cd bilderbuch
   ```

2. Install dependencies (recommended: use a virtual environment):
   ```
   pip install -r requirements.txt
   ```
   Or use the dependencies listed in `pyproject.toml`.

3. Make sure you have [Ollama](https://ollama.com/) running locally for LLM support.

## Usage

Run the Streamlit app:
```
streamlit run app.py
```

Follow the on-screen steps to create your own illustrated children's book. Download the final PDF when finished.

## Project Structure

- `app.py`: Main Streamlit application.
- `model.py`: Data models and state management.
- `storyline_creator.py`: Story and prompt generation.
- `image_generator.py`: AI image generation.
- `pdf_generator.py`: PDF creation.
- `topic_creator.py`: Topic suggestion via LLM.
