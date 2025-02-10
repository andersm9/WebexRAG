
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableBranch
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.runnables import RunnablePassthrough
from langchain.memory import ChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.document_loaders import TextLoader
from langchain.callbacks.tracers import ConsoleCallbackHandler
from langchain.globals import set_verbose
from langchain.globals import set_debug
from langchain.chat_models import AzureChatOpenAI
from langchain_community.document_loaders import UnstructuredPowerPointLoader
import tomllib
import base64
import dotenv

from pprint import pprint
import requests
from os import walk
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import Docx2txtLoader
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import UnstructuredXMLLoader
from langchain_community.document_loaders import UnstructuredExcelLoader

with open("config/settings.toml", "rb") as f:
    settings = tomllib.load(f)
client_id  = settings['BridgeIT']['client_id']
client_secret  = settings['BridgeIT']['client_secret']  
CISCO_OPENAI_APP_KEY = settings['BridgeIT']["CISCO_OPENAI_APP_KEY"]
CISCO_BRAIN_USER_ID =  settings['BridgeIT']["CISCO_BRAIN_USER_ID"]
url = settings['BridgeIT']["url"]
payload = settings['BridgeIT']["payload"]

value = base64.b64encode(f'{client_id}:{client_secret}'.encode('utf-8')).decode('utf-8')
headers = {
    "Accept": "*/*",
    "Content-Type": "application/x-www-form-urlencoded",
    "Authorization": f"Basic {value}"
}
set_debug(False)
set_verbose(False)
dotenv.load_dotenv()
userStore = {}

def token_refresh():
    print("token_refresh engaged")
    global token_response
    token_response = requests.request("POST", url, headers=headers, data=payload)
    print("Token_refresh complete")
    return None

def chatUpdate():
    global chat
    print("chatUpdate engaged")
    chat = AzureChatOpenAI(deployment_name="gpt-4o-mini", 
                    temperature=0.00,
                    azure_endpoint = 'https://chat-ai.cisco.com', 
                    api_key=token_response.json()["access_token"],  
                    api_version="2023-08-01-preview",
                    model_kwargs=dict(
                    user=f'{{"appkey": "{CISCO_OPENAI_APP_KEY}", "user": "{CISCO_BRAIN_USER_ID}"}}'
                    )
    ) 
    print("chatUpdate complete")

def chainUpdate():
    global query_transform_prompt
    global query_transforming_retriever_chain
    global question_answering_prompt
    global document_chain
    global demo_ephemeral_chat_history
    global conversational_retrieval_chain
    print("chainUpdate engaged")
    query_transform_prompt = ChatPromptTemplate.from_messages(
    [
        MessagesPlaceholder(variable_name="messages"),
        (
            "user",
            "Given the above conversation, generate a search query to look up in order to get information relevant to the conversation. Only respond with the query, nothing else."
        ),
    ]
    )   

    query_transforming_retriever_chain = RunnableBranch(
        (
            lambda x: len(x.get("messages", [])) == 1,
            # If only one message, then we just pass that message's content to retriever
            (lambda x: x["messages"][-1].content) | retriever,
        ),
        # If messages, then we pass inputs to LLM chain to transform the query, then pass to retriever
        query_transform_prompt | chat | StrOutputParser() | retriever,
        ).with_config(run_name="chat_retriever_chain")

    question_answering_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Answer the user's questions based on the below context. Try to include the following information, customer name, technology deployed (e.g. MX,MR,MS etc), and benefits seen from deploying the solution:\n\n{context}",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    document_chain = create_stuff_documents_chain(chat, question_answering_prompt)

    conversational_retrieval_chain = RunnablePassthrough.assign(
        context=query_transforming_retriever_chain,
    ).assign(
        answer=document_chain,
    )
    print("chainUpdate complete")
    
