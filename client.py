import requests

BASE_URL = "https://my-json-server.typicode.com/AdamGold/relevance-aware-llm/"


def fetch_entity_data(entity_type: str, entity_id: str):
    """
    Fetches data from the API for the given entity.
    - source: Source of the entity (e.g., 'slack')
    - entity_type: Type of the entity (e.g., 'message')
    - entity_id: ID of the entity (e.g., '102')
    """
