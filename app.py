import streamlit as st
from neo4j import Record
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

from graph_client import get_project_related_items

load_dotenv()  # Load environment variables from .env


# Neo4j connection details
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = os.getenv("DB_USERNAME")
NEO4J_PASSWORD = os.getenv("DB_PASSWORD")


openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(
    api_key=openai_api_key,
)


def create_llm_context_from_results(results: list[Record]) -> ContextForLLM:
    context = ContextForLLM()

    for record in results:
        for ticket in record["tickets"]:
            external_id = EntityParser.parse_id(ticket["id"])
            data = fetch_entity_data(
                entity_type=external_id["type"], entity_id=external_id["id"]
            )
            if not data:
                continue
            context.tickets.append(Ticket(**data))

        for related_node in record["related_nodes_in"]:
            for entity in related_node:
                external_id = EntityParser.parse_id(entity["id"])
                data = fetch_entity_data(
                    entity_type=external_id["type"], entity_id=external_id["id"]
                )
                if not data:
                    continue
                print(f"Got {data} for {external_id['type']}")
                if external_id["type"] == EntityTypes.MESSAGE.value:
                    context.messages.append(Message(**data))
                elif external_id["type"] == EntityTypes.MEETING.value:
                    context.meeting_transcriptions.append(Meeting(**data))

    return context


def format_entities_for_llm(context: ContextForLLM) -> str:
    return f"""
        ### Tickets
        {"".join(f"- **ID {ticket.id}**: {ticket.title} (Status: {ticket.status})\n" for ticket in context.tickets)}

        ### Messages
        {"".join(f"- {message.content}\n" for message in context.messages)}

        ### Meeting Transcriptions
        {"".join(f"#### {meeting.title} (ID: {meeting.id})\n- {meeting.transcription}\n\n" for meeting in context.meeting_transcriptions)}
        """


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


def get_answer_for_project(project_id: str):
    # get all related tickets
    # results = get_tickets(project_id)

    # Query Neo4j for the subgraph based on the selected ticket project
    results = get_project_related_items(project_id)
    context = create_llm_context_from_results(results=results)
    formatted_context = format_entities_for_llm(context=context)

    answer = (
        generate_answer(formatted_context, user_query)
        if formatted_context
        else "No relevant data found."
    )

    return answer, formatted_context


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
        answer, formatted_context = get_answer_for_project(project_id=project_id)

    # Display results

    st.subheader(user_query)

    st.title("Generated Answer")
    st.write(answer)

    with st.expander(label="Graph Context"):
        st.write(formatted_context)