def sources():
    global retriever
    print("Sources engaged")
    data = []
    mypath ='./Content'
    filenames = next(walk(mypath), (None, None, []))[2]  # [] if no file

    for file in filenames:
        if '.pdf' in file:
            file_path = mypath + "/" + str(file)
            print(file_path)
            loader = PyPDFLoader(str(file_path))
            data.extend(loader.load())
        if '.pptx' in file:
            file_path = mypath + "/" + str(file)
            print(file_path)
            loader = UnstructuredPowerPointLoader(str(file_path))
            data.extend(loader.load())
        if '.docx' in file:
            file_path = mypath + "/" + str(file)
            print(file_path)
            loader = Docx2txtLoader(str(file_path))
            data.extend(loader.load())
        if '.txt' in file:
            file_path = mypath + "/" + str(file)
            print(file_path)
            loader = TextLoader(str(file_path))
            data.extend(loader.load())
        if '.csv' in file:
            file_path = mypath + "/" + str(file)
            print(file_path)
            loader = TextLoader(str(file_path))
            data.extend(loader.load())
        if '.xml' in file:
            file_path = mypath + "/" + str(file)
            print(file_path)
            loader = UnstructuredXMLLoader(str(file_path))
            data.extend(loader.load())
        if '.xlsx' in file:
            file_path = mypath + "/" + str(file)
            print(file_path)
            loader = UnstructuredExcelLoader(str(file_path))
            data.extend(loader.load())


    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=25)
    all_splits = text_splitter.split_documents(data)


    vectorstore = Chroma.from_documents(documents=all_splits, embedding=OpenAIEmbeddings())

    retriever = vectorstore.as_retriever(search_type="similarity_score_threshold", search_kwargs={"score_threshold": 0.65,"k": 1})
    print("Sources complete")
token_refresh()
sources()
chatUpdate()
chainUpdate()

def BridgeIT(email,question):
    global demo_ephemeral_chat_history
    global response
    global demo_ephemeral_chat_history
    global query_transform_prompt
    global query_transforming_retriever_chain
    global question_answering_prompt
    global document_chain
    global conversational_retrieval_chain
    print(f"debug - in  BridgeIT with email {email} and  question: {question}")

    try:
        print("in Try loop")
        print(f"userStore = {userStore}")
        if email in userStore:
            print("This user has a conversation stored")
            demo_ephemeral_chat_history = userStore[email]
            print(demo_ephemeral_chat_history)

        else:
            print("No conversation stored fro this user")
            demo_ephemeral_chat_history = ChatMessageHistory()

        demo_ephemeral_chat_history.add_user_message(question)
        response = conversational_retrieval_chain.invoke(
            {"messages": demo_ephemeral_chat_history.messages},
            config={'callbacks': [ConsoleCallbackHandler()]}
            )
        demo_ephemeral_chat_history.add_ai_message(response["answer"])
        print("The following is the demo_ephemeral_chat_history messages:\n")
        print(demo_ephemeral_chat_history.messages)
        print("end of demo_ephemeral_chat_history")

        userStore[email] = demo_ephemeral_chat_history
        print("------------------------end of Std answer-----------------------\n")
        dataSource = response["context"][0].metadata['source']
        return("\n" + response["answer"]+ "\n" + "The source of this response is" + dataSource + "\n" + "AI results are experimantal and should be validated before use")

    except:
        print("In Exception Loop instigating a refresh")
        token_refresh()
        chatUpdate()
        chainUpdate()
        demo_ephemeral_chat_history.add_user_message(question)
        response = conversational_retrieval_chain.invoke(
            {"messages": demo_ephemeral_chat_history.messages},
            config={'callbacks': [ConsoleCallbackHandler()]}
            )
        demo_ephemeral_chat_history.add_ai_message(response["answer"])
        pprint(response["answer"])
        print("------------------------end of Exception answer-----------------------\n")
        try:
            dataSource = response["context"][0].metadata['source']
        except:
            dataSource = "no data source found"

        return("\n" + response["answer"]+ "\n" + "The source of this response is" + dataSource  + "\n" + "AI results are experimantal and should be validated before use")
