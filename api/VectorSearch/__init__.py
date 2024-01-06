import logging
import os
import azure.functions as func
import json
from langchain.chains import RetrievalQA
from langchain.memory import MongoDBChatMessageHistory
from langchain.memory import ConversationBufferMemory
from langchain.chat_models import AzureChatOpenAI
from langchain.agents import ZeroShotAgent, Tool, initialize_agent
from pymongo import MongoClient
from langchain.vectorstores.azure_cosmos_db import AzureCosmosDBVectorSearch
from langchain.embeddings import AzureOpenAIEmbeddings

# This function is called by the Azure Function App tp perform the vector search and call the OpenAI API
def vector_search_and_call_openai(sid,user_input):
    sid = sid

    CONNECTION_STRING = os.environ["CONNECTION_STRING"]
    INDEX_NAME = os.environ["INDEX_NAME"]
    NAMESPACE = os.environ["NAMESPACE"]
    DB_NAME, COLLECTION_NAME =NAMESPACE.split(".")

    # Initialize the LLM and Embeddings
    llm = AzureChatOpenAI(
        openai_api_version=os.environ["AZURE_OPENAI_VERSION"],
        openai_api_key=os.environ["AZURE_OPENAI_KEY"],
        azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"]
    )

    openai_embeddings = AzureOpenAIEmbeddings(
        openai_api_version=os.environ["AZURE_OPENAI_VERSION"],
        openai_api_key=os.environ["AZURE_OPENAI_KEY"],
        azure_deployment=os.environ["AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"]
    )

    client: MongoClient = MongoClient(CONNECTION_STRING)
    collection = client[DB_NAME][COLLECTION_NAME]

    # Initialize a connection to vector store to perform the search   
    vector_store = AzureCosmosDBVectorSearch.from_connection_string(
        connection_string=CONNECTION_STRING,
        embedding=openai_embeddings,
        namespace=NAMESPACE,
    )

    # Create a RetrievalQA object to perform the search
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_store.as_retriever()
    )


    # Tools for the agent to perform Retrieval Augmented Generation
    tools = [
        Tool("Contoso Electronics Handbook and Benefits Search",
        description = "use this tool to search for information related to contoso electronics employee benefits and handbook",
        func=qa.run)
    ]

    # You can create a memory to pass to an agent
    message_history = MongoDBChatMessageHistory(connection_string=f"{CONNECTION_STRING}", database_name="chatmemorydb", collection_name="chatemorycoll",session_id=sid)
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True, chat_memory=message_history)

    prefix = """Have a conversation with a human, answering the following questions based on Contoso Electronics Handbook and Benefits Search"""
    suffix = """Begin!"

    {chat_history}
    Question: {input}
    {agent_scratchpad}"""

    # Create the prompt template
    prompt = ZeroShotAgent.create_prompt(
        tools=tools,
        prefix=prefix,
        suffix=suffix,
        input_variables=["input", "chat_history", "agent_scratchpad"],
    )

    # Initialize the agent
    agent = initialize_agent(
        agent='chat-conversational-react-description',
        tools=tools,
        llm=llm,
        verbose=True,
        prompt=prompt,
        memory=memory
    )

    # Run the agent
    openai_response = agent.run(user_input)
    return openai_response


def main(req: func.HttpRequest) -> func.HttpResponse:

    req_body = req.get_json()
    sid = req_body.get('session_id')
    user_input = req_body.get('prompt')

    openai_response = vector_search_and_call_openai(sid,user_input)

    return func.HttpResponse(
            json.dumps({"output": openai_response}),
            status_code=200
        )