import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()  # Load environment variables from .env


# Neo4j connection details
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = os.getenv("DB_USERNAME")
NEO4J_PASSWORD = os.getenv("DB_PASSWORD")


driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def query_graph(query):
    with driver.session() as session:
        results = session.run(query)
        return [record for record in results]


def get_project_related_items(project_id: str):
    """Get all nodes related to the project ID"""
    graph_query = f"""
    MATCH (p:Project {{id: "{project_id}"}})<-[:child_of]-(t:Ticket)
    OPTIONAL MATCH path_out=(t)-[:link_to*0..]->(related_out)
    OPTIONAL MATCH path_in=(related_in)-[:link_to*0..]->(t)
    RETURN 
        p as project, 
        collect(DISTINCT t) AS tickets,
        collect(DISTINCT nodes(path_out)) AS related_nodes_out,
        collect(DISTINCT nodes(path_in)) AS related_nodes_in,
        collect(DISTINCT relationships(path_out)) AS related_relationships_out,
        collect(DISTINCT relationships(path_in)) AS related_relationships_in
    """

    return query_graph(graph_query)
