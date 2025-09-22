"""API Utilities

Utility functions related to connecting with the backend services supporting
the chatbot.
"""
import os
import logging
import streamlit as st
from openai import OpenAI
from llama_stack_client import LlamaStackClient
from llama_stack_client.types.shared_params.query_config import QueryConfig
from constants import AGENT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class AIGateway:

    ENV_LLAMA_STACK_URL = "LLAMA_STACK_URL"
    ENV_API_KEY = "API_KEY"
    ENV_MODEL = "MODEL"

    LLS_OPENAI_URL_SUFFIX = "/v1/openai/v1"

    MECHANIC_VECTOR_DB_NAME = "mechanic_vector_db"

    openai_client : OpenAI = None
    llama_stack_client : LlamaStackClient = None
    previous_response_id = None
    model = None

    def connect(self):
        """ Connects to the remote service provider. """
        # get the base url
        if not self.ENV_LLAMA_STACK_URL in os.environ:
            msg = "LLama Stack Endpoint URL has not been set and is a required variable. 'LLAMA_STACK_URL' missing."
            logger.error(msg)
            raise ValueError(msg)
        llama_stack_url = os.environ[self.ENV_LLAMA_STACK_URL]
        logger.info("LLama Stack URL: %s", llama_stack_url)

        # get the api key
        if not self.ENV_API_KEY in os.environ:
            msg = "LLS/OpenAI API Key is a required environment variable.  'API_KEY' missing."
            logger.error(msg)
            raise ValueError(msg)
        api_key = os.environ[self.ENV_API_KEY]
        logger.info("LLS/OpenAI API Key: %s", api_key)

        # Connect to LLama Stack
        logger.info("Connecting to LLama Stack.  URL=%s", llama_stack_url)
        self.llama_stack_client = LlamaStackClient(
            base_url=llama_stack_url,
        )
        logger.info("Successfully connected to LLama Stack.")

        # create client connection
        openai_base_url = llama_stack_url + self.LLS_OPENAI_URL_SUFFIX
        logger.info("Initializing OpenAI Client based on a base url value of = %s", openai_base_url)
        openai_client = OpenAI(base_url = openai_base_url,
                               api_key = api_key)
        logger.info("OpenAI Initialized")

        # get configured model
        if not self.ENV_MODEL in os.environ:
            msg = "OpenAI Model is a required environment variable.  'MODEL' missing."
            logger.error(msg)
            raise ValueError(msg)
        self.model = os.environ[self.ENV_MODEL]
        if len(self.model) == 0:
            msg = "OpenAI Model is empty and required."
            logger.error(msg)
            raise ValueError(msg)
        logger.info("OpenAI Model: %s", self.model)

        self.openai_client = openai_client

    def process_user_chat(self, user_input: str, placeholder) -> str:
        """ Process a chat request.
        
            user_input - user message
            placeholder - streamlit placeholder
            
            Returns: Chat response
        """
        # Log the user chat and systems prompt
        logger.info("System Prompt: %s", AGENT_SYSTEM_PROMPT)
        logger.info("User Input: %s", user_input)

        # Employ OpenAI Responses AI
        response_stream = self.openai_client.responses.create(
            model=self.model,
            instructions=AGENT_SYSTEM_PROMPT,
            input=user_input,
            temperature=0.3,
            max_output_tokens=2048,
            top_p=1,
            store=True,
            previous_response_id=self.previous_response_id,
            stream=True
        )

        # Capture response
        ai_response = ""
        for event in response_stream:
            if hasattr(event, "type") and "text.delta" in event.type:
                ai_response += event.delta
                print(event.delta, end="", flush=True)
                with placeholder.container():
                    st.write(ai_response)
            elif hasattr(event, "type") and "response.completed" in event.type:
                self.previous_response_id = event.response.id

        return ai_response

    def rag_search(self, search_string: str, max_chunks: int = 5):
        """ Search vector store for relevant content.
        """
        logger.info("Performing RAG Search.  Search String=%s. Max Chunks=%s", search_string, max_chunks)
    
        # Retrieve the vector database for the mechanic application
        logger.info("Searching for the mechanic vector database.  DB_NAME=%s", self.MECHANIC_VECTOR_DB_NAME)
        mechanic_vdb = None
        vector_db_list = self.llama_stack_client.vector_dbs.list()
        for vector_db in vector_db_list:
            logger.debug("Vector DB vector_db_name = %s", vector_db.vector_db_name)
            if vector_db.identifier == self.MECHANIC_VECTOR_DB_NAME:
                logger.debug("VDB Match Found!")
                mechanic_vdb = vector_db
                break
        if mechanic_vdb is None:
            msg = "No matching Vector Database for the Mechanic application could be found."
            logger.error(msg + " DBs=%s", vector_db_list)
            raise ValueError(msg)

        # Query documents
        query_config = QueryConfig(max_chunks=max_chunks)
        metadata, content = self.llama_stack_client.tool_runtime.rag_tool.query(
            vector_db_ids=[mechanic_vdb.identifier],
            content=search_string,
            query_config=query_config
        )

        # Parse metadata
        metadata = metadata[1]
        document_ids = metadata["document_ids"]
        logger.info("Matching Content.  #=%s. DocIds=%s", len(document_ids), document_ids)

        # Parse content
        content = content[1]
        results = []
        for result in content:
            text = result.text
            logger.info("Matching Chunk = %s", text)
            results.append(text)

        return results
