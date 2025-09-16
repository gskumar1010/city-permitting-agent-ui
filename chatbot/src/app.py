""" Mechanic Chatbot

Digital expert in fixing old corvettes
"""
import logging
import base64
import streamlit as st
from constants import SessionStateVariables
from constants import AppUserInterfaceElements
from constants import CannedGreetings
from constants import MessageAttributes
from gateway import ResponsesGateway

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO,
    handlers=[
        # no need from a docker container - logging.FileHandler("mechanic-chatbot.log"),
        logging.StreamHandler()
    ])

# Prepare engine bay photo
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()
bin_str = get_base64_of_bin_file('assets/engine_bay.jpeg')
sidebar_bg_css = f"""
<style>
.st-key-chatbot {{
    background-image: url("data:image/png;base64,{bin_str}");
    //background-image: linear-gradient(to right, rgba(255,255,255, 0.3) 0 100%), url("data:image/png;base64,{bin_str}");
    background-size: cover;
    background-attachment: local;
    //background-position: center center;
}}
</style>
"""
st.markdown(sidebar_bg_css, unsafe_allow_html=True)

# Initialize Streamlit State
if SessionStateVariables.MESSAGES not in st.session_state:
    logger.info("Initializing OpenAI Client")
    gateway = ResponsesGateway()
    gateway.connect()
    st.session_state[SessionStateVariables.GATEWAY] = gateway
    logger.info("Client Initialized")

    logger.info("Clearing message history.")
    st.session_state[SessionStateVariables.MESSAGES] = []

# Rehydrate global variables from session state
gateway = st.session_state[SessionStateVariables.GATEWAY]

# Initialize High Level Page Structure
st.set_page_config(page_title=AppUserInterfaceElements.TITLE,
                   page_icon=AppUserInterfaceElements.TAB_ICON,
                   layout="wide")
st.markdown("""
    <style>
        .stAppHeader {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)
col1, col2 = st.columns(2, vertical_alignment="center")
st.markdown("""
    <style>
        div[data-testid="column"] {
            width: fit-content !important;
            flex: unset;
        }
        div[data-testid="column"] * {
            width: fit-content !important;
        }
    </style>
    """, unsafe_allow_html=True)
with col1:
    st.image("assets/side_view_car.jpeg", width=100)
with col2:
    st.markdown(""" # My Classic Corvette Garage """)

# Initialize Chat Box
messages = st.container(height=400, key="chatbot")
messages.chat_message(MessageAttributes.ASSISTANT).write(CannedGreetings.INTRO)
for msg in st.session_state.messages:
    messages.chat_message(msg[MessageAttributes.ROLE]).write(msg[MessageAttributes.CONTENT])

# Gather and log user prompt
if user_input := st.chat_input():
    logger.info ("User Input: %s", user_input)
    messages.chat_message("user").write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    logger.info ("st.session_state.messages - %s", st.session_state.messages)

    # Process chat
    ai_response = None
    with messages.chat_message(MessageAttributes.ASSISTANT):
        placeholder = st.empty()
        ai_response = gateway.process_user_chat(user_input, placeholder)
    logger.info ("AI Response Message: %s", ai_response)

    # Append AI Response to history
    st.session_state.messages.append(
        {
            MessageAttributes.ROLE: MessageAttributes.ASSISTANT,
            MessageAttributes.CONTENT: ai_response
        }
    )
