from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env


NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = os.getenv("DB_USERNAME")
NEO4J_PASSWORD = os.getenv("DB_PASSWORD")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def setup_graph():
    """Sets up the graph with additional nodes and relationships."""
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")

        queries = [
            # Create Slack Channels
            "CREATE (:Channel {id: 'slack|channel|1'})",
            # Create Slack Messages
            "CREATE (:Message {id: 'slack|message|101'})",
            "CREATE (:Message {id: 'slack|message|102'})",
            "CREATE (:Message {id: 'slack|message|103'})",
            "CREATE (:Message {id: 'slack|message|104'})",
            "CREATE (:Message {id: 'slack|message|105'})",
            "CREATE (:Message {id: 'slack|message|201'})",
            "CREATE (:Message {id: 'slack|message|202'})",
            "CREATE (:Message {id: 'slack|message|203'})",
            "CREATE (:Message {id: 'slack|message|204'})",
            "CREATE (:Message {id: 'slack|message|205'})",
            # Create Ticket Projects
            "CREATE (:Project {id: 'ticket|project|1'})",
            "CREATE (:Project {id: 'ticket|project|2'})",
            # Create Tickets
            "CREATE (:Ticket {id: 'ticket|issue|301'})",
            "CREATE (:Ticket {id: 'ticket|issue|303'})",
            "CREATE (:Ticket {id: 'ticket|issue|304'})",
            "CREATE (:Ticket {id: 'ticket|issue|305'})",
            "CREATE (:Ticket {id: 'ticket|issue|306'})",
            "CREATE (:Ticket {id: 'ticket|issue|307'})",
            "CREATE (:Ticket {id: 'ticket|issue|308'})",
            "CREATE (:Ticket {id: 'ticket|issue|309'})",
            "CREATE (:Ticket {id: 'ticket|issue|310'})",
            # Create Meetings
            "CREATE (:Meeting {id: 'google|meeting|401'})",
            "CREATE (:Meeting {id: 'google|meeting|402'})",
            "CREATE (:Meeting {id: 'google|meeting|403'})",
            # Create Relationships (Channels to Messages)
            "MATCH (c:Channel {id: 'slack|channel|1'}), (m:Message) WHERE m.id IN ['slack|message|101', 'slack|message|102', 'slack|message|103', 'slack|message|104', 'slack|message|105', 'slack|message|201', 'slack|message|202', 'slack|message|203', 'slack|message|204', 'slack|message|205'] CREATE (m)-[:child_of]->(c)",
            # Create Relationships (Projects to Tickets)
            "MATCH (p:Project {id: 'ticket|project|1'}), (t:Ticket) WHERE t.id IN ['ticket|issue|301', 'ticket|issue|303', 'ticket|issue|304', 'ticket|issue|305'] CREATE (t)-[:child_of]->(p)",
            "MATCH (p:Project {id: 'ticket|project|2'}), (t:Ticket) WHERE t.id IN ['ticket|issue|306', 'ticket|issue|307', 'ticket|issue|308', 'ticket|issue|309', 'ticket|issue|310'] CREATE (t)-[:child_of]->(p)",
            # Create Relationships (Messages to Tickets based on mentions or discussions)
            "MATCH (m:Message {id: 'slack|message|101'}), (t:Ticket {id: 'ticket|issue|301'}) CREATE (m)-[:link_to]->(t)",
            "MATCH (m:Message {id: 'slack|message|102'}), (t:Ticket {id: 'ticket|issue|301'}) CREATE (m)-[:link_to]->(t)",
            "MATCH (m:Message {id: 'slack|message|103'}), (t:Ticket {id: 'ticket|issue|301'}) CREATE (m)-[:link_to]->(t)",
            "MATCH (m:Message {id: 'slack|message|104'}), (t:Ticket {id: 'ticket|issue|303'}) CREATE (m)-[:link_to]->(t)",
            "MATCH (m:Message {id: 'slack|message|105'}), (t:Ticket {id: 'ticket|issue|304'}) CREATE (m)-[:link_to]->(t)",
            "MATCH (m:Message {id: 'slack|message|203'}), (t:Ticket {id: 'ticket|issue|308'}) CREATE (m)-[:link_to]->(t)",
            "MATCH (m:Message {id: 'slack|message|204'}), (t:Ticket {id: 'ticket|issue|309'}) CREATE (m)-[:link_to]->(t)",
            "MATCH (m:Message {id: 'slack|message|205'}), (t:Ticket {id: 'ticket|issue|310'}) CREATE (m)-[:link_to]->(t)",
            # Create Relationships (Meetings to Tickets based on discussions)
            "MATCH (mt:Meeting {id: 'google|meeting|401'}), (t:Ticket {id: 'ticket|issue|303'}) CREATE (mt)-[:link_to]->(t)",
            "MATCH (mt:Meeting {id: 'google|meeting|402'}), (t:Ticket {id: 'ticket|issue|308'}) CREATE (mt)-[:link_to]->(t)",
            "MATCH (mt:Meeting {id: 'google|meeting|403'}), (t:Ticket {id: 'ticket|issue|301'}) CREATE (mt)-[:link_to]->(t)",
        ]

        for query in queries:
            session.run(query)

    print("Graph setup complete!")


if __name__ == "__main__":
    setup_graph()
