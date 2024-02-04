import os
from mem0 import Memory

os.environ["OPENAI_API_KEY"] = "sk-e884df8670e544a8b7d0c765760f2c19"
os.environ["OPENAI_BASE_URL"] = "https://api.deepseek.com/beta"
config = {
    "llm": {
        "provider": "openai",
        "config": {
            "model": "deepseek-chat",
            "temperature": 0.7,
            "max_tokens": 8000,
        }
    },
    "graph_store": {
        "provider": "neo4j",
        "config": {
            "url": "neo4j+s://localhost:7687",
            "username": "neo4j",
            "password": "N@eo4j852853"
        }
    },
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "test",
            "host": "localhost",
            "port": 6333,
            "embedding_model_dims": 768,  # Change this according to your local model's dimensions
        },
    },
    "embedder": {
        "provider": "ollama",
        "config": {
            "model": "nomic-embed-text:latest",
            # Alternatively, you can use "snowflake-arctic-embed:latest"
            "ollama_base_url": "http://localhost:11434",
        },
    },
}

m = Memory.from_config(config)
m.add("Likes to play cricket on weekends", user_id="alice", metadata={"category": "hobbies"})
