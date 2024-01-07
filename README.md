# Chat with Enterprise data using Azure OpenAI and Azure Cosmos DB for MongoDB vCore 

## Scope

The Retrieval Augmentation Generation (RAG) pattern enhances the capabilities of a Large Language Model (LLM) by integrating an information retrieval system that offers grounding data for logical reasoning. In the context of enterprise applications, the RAG patter empowers Generative AI application to focus on content specifically derived from vectorized documents, images, audio, and video within the enterprise.

This document outlines the design strategy for creating such an applicaiton integrating Azure OpenAI and Azure Cosmos DB for MongoDB vCore to intract with your proprietary data .To achieve this, Azure Functions orchestrates the search and retrieval process from Azure Cosmos DB for MongoDB vCore and sends it to Azure OpenAI for reasoning and generating a respsonse specific to user request(prompt). 
Additionally, the Azure Functions manages the session state and chat memory, storing them in a dedicated collection within the same database to facilitate contextual interactions.

## Solution Architecture 
![App Architecture](CosmosDBVectorDatabaseSessionstateMemory.png)

The RAG pattern for Azure Cosmos DB for MongoDB vCore vector search involves the following high-level steps:
1. Begin with a user question or request (prompt).
2. Submit the prompt to Azure Cosmos DB for MongoDB vCore vector search to identify pertinent information.
3. Forward the top-ranked search results to the Azure OpenAI.
4. Leverage the natural language understanding and reasoning capabilities of the Azure OpenAI. to generate a response to the initial prompt.
5. Save both the user prompt and the corresponding OpenAI response in a MongoDB collection. This collection will serve as the context  for subsequent follow-up questions and conversations.

To facilitate this process, the data intended for search needs to be segmented and embedded for vector search. The upcoming section illustrates the utilization of LangChain libraries.

### Prepare data and create index for vector search 
Create a python virtual environment and install required packages.
```
python -m venv .venv
. .venv/Scripts/activate
```
Ensure that the required packages are installed and accessible in the Python environment before using the code.
```
pip install pymongo langchain openai tiktoken azure-storage-blob pdf2image tabulate unstructured[pdf]
```
Note: Find attached a iPyhton notebook (cosmosdbLLMSearch-Contoso-employee-HandBook.ipynb) that you can use to create vector index and test the RAG process.

### Loading data from Azure Storage Account and split it into smaller chunks:

Copy the PDF documents from "data" folder in this repository to a Azure Storage Account container 

![Source File](source-files.png)

Execute the following code that uses LangChain's document loaders and text splitter modules to load PDF documents, split it into smaller chunks and store the result in a 'documents' object.

- `conn_str`: This is the connect string of the storage account ot ADLS where your pdf files are placed".
- `container`: This is the name of the storage account or ADLS container name where your pdf files are placed".
```
from langchain.document_loaders import AzureBlobStorageContainerLoader
loader = AzureBlobStorageContainerLoader(conn_str="DefaultEndpointsProtocol=https;AccountName=storage-account-name;AccountKey=storage-account-key;EndpointSuffix=core.windows.net", container="name-of-your-container")
documents = loader.load_and_split()
 ```
The 'documents' object now contains the split text from the PDF document.
Create an instance of the `AzureOpenAIEmbeddings` class from the `langchain` package. This is used to generate embeddings (numerical representations of text) using Azure's OpenAI services. 
```
openai_embeddings = AzureOpenAIEmbeddings(
    openai_api_version="your-open-ai-model-version",
    openai_api_key="your-open-ai-model-key",
    azure_deployment = "your-open-ai-embedding-deployment-name",
    azure_endpoint="your-open-ai-model-endpoint-url") 
```
Here's a breakdown of the Azure Open AI parameters:
- `openai_api_version`: This is the version of the OpenAI API to use. In this case, it's set to "2023-07-01-preview".
- `openai_api_key`: This is the API key used to authenticate with the OpenAI API. 
- `azure_deployment`: This is the name of the Azure deployment to use. In this case, it's set to "text-embedding-ada-002".
- `azure_endpoint`: This is the endpoint of the Azure service to use. In this case, it's set to 

### Create embedding and load to Azure Cosmodb for MongoDb vCore:

The following script sets up a connection to a Azure Cosmodb for MongoDb v core , creates an index for vector search and loads the data into it. Note: the `openai_embeddings` object defined in the previous step is used to generate embeddings for the text data in 'documents' object before loading it into the vector index.

Replace the connection string for the MongoDB database, the name of the index to create, and the namespace for the MongoDB collection. Note: The namespace is split into the database name and the collection name.

Here's a breakdown of the CosmosDB parameters:
- `CONNECTION_STRING`:  Azure Cosmodb for MongoDb v core connection string.
- `INDEX_NAME`: Azure Cosmodb for MongoDb v core Index to be created.
- `NAMESPACE`: Azure Cosmodb for MongoDb v core namespace (Format: database-name.collection-name).
- `DB_NAME, COLLECTION_NAME `: database name and collectionname will be derived from the above NAMESPACE parameter.

