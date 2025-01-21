import streamlit as st
from neo4j import GraphDatabase
from openai import OpenAI

from client import fetch_entity_data
from entity_parser import EntityParser, EntityTypes

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


def create_llm_context_from_results(results):
    context = {
        "tickets": [],
        "messages": [],
        "meeting_transcriptions": [],
    }

    for record in results:
        for ticket in record["tickets"]:
            external_id = EntityParser.parse_id(ticket["id"])
            data = fetch_entity_data(
                entity_type=external_id["type"], entity_id=external_id["id"]
            )
            if not data:
                continue
            context["tickets"].append(data)

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
                    context["messages"].append(data)
                elif external_id["type"] == EntityTypes.MEETING.value:
                    context["meeting_transcriptions"].append(data)

    print(context)
    return context


def generate_answer(context, question):
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
                "content": """
        You are an expert assistant specializing in providing clear and accurate answers based on graph-based data. Your role is to help users understand the relationships and insights within the data fetched from a graph database. 

When generating answers:
1. Always focus on the context provided, using it to construct concise, fact-based responses.
2. If the context lacks sufficient information to answer the user's question, acknowledge this and suggest clarifying queries or next steps.
3. Clearly explain relationships between entities (e.g., which users created posts, who liked them, or which comments were added to posts).
4. Ensure your tone is professional, approachable, and helpful.
5. Avoid making assumptions beyond the data presented in the context.

Here are some examples of how to approach queries:
- If asked "Who created the post titled 'Post 1 Title'?", respond with something like: "The post titled 'Post 1 Title' was created by Leanne Graham (ID: 1)."
- If asked "Which posts did User 2 like?", respond with: "User 2 liked the following posts: Post 1 Title (ID: 1)."
- If the question is unanswerable with the current context, respond with: "I couldn't find this information in the current data. Could you clarify or refine your question?"

Always aim to provide actionable, graph-based insights in a friendly and clear way.

        """,
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=150,
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
        formatted_context = f"""
        Tickets:
        {[ticket for ticket in context['tickets']]}

        Messages:
        {[message for message in context['messages']]}

        Meeting transcriptions:
        {[meeting for meeting in context['meeting_transcriptions']]}
        """

        if not context:
            context = "No data found for the given filter."

        # Generate answer
        answer = (
            generate_answer(context, user_query)
            if context
            else "No relevant data found."
        )

    # Display results
    st.subheader("Graph Context")
    st.text(formatted_context)

    st.subheader("Generated Answer")
    st.write(answer)
