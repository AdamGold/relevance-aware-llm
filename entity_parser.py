from enum import Enum


class EntityTypes(Enum):
    TICKET = "ticket"
    MESSAGE = "message"
    MEETING = "meeting"


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
