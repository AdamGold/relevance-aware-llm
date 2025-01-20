import requests

BASE_URL = "https://my-json-server.typicode.com/AdamGold/relevance-aware-llm/"


def fetch_entity_data(entity_type: str, entity_id: str):
    """
    Fetches data from the API for the given entity.
    - source: Source of the entity (e.g., 'slack')
    - entity_type: Type of the entity (e.g., 'message')
    - entity_id: ID of the entity (e.g., '102')
    """
    entity_factory = {"issue": "issues", "message": "messages", "meeting": "meetings"}
    # Construct the endpoint URL
    url = f"{BASE_URL}{entity_factory[entity_type]}/{entity_id}"
    print(f"Fetching {url}")
    response = requests.get(url)
    return response.json() if response.status_code == 200 else None
