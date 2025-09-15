""" CLI for loading content into vector database. """
import os
import sys
import logging
import click
from llama_stack_client import LlamaStackClient, LlamaStackClient, RAGDocument
from langchain_text_splitters import MarkdownHeaderTextSplitter

logger = logging.getLogger(__name__)

MECHANIC_VECTOR_DB_NAME = "mechanic_vector_db"

class ErrorCodes:
    SUCCESS = 0
    ILLEGAL_ARGS = 1
    FILE_NOT_FOUND = 2
    LLS_CONFIG_ERROR = 3

class ColorOutputFormatter(logging.Formatter):
    """ Add colors to stdout logging output to simplify text.  Thank you to:
        https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
    """

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format_str = '%(name)-13s: %(message)s'

    FORMATS = {
        logging.DEBUG: grey + format_str + reset,
        logging.INFO: grey + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: bold_red + format_str + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

@click.command()
@click.argument('llama_stack_url')
@click.argument('embedding_model_name')
@click.argument('vdb_provider')
@click.argument('input_file')
def cli(llama_stack_url: str, embedding_model_name: str, vdb_provider:str, input_file: str):
    """ CLI for importing mechanic content into vector store.
    
        llama_stack_url - LLama Stack URL
        embedding_model_name - Embedding Model Name
        input_file - Input file to ingest
    """
    # Default to not set
    logging.getLogger().setLevel(logging.NOTSET)

    # Log info and higher to the console
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(ColorOutputFormatter())
    logging.getLogger().addHandler(console)

    # Validate arguments
    if llama_stack_url is None or len(llama_stack_url) == 0:
        logger.fatal("LLama Stack URL is a required parameter and cannot be empty.")
        sys.exit(ErrorCodes.ILLEGAL_ARGS)
    if embedding_model_name is None or len(embedding_model_name) == 0:
        logger.fatal("Embedding Model is a required parameter and cannot be empty.")
        sys.exit(ErrorCodes.ILLEGAL_ARGS)
    if vdb_provider is None or len(vdb_provider) == 0:
        logger.fatal("VectorDB Provider is required and cannot be empty.")
        sys.exit(ErrorCodes.ILLEGAL_ARGS)
    if input_file is None or len(input_file) == 0:
        logger.fatal("Input File is a required paramter and cannot be empty.")
        sys.exit(ErrorCodes.ILLEGAL_ARGS)

    # Ensure the input file exists
    if not os.path.exists(input_file):
        logger.fatal("Input File does not exist!  Filename = %s", input_file)
        sys.exit(ErrorCodes.FILE_NOT_FOUND)
    if not os.path.isfile(input_file):
        logger.fatal("Input File is a directory.  This is currently unsupported functionality.  Filename = %s", input_file)
        sys.exit(ErrorCodes.FILE_NOT_FOUND)

    # Connect to LLama Stack
    logger.info("Connecting to LLama Stack.  URL=%s", llama_stack_url)
    llama_stack_client = LlamaStackClient(
        base_url=llama_stack_url,
    )
    logger.info("Successfully connected to LLama Stack.")

    # Load the input file
    file_contents = ""
    with open(input_file, "r") as f:
        file_contents = f.read()
    if len(file_contents) == 0:
        logger.fatal("Input file is empty.  Cannot load.")
        sys.exit(ErrorCodes.FILE_NOT_FOUND)
    logger.info("Loaded input file.  Size of File=%s", len(file_contents))

    # Split document into chunks
    logger.info("Chunking file...")
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    text_chunks = markdown_splitter.split_text(file_contents)
    logger.info("File Chunked.  # of Chunks = %s", len(text_chunks))

    # Create a list of the registred Vector Databases
    logger.info("Searching list of Vector DBs for pre-existing repositories.")
    for vector_db in llama_stack_client.vector_dbs.list():
        logger.debug("Vector DB vector_db_name = %s", vector_db.vector_db_name)
        if vector_db.vector_db_name == MECHANIC_VECTOR_DB_NAME:
            logger.warning("Preexisting instance of the vector database.  Deleting....  vector_db_id=%s", vector_db.identifier)
            llama_stack_client.vector_dbs.unregister(vector_db.identifier)

    # Register a vector database
    logger.info("Creating new Vector Database for content.  ID/Name=%s", MECHANIC_VECTOR_DB_NAME)
    new_vdb = llama_stack_client.vector_dbs.register(
        vector_db_id=MECHANIC_VECTOR_DB_NAME,
        embedding_model=embedding_model_name,
        embedding_dimension=384,
        provider_id=vdb_provider,
    )
    logger.info("Vector Database Created.  New VDB ID = %s", new_vdb.identifier)

    # Create chunks into Vector Database
    logger.info("Creating LLama Stack RAG Documents...")
    documents = [
        RAGDocument(
            document_id=f"num-{i}",
            content=f"{chunk}",
            mime_type="text/plain",
            metadata={},
        )
        for i, chunk in enumerate(text_chunks)
    ]

    # Chunk the chunks so the LLama Stack API doesn't time out
    def chunks(lst, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    # Import content
    logger.info("Inserting RAG Documents into Vector Store...")
    for chunk in chunks(documents, 10):
        logger.info("Inserting a chunk of chunks...")
        llama_stack_client.tool_runtime.rag_tool.insert(
            documents=chunk,
            vector_db_id=new_vdb.identifier,
            chunk_size_in_tokens=2048,
        )

    # Successfully imported
    logger.info("Successfully imported content.")
    sys.exit(ErrorCodes.SUCCESS)


if __name__ == '__main__':
    cli()
