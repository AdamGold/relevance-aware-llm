import streamlit as st
from neo4j import GraphDatabase, Record
from openai import OpenAI

from client import fetch_entity_data
from entity_parser import (
    ContextForLLM,
    EntityParser,
    EntityTypes,
    Meeting,
    Message,
    Ticket,
)
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env


# Neo4j connection details
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = os.getenv("DB_USERNAME")
NEO4J_PASSWORD = os.getenv("DB_PASSWORD")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(
    api_key=openai_api_key,
)


def query_graph(query):
    """Query Neo4j to fetch IDs."""
    with driver.session() as session:
        results = session.run(query)
        return [record for record in results]


def create_llm_context_from_results(results: list[Record]) -> ContextForLLM:
    context = ContextForLLM()

    # PLACEHOLDER

    return context


def format_entities_for_llm(context: ContextForLLM) -> str:
    return "PLACEHOLDER"


def generate_answer(context: str, question: str) -> str | None:
    """Generate LLM response using context and question."""
    prompt = f"""
    Context:
    {context}

    Question:
    {question}

    Answer:
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are an assistant tasked with perliminary summarization of content from productivity tools used by an software development team.\n"
                "Your results are CRITICAL for the final summary creation, so make sure to provide the most accurate and relevant information.\n"
                "You will be provided with a document representation of such content:\n"
                "- The document will contain the main item with its comments/additional information items\n"
                "- Each item  will include its item type, main text, secondary text, author, created at, updated at, and status (if available) of the item.\n"
                "- The item type is a combination of the product and the type of the item.\n\n"
                "Ensure that the extraction:\n"
                "- Has full coverage, capturing all significant information.\n"
                "- Is factually correct based solely on the provided document.\n"
                "- Uses clear and concise language.\n",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )
    return response.choices[0].message.content


# Streamlit UI
st.title("Graph RAG App")

st.sidebar.header("Input Section")
# Let the user pick a ticket project
project_id = st.sidebar.selectbox(
    "Select a Project:",
    ["ticket|project|1", "ticket|project|2"],
)


user_query = st.sidebar.text_area("Ask a question:", placeholder="Who created post 1?")
if st.sidebar.button("Submit"):
    with st.spinner("Querying the graph and fetching data..."):
        # Query Neo4j for the subgraph based on the selected ticket project
        graph_query = "PLACEHOLDER"
        results = query_graph(graph_query)

        # Fetch data from JSONPlaceholder
        context = create_llm_context_from_results(results=results)
        formatted_context = format_entities_for_llm(context=context)

        # Generate answer
        answer = (
            generate_answer(formatted_context, user_query)
            if formatted_context
            else "No relevant data found."
        )

    # Display results

    st.subheader(user_query)

    st.title("Generated Answer")
    st.write(answer)

    with st.expander(label="Graph Context"):
        st.write(formatted_context)
