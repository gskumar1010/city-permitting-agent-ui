LLAMA_STACK_URL := https://my-llama-stack-my-llama-stack.apps.ocp.home.glroland.com
MODEL := meta-llama/Llama-3.3-70B-Instruct
EMBEDDING_MODEL := text-embedding-3-large
VECTORDB_PROVIDER := milvus

OS := $(shell uname -s)

install:
	pip install -r chatbot/requirements.txt
ifeq ($(OS),Darwin)
	pip install -r ingest/requirements.txt.mac
else
	pip install -r ingest/requirements.txt.linux
endif

clean:
	rm -rf target

ingest-data:
	mkdir -p target/data
	cd target/data && docling --from pdf --to json --to md --image-export-mode referenced --ocr --output . --abort-on-error ../../data/c3_repair.pdf

test:
	cd ingest/src && python import.py $(LLAMA_STACK_URL) $(EMBEDDING_MODEL) $(VECTORDB_PROVIDER) ../../target/data/c3_repair.md
