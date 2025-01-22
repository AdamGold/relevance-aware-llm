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

# Neo4j connection details
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "wgyB5Mdqae3icKy"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# OpenAI API setup
openai_api_key = "XXX"
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


# Streamlit UI
st.title("Graph RAG App")

st.sidebar.header("Input Section")
# Let the user pick a ticket project
project_id = st.sidebar.selectbox(
    "Select a Project:",
    ["ticket|project|1", "ticket|project|2"],
)


user_query = st.sidebar.text_input("Ask a question:", placeholder="Who created post 1?")
if st.sidebar.button("Submit"):
    with st.spinner("Querying the graph and fetching data..."):
        # Query Neo4j for the subgraph based on the selected ticket project
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
        results = query_graph(graph_query)

        # Fetch data from JSONPlaceholder
        context = create_llm_context_from_results(results=results)
        formatted_context = format_entities_for_llm(context=context)

        if not context:
            context = "No data found for the given filter."

        # Generate answer
        answer = (
            generate_answer(formatted_context, user_query)
            if context
            else "No relevant data found."
        )

    # Display results

    st.subheader("Generated Answer")
    st.write(answer)

    st.subheader("Graph Context")
    st.text(formatted_context)