```
# Create a vector index and load data using LangChian libraries
from pymongo import MongoClient

from langchain.vectorstores.azure_cosmos_db import AzureCosmosDBVectorSearch,CosmosDBSimilarityType

CONNECTION_STRING = "mongodb+srv://cosmosdb-username:cosmosdb-password@cosmosdb-name.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000"
INDEX_NAME = "contoso-employee-handbook-index1"
NAMESPACE = "contoso-employee-db1.contoso-employee-collection1"
DB_NAME, COLLECTION_NAME = NAMESPACE.split(".")


client: MongoClient = MongoClient(CONNECTION_STRING)
collection = client[DB_NAME][COLLECTION_NAME]

print(collection)

vectorstore = AzureCosmosDBVectorSearch.from_documents(
    documents,
    openai_embeddings,
    collection=collection,
    index_name=INDEX_NAME,
)

num_lists = 100
dimensions = 1536
similarity_algorithm = CosmosDBSimilarityType.COS

vectorstore.create_index(num_lists, dimensions, similarity_algorithm)
```

Login to Azure Cosmos DB for MongoDB vCore and verifiy if the Vector collection was created and pouplated with vector by above script.
Screenshot of Vector content stored in Azure Cosmos DB for MongoDB vCore.

![Azure Cosmos DB for MongoDB vCore - Vector collection](vector-content-in-cosmos-mongovcore.png)

### Test the RAG pattern and chat memory functionalities

Replace the following with your environment specific values

- `openai_api_version`: This is the version of the OpenAI API to use. In this case, it's set to "2023-07-01-preview".
- `openai_api_key`: This is the API key used to authenticate with the OpenAI API. 
- `azure_deployment`: This is the name of the Azure deployment to use. In this case, it's set to "text-embedding-ada-002".
- `azure_endpoint`: This is the endpoint of the Azure service to use. In this case, it's set to 

```
from langchain.chains import RetrievalQA
from langchain.memory import RedisChatMessageHistory,MongoDBChatMessageHistory
from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI,AzureChatOpenAI
from langchain.agents import ZeroShotAgent, Tool, AgentExecutor,initialize_agent

sid ="your_session_id"

llm = AzureChatOpenAI(    
    openai_api_version="your-open-ai-model-version",
    openai_api_key="your-open-ai-key",
    azure_deployment = "our-open-ai-deployment-name",
    azure_endpoint="our-open-ai-endpoint-url")


vector_store = AzureCosmosDBVectorSearch.from_connection_string(
    connection_string=CONNECTION_STRING,
    embedding=openai_embeddings,
    namespace=NAMESPACE,
)

qa = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vector_store.as_retriever(),
    verbose=True
)

tools = [
    Tool("Contoso Electronics Handbook and benefits Search",
    description = "use this tool to search for information related to contoso electronics employee benefits and handbook",
     func=qa.run)
]

message_history = MongoDBChatMessageHistory(connection_string=f"{CONNECTION_STRING}", database_name="chatmemorydb", collection_name="chatemorycoll",session_id=sid)
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True, chat_memory=message_history)

prefix = """Have a conversation with a human, answering the following questions based on LLM knowledge , current events or Contoso Electronics Benefit Knowledge Base"""
suffix = """Begin!"

{chat_history}
Question: {input}
{agent_scratchpad}"""

prompt = ZeroShotAgent.create_prompt(
    tools=tools,
    prefix=prefix,
    suffix=suffix,
    input_variables=["input", "chat_history", "agent_scratchpad"],
)

agent = initialize_agent(
    agent='chat-conversational-react-description',
    tools=tools,
    llm=llm,
    verbose=True,
    prompt=prompt,
    memory=memory)

agent.run(input="what are difference between stand and plus plans offered to contoso employees?")
```

## Follow the instructions in these link to setup Azure Static web App and Azure Functions and publish the application.

    - https://learn.microsoft.com/en-us/azure/static-web-apps/getting-started?tabs=react
    - https://learn.microsoft.com/en-us/azure/static-web-apps/add-api?tabs=vanilla-javascript

- After the Azure Static Web App is created , right click on the Static web app and clone the repository and copy the followiing files to the cloned respository.

        ├── api
        │   ├── VectorSearch
        │   │   ├── function.json
        │   │   └── __init__.py
        │   ├── host.json
        │   ├── local.settings.json
        │   └── requirements.txt
        │
        └── src
        ├── public
        ├── package.json
        ├── package-lock.json
        ├── staticwebapp.config

## Open you Chat application and test.

You can find the applicatoin URL in the Azure Static Web App home page

![App URL](chat-link.png)

## Conclusion

This sample application demonstrates how to use Azure Cosmos DB for MongoDB vCore as a central database to securely store and perform vector searchs, and it also shows how to it stores and retains history in the same database to answer subsequent questions.

Additionally, this appliation demostrates the Retrieval Augmented Generation technique orchestrated by Azure Function to perform vector search and pass relavent data into your OpenAI models using LangChain librairs for reasoning.

Screenshot of Chat application showing vector search and data retrival from  Azure Cosmos DB for MongoDB vCore.

![App URL](chat-sample.png)

Screenshot of Vector content stored in Azure Cosmos DB for MongoDB vCore.

![Azure Cosmos DB for MongoDB vCore - Vector collection](vector-content-in-cosmos-mongovcore.png)

Screenshot of chat history stored in Azure Cosmos DB for MongoDB vCore.

![Azure Cosmos DB for MongoDB vCore - Chat History Collection](chat-history-in-cosmos-mongovcore.png)