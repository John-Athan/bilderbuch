from ollama import chat

from model import State, Page, Storyline, load_state

TITLE_PROMPT_TEMPLATE = '''
Du bist ein kreativer Kinderbuchautor. 
Welchen passenden Titel würdest du einem illustrierten Kinderbuch zum Thema "{theme}" geben? 
Der Titel soll neugierig machen, kindgerecht sein und zur Altersgruppe 4–8 passen. Gib nur den Titel zurück.
'''

STRUCTURE_PROMPT_TEMPLATE = '''
Du bist ein Kinderbuchautor und schreibst ein kurzes illustriertes Buch für Kinder im Alter von 4–8 Jahren. 
Das Thema lautet: "{theme}"
Erstelle eine kurze Gliederung für eine Geschichte zu diesem Thema.
Folge dabei dieser Struktur:
1 Seite Einführung, 
1 Seiten Problem/Konflikt, 
2 Seiten steigende Handlung, 
1 Seite Höhepunkt, 
1 Seite Auflösung, 
1 Seite Schluss.

Die Geschichte soll kindgerecht, einfach und gut illustrierbar sein. 
Jeder Schritt soll aus 1–2 kurzen Sätzen bestehen. 
Gib die Gliederung als nummerierte Liste zurück (z.B. 1. ..., 2. ..., usw.). Schreibe noch nicht den vollständigen Text der Geschichte.
'''

TEXT_FROM_STRUCTURE_PROMPT_TEMPLATE = '''
Du schreibst ein Kinderbuch mit dem Titel "{title}" zum Thema "{theme}".
Die geplante Gliederung der Geschichte lautet:

```

{outline}

```

Schreibe den endgültigen Text für Seite {index}, basierend auf dem entsprechenden Punkt in der Gliederung.
Schreibe 1–3 kurze Sätze, die für Kinder im Alter von 4–8 Jahren geeignet sind. 
Verwende eine einfache, verständliche Sprache.
Gib ausschließlich den eigentlichen Text für die Kinderbuchseite zurück – ohne Überschrift, Seitennummer, Kommentare oder Erklärungen. 
Nur den Text, der im Buch abgedruckt wird.
'''

IMAGE_PROMPT_TEMPLATE = '''
You are a children's book illustrator. You are working on the book "{title}" (Theme: {theme}).
The text generated so far is:

```

{content}

```

Briefly describe what should be shown in the illustration for page {index}, in the form of a prompt for text-to-image generation.
Maintain consistency with the previously described content, characters, and illustrations.
The text on the page is: {text}
Take into account what is typically appropriate for children's books (e.g., bright colors, clear scenes). 
Return only the english image description. 
Mind that you only have 77 tokens for your entire response so write super short efficient prompts!
'''

CHARACTER_DESCRIPTION_PROMPT_TEMPLATE = '''
You are a children's book author and illustrator.
You are working on a short picture book for ages 4–8, with the theme "{theme}".
Define 1–3 recurring characters for the story.

For each character, briefly describe:
- Name
- Role in the story
- Appearance (age, clothes, colors, special traits)
- Personality

Make the descriptions consistent and suitable for illustrations.
Return as a list.
Mind that this will be included in all image descriptions, so keep it very short and efficient.
'''


def clean_page_text(text: str) -> str:
    lines = text.strip().split('\n')

    lines = [line for line in lines if not line.strip().lower().startswith("**seite")]
    for sep in ["---", "***", "###", "■■■"]:
        lines = [line.split(sep)[0].strip() for line in lines]
    lines = [line for line in lines if not any(keyword in line.lower() for keyword in
                                               ["diese seite", "ziel", "soll", "darauf", "ist darauf ausgelegt",
                                                "hilft", "verständlichkeit"])]

    cleaned = '\n'.join(lines).strip()
    return cleaned


def generate_character_descriptions(theme: str, model: str) -> list[str]:
    prompt = CHARACTER_DESCRIPTION_PROMPT_TEMPLATE.format(theme=theme)
    result = call(model, prompt)
    return [line.strip() for line in result.strip().split('\n') if line.strip()]


def call(model: str, prompt: str, token_callback=None) -> str:
    stream = chat(model=model, messages=[{"role": "user", "content": prompt}], stream=True)
    response = ""

    for chunk in stream:
        content = chunk['message']['content']
        response += content
        if token_callback:
            token_callback(content)

    if "<think>" in response:
        response = response[response.index("</think>") + 10:]
    return response


def generate_title(theme: str, model: str) -> str:
    prompt = TITLE_PROMPT_TEMPLATE.format(theme=theme)
    title = call(model, prompt)
    return title.strip('"* \n')


def generate_story_outline(theme: str, model: str) -> list[str]:
    prompt = STRUCTURE_PROMPT_TEMPLATE.format(theme=theme)
    outline = call(model, prompt)
    steps = [line.strip().split('. ', 1)[1] for line in outline.strip().split('\n') if '. ' in line]
    return steps


def generate_page_text_from_outline(theme: str, title: str, outline: list[str], index: int, model: str) -> str:
    outline_str = "\n".join(f"{i + 1}. {step}" for i, step in enumerate(outline))
    prompt = TEXT_FROM_STRUCTURE_PROMPT_TEMPLATE.format(theme=theme, title=title, outline=outline_str, index=index)
    raw_text = call(model, prompt)
    return clean_page_text(raw_text)


def generate_image_description(theme: str, title: str, content: str, index: int, text: str, model: str,
                               characters: list[str]) -> str:
    characters_str = "\n".join(characters)
    prompt = IMAGE_PROMPT_TEMPLATE.format(theme=theme, title=title, content=content, index=index, text=text)
    prompt = f"The main characters in this book are:\n{characters_str}\n\n{prompt}"
    return call(model, prompt)


def generate_storyline(state: State) -> State:
    if "storyline" in state:
        return state

    title = generate_title(state.selected_topic, state.model)
    outline = generate_story_outline(state.selected_topic, state.model)
    character_descriptions = generate_character_descriptions(state.selected_topic, state.model)

    pages = []
    for i in range(1, 8):
        page_text = generate_page_text_from_outline(state.selected_topic, title, outline, i, state.model)
        prior_texts = "\n".join([f"{j + 1}. {p.text}" for j, p in enumerate(pages)])
        image_description = generate_image_description(state.selected_topic, title, prior_texts, i, page_text,
                                                       state.model, character_descriptions)
        pages.append(Page(text=page_text, image_description=image_description))

    state.storyline = Storyline(title=title, pages=pages)
    return state


if __name__ == "__main__":
    print(generate_storyline(load_state("asd")))
