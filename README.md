# docubot-slack

A Slack chatbot powered by Retrieval-Augmented Generation (RAG) that can answer questions based on your PDF documents. The bot uses Groq's LLM, Pinecone for vector storage, and HuggingFace embeddings to provide accurate, context-aware responses.

## Features

- **PDF Document Processing**: Automatically processes PDF files and creates a searchable knowledge base
- **RAG Pipeline**: Retrieves relevant document chunks to provide contextual answers
- **Slack Integration**: Native Slack bot with rich message formatting
- **Real-time Updates**: Reload your knowledge base without restarting the bot
- **Vector Search**: Powered by Pinecone for fast and accurate document retrieval
- **Conversation Memory**: Maintains context across conversations

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────┐
│   Slack App     │◄──►│   RAG Engine │◄──►│  Pinecone   │
│                 │    │              │    │  Vector DB  │
└─────────────────┘    └──────┬───────┘    └─────────────┘
                              │
                       ┌──────▼───────┐
                       │   Groq LLM   │
                       │ (Llama 3.3)  │
                       └──────────────┘
```

The system processes PDF documents, creates embeddings using HuggingFace models, stores them in Pinecone, and uses Groq's Llama model to generate responses based on retrieved context.

## 📋 Prerequisites

- Python 3.8+
- Slack workspace with bot permissions
- Pinecone account and API key
- Groq API key
- (Optional) MongoDB for additional data storage

## 🔧 Installation

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd pdf-knowledge-slack-bot
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Setup

Create a `.env` file in the project root:

```env
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_APP_TOKEN=xapp-your-app-token-here

# Groq Configuration
GROQ_API_KEY=your-groq-api-key-here

# Pinecone Configuration
PINECONE_API_KEY=your-pinecone-api-key-here

# MongoDB Configuration (Optional)
MONGODB_URI=mongodb://localhost:27017
```

### 4. Slack App Configuration

1. **Create a Slack App**:
   - Go to [api.slack.com](https://api.slack.com/apps)
   - Click "Create New App" → "From scratch"
   - Enter app name and select your workspace

2. **Enable Socket Mode**:
   - Go to "Socket Mode" in your app settings
   - Enable Socket Mode and generate an App-Level Token
   - Copy the token (starts with `xapp-`) to your `.env` file

3. **Configure Bot Permissions**:
   - Go to "OAuth & Permissions"
   - Add these Bot Token Scopes:
     - `chat:write`
     - `channels:history`
     - `groups:history`
     - `im:history`
     - `mpim:history`
     - `files:read`
   - Install the app to your workspace
   - Copy the Bot User OAuth Token (starts with `xoxb-`) to your `.env` file

4. **Enable Events**:
   - Go to "Event Subscriptions"
   - Enable Events
   - Subscribe to these bot events:
     - `message.channels`
     - `message.groups`
     - `message.im`
     - `message.mpim`
     - `file_shared`

### 5. External Service Setup

#### Groq API
1. Sign up at [console.groq.com](https://console.groq.com)
2. Create an API key
3. Add it to your `.env` file

#### Pinecone
1. Sign up at [pinecone.io](https://pinecone.io)
2. Create a project and get your API key
3. Add it to your `.env` file

## Usage

### Starting the Bot

```bash
python main.py
```

The bot will:
1. Initialize Pinecone vector database
2. Load embedding models
3. Process any PDFs in the `./pdfs` folder
4. Start the Slack connection

### Adding Documents

1. Place your PDF files in the `./pdfs` folder
2. Use the `/reload_pdfs` command in Slack to process new documents
3. The bot will extract text, create embeddings, and store them in Pinecone

### Bot Commands

- **`/reload_pdfs`**: Process all PDFs in the pdfs folder and update the knowledge base
- **`/index_stats`**: Display Pinecone index statistics and vector counts
- **Regular messages**: Ask questions about your documents

### Example Interactions

```
User: What is the main topic of the annual report?
Bot: Based on the annual report document, the main topic focuses on...

User: /reload_pdfs
Bot: 📄 PDF knowledge base reloaded. Uploaded 45 document chunks to Pinecone.

User: /index_stats
Bot: 📊 Pinecone Index Stats
     {
       "total_vector_count": 45,
       "dimension": 384,
       "index_fullness": 0.001
     }
```

## 📁 Project Structure

```
pdf-knowledge-slack-bot/
├── main.py                 # Entry point and initialization
├── slack_app.py            # Slack bot implementation
├── rag.py                  # RAG chain configuration
├── pinecone_client.py      # Pinecone vector database client
├── embeddings.py           # HuggingFace embedding models
├── pdf_processor.py        # PDF text extraction and chunking
├── utils.py                # Utility functions
├── mongo_utils.py          # MongoDB helper functions (optional)
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (create this)
└── pdfs/                   # Directory for PDF documents
```

## 🔧 Configuration

### Embedding Model
The default embedding model is `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions). To change:

```python
# In embeddings.py
def load_embeddings(model_name: str = "your-preferred-model", device: str = "cpu"):
```

### LLM Model
The default LLM is `llama-3.3-70b-versatile`. To change:

```python
# In rag.py
llm = ChatGroq(api_key=os.environ.get("GROQ_API_KEY"), model="your-preferred-model", temperature=0.1)
```

### Chunking Parameters
Adjust document chunking in `pdf_processor.py`:

```python
def chunk_documents(documents, chunk_size: int = 1000, chunk_overlap: int = 200):
```

### Vector Search
Modify search parameters in `slack_app.py`:

```python
search_res = index.query(vector=query_embedding, top_k=5, include_metadata=True)
```

## 🛠️ Troubleshooting

### Common Issues

1. **"RAG unavailable" message**:
   - Check your Pinecone API key
   - Ensure the Pinecone index was created successfully
   - Verify embedding model loaded correctly

2. **No documents found**:
   - Ensure PDF files are in the `./pdfs` folder
   - Check that PDFs contain selectable text (not scanned images)
   - Run `/reload_pdfs` command

3. **Slack connection issues**:
   - Verify bot token and app token in `.env`
   - Check bot permissions in Slack app settings
   - Ensure Socket Mode is enabled

4. **Empty responses**:
   - Check Groq API key and quota
   - Verify the LLM model name is correct
   - Look for error messages in console output

### Debugging

Enable verbose logging by setting environment variable:

```bash
export LANGCHAIN_VERBOSE=true
python main.py
```

Check console output for detailed processing information.

## 🔒 Security Notes

- Keep your `.env` file secure and never commit it to version control
- Use environment-specific API keys
- Consider implementing user authentication for production use
- Regularly rotate API keys

## 📝 Dependencies

- **slack-bolt**: Slack app framework
- **python-dotenv**: Environment variable management
- **PyPDF2**: PDF text extraction
- **pinecone**: Vector database client
- **langchain**: LLM application framework
- **langchain-groq**: Groq LLM integration
- **langchain-huggingface**: HuggingFace embeddings
- **sentence-transformers**: Text embedding models
- **pymongo**: MongoDB client (optional)

## 🚀 Deployment

### Local Development
```bash
python main.py
```

### Production Deployment

1. **Using Docker**:
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

2. **Using systemd** (Linux):
```ini
[Unit]
Description=PDF Knowledge Slack Bot
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/your/bot
ExecStart=/usr/bin/python3 main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Commit your changes: `git commit -m 'Add feature'`
5. Push to the branch: `git push origin feature-name`
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter issues or have questions:
1. Check the troubleshooting section above
2. Review the console output for error messages
3. Create an issue on GitHub with detailed information
4. Include your environment details and error logs (without sensitive information)
