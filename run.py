import streamlit as st
import time
import os
from assistant import PDFChatManager, avalible_tools
from utils import pretty_print
from seed import ASSISTANT_SEED_PROMPT
import tempfile
from openai.types.beta.threads import ThreadMessage
from openai.types.beta.thread import Thread
from openai.types.beta.assistant import Assistant

# Initialize the chat pdf assistance instance
pdf_assistant_manager: PDFChatManager = PDFChatManager()


# 01 Create an assistant
pdf_assistant: Assistant = pdf_assistant_manager.create_assistant(
    name="New PDF Assistant", instructions=ASSISTANT_SEED_PROMPT, tools=avalible_tools, file_obj=[]
)

# 02 Create a thread
thread = pdf_assistant_manager.create_thread()

# 06 return response to be displayed
# return messages, pdf_assistant_manager, run, thread, file_obj, pdf_assistant

# Set up the Streamlit page with a title and icon
st.set_page_config(page_title="PDF AI",
                   page_icon=":coffee:",
                   layout="wide"  # Add this line to set the layout to wide
                   )

st.title("AI Chat With PDFs")
st.markdown("#### A Digital Brain for your Docs!")

st.sidebar.header("Manage PDFs")

# Initialize chat history
if "chat" not in st.session_state:
    st.session_state.chat = []

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize session state for the uploaded file ID and path
if 'uploaded_file_id' not in st.session_state:
    st.session_state['uploaded_file_id'] = None
if 'uploaded_file_path' not in st.session_state:
    st.session_state['uploaded_file_path'] = None

# File uploader in the sidebar
uploaded_file = st.sidebar.file_uploader(
    "Choose a PDF file", type=['pdf'], key="file_uploader")

# Check if a new file is uploaded and update session state
if uploaded_file is not None and st.session_state['uploaded_file_id'] is None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", dir="data/") as tmp_file:
        tmp_file.write(uploaded_file.getbuffer())
        tmp_file_path = tmp_file.name

    file_obj_id = pdf_assistant_manager.create_file(file_path=tmp_file_path)
    st.session_state['uploaded_file_id'] = file_obj_id
    st.session_state['uploaded_file_path'] = tmp_file_path

    pdf_assistant_manager.modifyAssistant(
        file_obj=[file_obj_id],
        assistant_id=pdf_assistant.id,
        new_instructions=ASSISTANT_SEED_PROMPT,
        tools=avalible_tools)


# Display uploaded file info and provide an option to remove it
if st.session_state['uploaded_file_id'] is not None:
    st.sidebar.write(f"Uploaded PDF: {os.path.basename(
        st.session_state['uploaded_file_path'])}")

    if st.sidebar.button("Remove PDF", key="remove_pdf"):
        pdf_assistant_manager.delAssistantFile(
            file_id=st.session_state['uploaded_file_id'])

        if os.path.exists(st.session_state['uploaded_file_path']):
            os.remove(st.session_state['uploaded_file_path'])

        st.session_state['uploaded_file_id'] = None
        st.session_state['uploaded_file_path'] = None

        st.sidebar.info("PDF and temporary file removed successfully.")
        st.experimental_rerun()


# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What is up?"):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 03 Add a message to the thread
    pdf_assistant_manager.add_message_to_thread(role="user", content=prompt)

    # 04 Run the assistant
    run = pdf_assistant_manager.run_assistant(instructions="")

    # 05 Wait for the assistant to complete
    messages = pdf_assistant_manager.wait_for_completion(
        run=run, thread=thread)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        full_response += (messages.data[0].content[0].text.value or "")
        # Simulate stream of response with milliseconds delay
        # for chunk in full_response.split():
        #     full_response += chunk + " "
        #     time.sleep(0.05)
        #     # Add a blinking cursor to simulate typing
        #     message_placeholder.markdown(full_response)

        message_placeholder.markdown(full_response)
    st.session_state.messages.append(
        {"role": "assistant", "content": full_response})

# Display chat chat from history on app rerun
for message in st.session_state.chat:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
