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
from ai_gateway import AIGateway

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

# Initialize Streamlit State
if SessionStateVariables.MESSAGES not in st.session_state:
    logger.info("Initializing OpenAI Client")
    gateway = AIGateway()
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

# Page setup
css = f"""
<style>
.stMain {{
    background-image: url("data:image/png;base64,{bin_str}");
    background-size: cover;
    }}

.st-key-chatbot {{
    background-color: black;
    //background-image: linear-gradient(to right, rgba(255,255,255, 0.3) 0 100%), url("data:image/png;base64,{bin_str}");
    background-size: cover;
    background-attachment: local;
    //background-position: center center;
}}

.stAppHeader {{visibility: hidden;}}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

@st.dialog("Service Manual", width="large")
def display_service_manual():
    st.pdf("assets/c3_repair.pdf")

# Setup header
col1, col2, col3 = st.columns([0.1, 0.2, 0.7], vertical_alignment="center")
with col1:
    st.image("assets/side_view_car.jpeg", width=100)
with col2:
    if st.button("Service Manual"):
        display_service_manual()
with col3:
    st.markdown(""" # My&nbsp;Classic&nbsp;Corvette&nbsp;Garage """)

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

    # Search VDB for relevant content
    matching_content = gateway.rag_search(user_input)
    expanded_user_input = ""
    if matching_content is not None and len(matching_content) > 0:
        expanded_user_input += "Context:\n"
        for c in matching_content:
            expanded_user_input += c + "\n"
        expanded_user_input += "\nQuestion:"
    expanded_user_input += user_input

    # Process chat
    ai_response = None
    with messages.chat_message(MessageAttributes.ASSISTANT):
        placeholder = st.empty()
        ai_response = gateway.process_user_chat(expanded_user_input, placeholder)
    logger.info ("AI Response Message: %s", ai_response)

    # Append AI Response to history
    st.session_state.messages.append(
        {
            MessageAttributes.ROLE: MessageAttributes.ASSISTANT,
            MessageAttributes.CONTENT: ai_response
        }
    )
