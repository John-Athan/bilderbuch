import json

from ollama import chat

from model import State, load_state

PROMPT = '''
Du bist Paul, ein erfahrener Kinderbuchredakteur in einem großen Verlag. 
Du kennst die aktuellen Interessen von Kindern im Alter von 4–8 Jahren sehr gut, weil du regelmäßig Kinderzeitschriften liest, Spielzeugkataloge durchgehst und mit Eltern, Lehrer:innen und Kindern sprichst.

Welche drei Themen sind im Moment besonders beliebt und eignen sich gut als kreative Kinderbuchideen?

Gib deine Antwort als JSON-Liste mit genau drei kindgerechten Buchtiteln zurück:

["Titel 1", "Titel 2", "Titel 3"]
'''


def suggest_book_topics(state: State) -> State:
    response = chat(model=state.model, messages=[{"role": "user", "content": PROMPT}])
    output = response.message.content
    try:
        start = output.find("[")
        end = output.rfind("]") + 1
        state.suggested_topics = json.loads(output[start:end])
        return state
    except Exception as e:
        raise ValueError(f"Konnte Themenvorschläge nicht parsen: {e}\n{output}")


if __name__ == "__main__":
    print(suggest_book_topics(load_state("asd"), "asd"))
