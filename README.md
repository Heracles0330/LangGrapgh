# Cheese Shopping Agent

A LangGraph-powered AI agent for assisting users with cheese product information.

## Architecture

This project uses an advanced agent architecture with:

1. **Reasoning-First Design**
   - Planning node creates high-level steps
   - Reasoning node selects appropriate tools
   - Cyclic execution with evaluation after each step

2. **Multi-Source Search**
   - Pinecone vector search for semantic understanding
   - MongoDB for structured queries and filtering
   - Web search for real-time information

3. **Human-in-the-Loop**
   - Clarification requests when queries are ambiguous
   - Interactive UI for refinement and exploration

4. **Parallel Execution**
   - Multiple search methods can run concurrently
   - Efficient processing with ThreadPoolExecutor

5. **LangSmith Integration**
   - Tracing and monitoring of agent execution
   - Tool call tracking and performance analysis

## Environment Setup

### MongoDB Setup

1. Create a MongoDB Atlas account at https://www.mongodb.com/cloud/atlas/register
2. Create a new cluster (the free tier is sufficient)
3. In the Security section, create a database user with read/write privileges
4. In the Network section, add your IP address to the access list or allow access from anywhere (0.0.0.0/0)
5. In the Database section, click "Connect" and select "Connect your application"
6. Copy the connection string and replace the placeholders with your username and password

### Pinecone Setup

1. Create a Pinecone account at https://www.pinecone.io/
2. Create a new index with dimension 1536 (for OpenAI embeddings)
3. Copy your API key and environment name

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```
# MongoDB Configuration
MONGODB_CONNECTION_STRING=mongodb+srv://username:password@cluster.mongodb.net/cheese_shop?retryWrites=true&w=majority

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=gcp-starter

# OpenAI Configuration (for embeddings and LLM)
OPENAI_API_KEY=your_openai_api_key

# LangSmith Configuration (optional, for tracing)
LANGCHAIN_API_KEY=your_langchain_api_key
LANGCHAIN_PROJECT=cheese-agent
LANGCHAIN_TRACING_V2=true
```

### Testing MongoDB Connection

Run the test script to verify your MongoDB connection:

```bash
python test_mongodb.py
```

If successful, you should see the available databases and collections.

## Loading Data

To load the pre-scraped cheese data into MongoDB and Pinecone:

```bash
python -m data.loader
```

This will download the data from Google Drive and import it into both databases.

## Running the Application

Start the Streamlit app:

```bash
streamlit run app.py
``` 