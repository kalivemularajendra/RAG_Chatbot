import streamlit as st
import os
import datetime
from utils import (
    verify_user,
    register_user,
    get_conversational_agent,
    process_and_store_docs,
    load_vector_store,
    save_chat_history,
    load_chat_history,
    list_past_chats,
    delete_chat_history
)
from langchain_core.messages import AIMessage, HumanMessage

# --- Page Configuration ---
st.set_page_config(page_title="Chat with Your Data", layout="wide")

# --- Session State Initialization ---
# This block ensures all necessary keys are in st.session_state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "agent_executor" not in st.session_state:
    st.session_state.agent_executor = None
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

# --- User Authentication UI ---
def show_login_page():
    """Displays the login and registration forms."""
    st.title("Login / Register")

    menu = ["Login", "Register"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Login":
        st.subheader("Login Section")
        username = st.text_input("User Name")
        password = st.text_input("Password", type='password')

        if st.button("Login"):
            if verify_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                # Clear any previous session data
                st.session_state.agent_executor = None
                st.session_state.chat_history = []
                st.session_state.current_chat_id = None
                st.rerun()
            else:
                st.error("Incorrect Username or Password")

    elif choice == "Register":
        st.subheader("Create New Account")
        new_user = st.text_input("Username")
        new_password = st.text_input("Password", type='password')

        if st.button("Register"):
            if register_user(new_user, new_password):
                st.success("You have successfully created an account!")
                st.info("Go to the Login Menu to login")
            else:
                st.error("Username already exists.")

# --- Main Chat Application UI ---
def show_chat_page():
    """Displays the main chat interface after a user logs in."""
    user_dir = os.path.join("user_data", st.session_state.username)
    vector_store_path = os.path.join(user_dir, "faiss_index")

    # --- Sidebar ---
    with st.sidebar:
        st.title(f"Welcome, {st.session_state.username}!")
        
        if st.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        st.header("Your Chats")
        if st.button("➕ New Chat"):
            # Generate a unique chat ID using the current timestamp
            new_chat_id = f"chat_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            st.session_state.current_chat_id = new_chat_id
            st.session_state.chat_history = []
            st.rerun()

        st.subheader("Recent Chats")
        past_chats = list_past_chats(st.session_state.username)
        
        for chat_id, chat_title in past_chats.items():
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(chat_title, key=f"load_{chat_id}", use_container_width=True):
                    st.session_state.current_chat_id = chat_id
                    st.session_state.chat_history = load_chat_history(st.session_state.username, chat_id)
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_{chat_id}", use_container_width=True, help=f"Delete chat '{chat_title}'"):
                    delete_chat_history(st.session_state.username, chat_id)
                    if st.session_state.current_chat_id == chat_id:
                        st.session_state.current_chat_id = None
                        st.session_state.chat_history = []
                    st.rerun()
        
        # --- Data Source Management ---
        with st.expander("Data Source Management", expanded=not os.path.exists(vector_store_path)):
            source_type = st.radio("Choose source type:", ("Upload a File", "Enter a URL"))
            
            source_input = None
            if source_type == "Upload a File":
                uploaded_file = st.file_uploader("Upload your document", type=['pdf', 'docx', 'txt', 'csv'])
                if uploaded_file:
                    file_path = os.path.join(user_dir, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    source_input = file_path
            else:
                source_input = st.text_input("Enter the URL")

            if source_input and st.button("Process Data"):
                with st.spinner("Processing your data... This may take a moment."):
                    process_and_store_docs(st.session_state.username, source_input)
                    st.session_state.agent_executor = None  # Force agent to reload with new data
                st.success("Data processed successfully!")
                st.rerun()

    # --- Main Chat Area ---
    st.title("Chat with your Data")

    if not os.path.exists(vector_store_path):
        st.info("Please upload a document or URL from the 'Data Source Management' section in the sidebar to begin.")
        return

    # Load agent if not already in session state
    if st.session_state.agent_executor is None:
        with st.spinner("Loading AI agent..."):
            vector_store = load_vector_store(vector_store_path)
            st.session_state.agent_executor = get_conversational_agent(vector_store, "the provided document or web page")

    # Display chat interface if a chat is active
    if st.session_state.current_chat_id:
        # Display chat history
        for message in st.session_state.chat_history:
            role = "AI" if isinstance(message, AIMessage) else "Human"
            with st.chat_message(role):
                st.markdown(message.content)

        # Chat input box
        if user_query := st.chat_input("Ask a question about your data..."):
            st.session_state.chat_history.append(HumanMessage(content=user_query))
            with st.chat_message("Human"):
                st.markdown(user_query)

            with st.chat_message("AI"):
                with st.spinner("Thinking..."):
                    response = st.session_state.agent_executor.invoke({
                        "input": user_query,
                        "chat_history": st.session_state.chat_history
                    })
                    st.markdown(response["output"])
            
            st.session_state.chat_history.append(AIMessage(content=response["output"]))
            
            # Save the updated history to its file
            save_chat_history(st.session_state.username, st.session_state.current_chat_id, st.session_state.chat_history)
    else:
        # Welcome screen when no chat is selected
        st.info("Select a past conversation or start a new one from the sidebar.")
        st.markdown("### Welcome! 👋")
        st.markdown("I'm ready to help you analyze your data. Just upload a document or URL, then start a new chat!")

# --- Main App Logic ---
if not st.session_state.get("logged_in", False):
    show_login_page()
else:
    show_chat_page()