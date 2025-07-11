# Chat with Your Data

A Streamlit-based conversational AI application that allows users to upload documents or provide URLs and chat with their data using Google's Gemini AI model.

## Features

- **User Authentication**: Secure login and registration system
- **Document Processing**: Support for PDF, DOCX, TXT, CSV files, and web URLs
- **Vector Database**: Uses FAISS for efficient document retrieval
- **Chat History**: Persistent chat sessions with the ability to manage multiple conversations
- **Conversational AI**: Powered by Google's Gemini 2.0 Flash model
- **User-Specific Data**: Each user has their own isolated data storage

## Prerequisites

- Python 3.8+
- Google API Key for Gemini AI
- Internet connection for web-based document loading

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd chat-with-your-data
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Set up your Google API key:
   - Get your API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Set it as an environment variable:
     ```bash
     export GOOGLE_API_KEY="your_api_key_here"
     ```
   - Or create a `.env` file in the project root:
     ```
     GOOGLE_API_KEY=your_api_key_here
     ```

## Usage

1. Start the application:
```bash
streamlit run main.py
```

2. Open your web browser and navigate to `http://localhost:8501`

3. **Register or Login**:
   - Create a new account or login with existing credentials
   - User data is stored locally in `users.json`

4. **Upload Data**:
   - Use the sidebar to upload documents or enter URLs
   - Supported formats: PDF, DOCX, TXT, CSV, and web pages
   - The system will process and create a vector database for your data

5. **Start Chatting**:
   - Click "New Chat" to begin a conversation
   - Ask questions about your uploaded data
   - The AI will retrieve relevant information and provide answers

6. **Manage Conversations**:
   - View past chats in the sidebar
   - Delete unwanted conversations
   - Each chat is automatically titled based on the first message

## File Structure

```
project/
├── main.py              # Main Streamlit application
├── utils.py             # Utility functions for data processing and user management
├── requirements.txt     # Python dependencies
├── users.json          # User authentication database (created automatically)
└── user_data/          # User-specific data storage (created automatically)
    └── [username]/
        ├── faiss_index/    # Vector database files
        ├── chats/          # Chat history files
        └── [uploaded_files]
```

## Dependencies

- **streamlit**: Web application framework
- **langchain**: LLM application framework
- **langchain_core**: Core LangChain components
- **langchain_community**: Community-contributed LangChain components
- **langchain_google_genai**: Google Generative AI integration
- **langchain_text_splitters**: Text splitting utilities

## Security Notes

- Passwords are hashed using SHA-256 before storage
- Each user's data is isolated in separate directories
- User authentication is handled locally (not suitable for production without additional security measures)

## Configuration

The application uses the following default settings:
- **Chunk Size**: 1000 characters
- **Chunk Overlap**: 200 characters
- **Model**: Gemini 2.0 Flash
- **Temperature**: 0.7
- **Embedding Model**: models/embedding-001

## Troubleshooting

### Common Issues

1. **"Module not found" errors**:
   - Ensure all dependencies are installed: `pip install -r requirements.txt`

2. **Google API errors**:
   - Verify your API key is set correctly
   - Check that the API key has the necessary permissions

3. **File upload issues**:
   - Ensure uploaded files are in supported formats
   - Check file size limits (Streamlit has a default 200MB limit)

4. **Vector store errors**:
   - Delete the `faiss_index` folder in your user directory and re-upload your data

### Logs and Debugging

- Enable verbose mode by setting the agent's `verbose=True` parameter in `utils.py`
- Check the Streamlit console for error messages
- Ensure proper file permissions for the `user_data` directory


## Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Powered by [Google's Gemini AI](https://ai.google.dev/)
- Uses [LangChain](https://langchain.com/) for LLM orchestration
- Vector search with [FAISS](https://faiss.ai/)
