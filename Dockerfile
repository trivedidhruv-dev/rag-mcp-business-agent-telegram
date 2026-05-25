# Use a Python 3.11 image based on Debian Bookworm (native SQLite 3.40+ for ChromaDB)
FROM python:3.11-slim-bookworm

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Ensure necessary directories exist
RUN mkdir -p chroma_db rag/documents

# Hugging Face runs containers with user ID 1000 (not root). 
# We must give write permissions to the app directory so ChromaDB and SQLite don't crash.
RUN chmod -R 777 /app

# Set the port for Hugging Face Space health check
ENV PORT=7860
EXPOSE 7860

# Run the application
CMD ["python", "main.py"]
