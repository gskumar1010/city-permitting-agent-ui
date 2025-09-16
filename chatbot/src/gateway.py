"""API Utilities

Utility functions related to connecting with the backend services supporting
the chatbot.
"""
import os
import logging
import streamlit as st
from openai import OpenAI
from constants import AGENT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class ResponsesGateway:

    ENV_OPENAI_BASE_URL = "OPENAI_BASE_URL"
    ENV_OPENAI_API_KEY = "OPENAI_API_KEY"
    ENV_OPENAI_MODEL = "OPENAI_MODEL"

    openai_client : OpenAI
    previous_response_id = None
    model = None

    def connect(self):
        """ Connects to the remote service provider. """
        # get the base url
        openai_base_url = None
        if not self.ENV_OPENAI_BASE_URL in os.environ:
            logger.warning("OpenAI Endpoint has not been set.  Using OpenAI directly.")
        else:
            openai_base_url = os.environ[self.ENV_OPENAI_BASE_URL]
            logger.info("OpenAI Compatible Endpoint URL: %s", openai_base_url)

        # get the api key
        if not self.ENV_OPENAI_API_KEY in os.environ:
            msg = "OpenAI API Key is a required environment variable.  'OPENAI_API_KEY' missing."
            logger.error(msg)
            raise ValueError(msg)
        openai_api_key = os.environ[self.ENV_OPENAI_API_KEY]
        logger.info("OpenAI API Key: %s", openai_api_key)

        # create client connection
        logger.info("Initializing OpenAI Client")
        openai_client = OpenAI(base_url = openai_base_url,
                            api_key = openai_api_key)
        logger.info("OpenAI Initialized")

        # get configured model
        if not self.ENV_OPENAI_MODEL in os.environ:
            msg = "OpenAI Model is a required environment variable.  'OPENAI_MODEL' missing."
            logger.error(msg)
            raise ValueError(msg)
        self.model = os.environ[self.ENV_OPENAI_MODEL]
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
