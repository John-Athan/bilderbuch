import json
from typing import List, Optional

from pydantic import ConfigDict, BaseModel


class Page(BaseModel):
    model_config = ConfigDict(frozen=False)
    text: str
    image_description: str
    image_filepath: Optional[str] = None


class Storyline(BaseModel):
    model_config = ConfigDict(frozen=False)
    title: str
    title_image_filepath: Optional[str] = None
    pages: List[Page]


class State(BaseModel):
    model_config = ConfigDict(frozen=False)
    model: str
    image_model: str
    suggested_topics: Optional[List[str]] = None
    selected_topic: Optional[str] = None
    storyline: Optional[Storyline] = None


def save_state(state: State, run_id: str):
    with open(f"{run_id}/state.json", "w", encoding="utf-8") as f:
        f.write(state.model_dump_json(indent=2))


def load_state(run_id: str) -> State:
    with open(f"{run_id}/state.json", "r", encoding="utf-8") as f:
        state_raw = json.load(f)
        state = State(**state_raw)
        return state
