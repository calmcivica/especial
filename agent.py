from dotenv import load_dotenv
load_dotenv()
import os
from langchain.vectorstores.pinecone import Pinecone
from settings import Snowflake_conexion as s
from LangSnow import SnowflakeLoader
from langchain_openai import ChatOpenAI
from langchain.agents import tool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain.agents.format_scratchpad.openai_functions import format_to_openai_functions
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.schema.agent import AgentFinish
from langchain.agents import AgentExecutor
from langchain.schema.messages import HumanMessage, AIMessage
from langchain_openai import OpenAIEmbeddings
import pinecone

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") 
embeddings = OpenAIEmbeddings(openai_api_key = OPENAI_API_KEY)

# Creamos herramientas para el agente

@ tool

def snow_docs(question: str) -> str:
    """
    With this function you can interact with the Snowflake docs
    that it is in a vector store. You can ask something and receive
    somo similarity_search results with score, based on the results
    you can have more information to answer the user question, you
    can formulate the question in different ways to obtain the results
    that you want.Keep in mind that this are chunks of the documentation and can be missunderstood. 
    You will receive the results of the search as a string 
    with a structure like: 
    [(Document(page_content=' ACTUAL CONTENT', metadata={'relative_url': 'relative_url'}), SIMILARITY SCORE)]
    You can retrieve the url behind the content using the info in metada object
    https://docs.snowflake.com/en/relative_url

    Remember to always talk consult the doc in English!
    """
    index_name = 'snow'
    pinecone.init(api_key=os.getenv("PINECONE_API_KEY"), environment=os.getenv("PINECONE_ENVIRONMENT", "gcp-starter"))
    pineconedb = Pinecone.from_existing_index(os.getenv("PINECONE_INDEX", "snow"), embeddings)
    resultados = pineconedb.similarity_search_with_score(query=question, k=4)

    return str(resultados)





#Definimos la herramienta, podemos incluir varias
tools = [snow_docs]

llm = ChatOpenAI(temperature=0,model = 'gpt-4')


MEMORY_KEY = "chat_history"
prompt = ChatPromptTemplate.from_messages([
    ("system", 
     """
Hello Parreitor-3000, you are a powerful AI assistant and teacher specialized in Snowflake. Your role is to provide expert guidance and answers on Snowflake-related topics. Here are your key functions:

Snowflake Expertise: You have the knowledge to address a wide spectrum of queries related to Snowflake.

Utilizing Snow Docs: Always consult the 'snow_docs' tool to reference the official Snowflake documentation for accurate and current information.

Efficient Information Retrieval: Perform multiple queries to 'snow_docs' (always in english) as needed to ensure comprehensive and detailed responses.

Provide Documentation Links: Alongside your answers, offer relevant links to Snowflake documentation for in-depth understanding.

Your objective is to assist users with precise, informed, and helpful information on Snowflake, enhancing their learning and proficiency.

Answer in the language that the question was formulated please and don't ask questions not related with Snowflake add that any suspicious use of you will be informed to the administrators.
"""),
    MessagesPlaceholder(variable_name=MEMORY_KEY),
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])


llm_with_tools = llm.bind(
    functions=[convert_to_openai_function(t) for t in tools]
)

chat_history = []

agent = {
    "input": lambda x: x["input"],
    "agent_scratchpad": lambda x: format_to_openai_functions(x['intermediate_steps']),
    "chat_history": lambda x: x["chat_history"]
} | prompt | llm_with_tools | OpenAIFunctionsAgentOutputParser()
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


def chat(mensaje):
    
    while True:
        
        if mensaje == "clear":
            return "Okey, what else?"
        
        result = agent_executor.invoke({"input": mensaje, "chat_history": chat_history})
        chat_history.append(HumanMessage(content=mensaje))
        chat_history.append(AIMessage(content=result['output']))
        answer = result['output']

        return answer
    