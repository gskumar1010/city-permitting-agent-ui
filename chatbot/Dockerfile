FROM registry.access.redhat.com/ubi9/python-311:9.6-1750969934

# Configuration
ENV LLAMA_STACK_URL "http://localhost:8321"
ENV EMBEDDING_MODEL "sentence-transformers/all-mpnet-base-v2"
ENV OPENAI_BASE_URL = "OPENAI_BASE_URL"
ENV OPENAI_API_KEY = "OPENAI_API_KEY"
ENV OPENAI_MODEL = "OPENAI_MODEL"

# By default, listen on port 8080
EXPOSE 8080/tcp

# Set the working directory in the container
WORKDIR /projects

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any dependencies
RUN pip install -r requirements.txt

# Copy the content of the local src directory to the working directory
COPY ./src/ .

# Specify the command to run on container start
CMD ["streamlit", "run", "./app.py", "--server.port=8080", "--server.address=0.0.0.0"]
