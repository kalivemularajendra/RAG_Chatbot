import os
import json
import hashlib
from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredWordDocumentLoader,
    TextLoader,
    WebBaseLoader,
    CSVLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools.retriever import create_retriever_tool
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage

# --- User Management Functions ---

def get_user_db():
    """Loads the user database from users.json, creating it if it doesn't exist."""
    if not os.path.exists("users.json"):
        with open("users.json", "w") as f:
            json.dump({}, f)
    with open("users.json", "r") as f:
        return json.load(f)

def save_user_db(db):
    """Saves the user database to users.json."""
    with open("users.json", "w") as f:
        json.dump(db, f, indent=4)

def hash_password(password):
    """Hashes a password for secure storage."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(username, password):
    """Verifies a user's credentials against the database."""
    db = get_user_db()
    if username in db and db[username] == hash_password(password):
        return True
    return False

def _ensure_chat_dir(username):
    """Ensures the 'chats' subdirectory exists for a user."""
    chat_dir = os.path.join("user_data", username, "chats")
    os.makedirs(chat_dir, exist_ok=True)
    return chat_dir

def register_user(username, password):
    """Registers a new user, returns False if the user already exists."""
    db = get_user_db()
    if username in db:
        return False
    db[username] = hash_password(password)
    save_user_db(db)
    # Create a dedicated directory and a chats subdirectory for the new user
    os.makedirs(os.path.join("user_data", username), exist_ok=True)
    _ensure_chat_dir(username)
    return True

# --- Document Loading and Processing ---

def load_document(file_path_or_url):
    """
    Loads a document from a local file path or a web URL.
    """
    if os.path.exists(file_path_or_url): # Check if it's a local file
        _, file_extension = os.path.splitext(file_path_or_url)
        if file_extension.lower() == '.pdf':
            loader = PyPDFLoader(file_path_or_url)
        elif file_extension.lower() == '.docx':
            loader = UnstructuredWordDocumentLoader(file_path_or_url)
        elif file_extension.lower() == '.txt':
            loader = TextLoader(file_path_or_url)
        elif file_extension.lower() == '.csv':
            loader = CSVLoader(file_path_or_url)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
    else: # Assume it's a URL
        try:
            loader = WebBaseLoader(file_path_or_url)
        except Exception as e:
            raise ValueError(f"Could not load from URL. Error: {e}")

    return loader.load()

# --- Conversational Agent Creation ---

def get_conversational_agent(vector_store, source_description):
    """
    Creates and returns a conversational agent with a retriever tool.
    """
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.7,
        convert_system_message_to_human=True
    )
    retriever = vector_store.as_retriever()
    retriever_tool = create_retriever_tool(
        retriever,
        "context_search",
        f"Search for information from {source_description}. For any questions about its content, you must use this tool!"
    )
    tools = [retriever_tool]
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant. You must use the provided tools to answer questions based on the context given. Use the conversation history to provide context."),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    agent = create_openai_tools_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    return agent_executor

def process_and_store_docs(username, file_or_url):
    """
    Processes a document/URL, creates a vector store, and saves it for the user.
    """
    user_dir = os.path.join("user_data", username)
    vector_store_path = os.path.join(user_dir, "faiss_index")
    docs = load_document(file_or_url)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    documents = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200).split_documents(docs)
    vectordb = FAISS.from_documents(documents, embeddings)
    vectordb.save_local(vector_store_path)

def load_vector_store(path):
    """Loads a FAISS vector store from a local path."""
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    return FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)

# --- Chat History Management Functions ---

def save_chat_history(username, chat_id, chat_history):
    """Saves chat history to a specific chat_id JSON file for a user."""
    chat_dir = _ensure_chat_dir(username)
    history_file = os.path.join(chat_dir, f"{chat_id}.json")
    
    serializable_history = []
    for msg in chat_history:
        if isinstance(msg, HumanMessage):
            serializable_history.append({"type": "human", "content": msg.content})
        elif isinstance(msg, AIMessage):
            serializable_history.append({"type": "ai", "content": msg.content})

    # Generate a title from the first human message
    title = "New Chat"
    if serializable_history and serializable_history[0]['type'] == 'human':
        first_message = serializable_history[0]['content']
        title = first_message[:50] + "..." if len(first_message) > 50 else first_message

    with open(history_file, "w") as f:
        json.dump({"title": title, "messages": serializable_history}, f, indent=4)

def load_chat_history(username, chat_id):
    """Loads a specific chat history from a JSON file for a user."""
    chat_dir = _ensure_chat_dir(username)
    history_file = os.path.join(chat_dir, f"{chat_id}.json")
    if not os.path.exists(history_file):
        return []
    
    try:
        with open(history_file, "r") as f:
            data = json.load(f)
            serializable_history = data.get("messages", [])
        
        history = []
        for msg_data in serializable_history:
            if msg_data["type"] == "human":
                history.append(HumanMessage(content=msg_data["content"]))
            elif msg_data["type"] == "ai":
                history.append(AIMessage(content=msg_data["content"]))
        return history
    except (json.JSONDecodeError, KeyError):
        return [] # Return empty list if file is corrupted or not in the expected format

def list_past_chats(username):
    """Lists past chats for a user, returning a dict of {chat_id: title}."""
    chat_dir = _ensure_chat_dir(username)
    chats = {}
    
    # Get all json files from the chat directory
    files = [f for f in os.listdir(chat_dir) if f.endswith('.json')]
    # Sort files by modification time (newest first)
    files.sort(key=lambda x: os.path.getmtime(os.path.join(chat_dir, x)), reverse=True)

    for file_name in files:
        chat_id = os.path.splitext(file_name)[0]
        file_path = os.path.join(chat_dir, file_name)
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                chats[chat_id] = data.get("title", chat_id)
        except json.JSONDecodeError:
            # If file is corrupted, use the filename as a fallback title
            chats[chat_id] = chat_id
            
    return chats

def delete_chat_history(username, chat_id):
    """Deletes a specific chat history file for a user."""
    chat_dir = _ensure_chat_dir(username)
    history_file = os.path.join(chat_dir, f"{chat_id}.json")
    if os.path.exists(history_file):
        os.remove(history_file)