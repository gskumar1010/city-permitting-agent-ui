LLAMA_STACK_URL := https://my-llama-stack-my-llama-stack.apps.ocp.home.glroland.com
MODEL := openai/gpt-4
#MODEL := llama32
#EMBEDDING_MODEL := text-embedding-3-large
EMBEDDING_MODEL := granite-embedding-125m
VECTORDB_PROVIDER := milvus
API_KEY := "nokeyneeded"

OS := $(shell uname -s)

install:
	pip install -r chatbot/requirements.txt
ifeq ($(OS),Darwin)
	pip install -r corvetteforum-mcp/requirements.txt.mac
	pip install -r ingest/requirements.txt.mac
else
	pip install -r corvetteforum-mcp/requirements.txt.linux
	pip install -r ingest/requirements.txt.linux
endif

clean:
	rm -rf target

ingest-data:
	mkdir -p target/data
	cd target/data && docling --from pdf --to json --to md --image-export-mode referenced --ocr --output . --abort-on-error ../../chatbot/src/assets/c3_repair.pdf
	cd ingest/src && python import.py $(LLAMA_STACK_URL) $(EMBEDDING_MODEL) $(VECTORDB_PROVIDER) ../../target/data/c3_repair.md

run-chatbot:
	cd chatbot/src && LLAMA_STACK_URL=$(LLAMA_STACK_URL) API_KEY=$(API_KEY) MODEL=$(MODEL) streamlit run app.py --server.headless true --server.address 0.0.0.0 --server.port 8080

run-corvetteforummcp:
	cd corvetteforum-mcp/src && python app.py

test:
	cd ingest/src && python import.py $(LLAMA_STACK_URL) $(EMBEDDING_MODEL) $(VECTORDB_PROVIDER) ../../target/data/c3_repair.md
