from enum import Enum
from pydantic import BaseModel, Field


class EntityTypes(Enum):
    TICKET = "ticket"
    MESSAGE = "message"
    MEETING = "meeting"


class Ticket(BaseModel):
    id: str | int
    title: str
    status: str


class Message(BaseModel):
    id: str | int
    content: str


class Meeting(BaseModel):
    id: str | int
    title: str
    transcription: str


class ContextForLLM(BaseModel):
    tickets: list[Ticket] = Field(default_factory=list)
    messages: list[Message] = Field(default_factory=list)
    meeting_transcriptions: list[Meeting] = Field(default_factory=list)


class EntityParser:
    @staticmethod
    def parse_id(entity_id: str) -> dict[str, str]:
        """
        Parses the entity ID string and extracts the source, type, and ID.
        Example: 'slack|message|102' -> {'source': 'slack', 'type': 'message', 'id': '102'}
        """
        parts = entity_id.split("|")
        [source, type_, id_] = parts
        return {"source": source, "type": type_, "id": id_}
