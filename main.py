# Import necessary libraries
import streamlit as st

from openai.types.beta.assistant import Assistant

from assistant import PDFChatManager, avalible_tools

from utils import delete_file

from seed import ASSISTANT_SEED_PROMPT

# Initialize the chat pdf assistance instance
pdf_assistant_manager: PDFChatManager = PDFChatManager()

# 01 Create an assistant
pdf_assistant: Assistant = pdf_assistant_manager.create_assistant(
    name="New PDF Assistant", instructions=ASSISTANT_SEED_PROMPT, tools=avalible_tools, file_obj=[]
)

# 02 Create a thread
thread = pdf_assistant_manager.create_thread()

# Initialize session state variables for file management
if "file_id_dict" not in st.session_state:
    st.session_state.file_id_dict = {}

if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

st.set_page_config(page_title="PDF AI",
                   page_icon=":coffee:",
                   layout="wide"  # Add this line to set the layout to wide
                   )


# Create a sidebar for API key configuration and additional features
st.sidebar.header("Manage Your PDFs")

# Debugging: Display the current state of file_id_dict
# st.sidebar.write("Debug - file_id_dict:", st.session_state.file_id_dict)

# Sidebar option for users to upload their own files
uploaded_file = st.sidebar.file_uploader(
    "Upload a file to be given to OpenAI", key="file_uploader")

# Button to upload a user's file and store the file ID
if st.sidebar.button("Give Uploaded PDF to Assistant"):

    if uploaded_file and uploaded_file.name not in st.session_state.file_id_dict:
        with open(f"{uploaded_file.name}", "wb") as f:
            f.write(uploaded_file.getbuffer())
        additional_file_id = pdf_assistant_manager.create_file(
            f"{uploaded_file.name}")
        st.session_state.file_id_dict[uploaded_file.name] = additional_file_id

        # Store its ID in session state
        st.session_state.thread_id = thread.id

if st.session_state.file_id_dict:
    st.sidebar.write("Uploaded File IDs:")
    for filename, file_id in st.session_state.file_id_dict.items():
        st.sidebar.write(f"{filename}: {file_id}")

    # Associate files with the assistant
    assistant_file = pdf_assistant_manager.modifyAssistant(
        file_obj=list(st.session_state.file_id_dict.values()),
        assistant_id=pdf_assistant.id,
        new_instructions=ASSISTANT_SEED_PROMPT,
        tools=avalible_tools
    )
else:
    st.sidebar.warning("Assistant is running without PDF Files.")

if st.sidebar.button("Remove All PDFs"):
    # Create a copy of the keys to iterate over
    filenames = list(st.session_state.file_id_dict.keys())

    for filename in filenames:
        file_id = st.session_state.file_id_dict[filename]

        # Delete All Files From Open AI Platform
        rm_assistant_file = pdf_assistant_manager.delAssistantFile(
            file_id=file_id)
        del_file = pdf_assistant_manager.deleteFile(file_id=file_id)
        delete_file(filename)

        # Remove the file ID from the session state after deletion
        if rm_assistant_file['status'] == 'success' or del_file['status'] == 'success':
            del st.session_state.file_id_dict[filename]

    # Refresh the sidebar or interface to reflect the changes
    st.experimental_rerun()


def process_message_with_citations(message):
    """Extract content and annotations from the message and format citations as footnotes."""
    message_content = message.content[0].text
    annotations = message_content.annotations if hasattr(
        message_content, 'annotations') else []
    citations = []

    # Iterate over the annotations and add footnotes
    for index, annotation in enumerate(annotations):
        # Replace the text with a footnote
        message_content.value = message_content.value.replace(
            annotation.text, f' [{index + 1}]')

        # Gather citations based on annotation attributes
        if (file_citation := getattr(annotation, 'file_citation', None)):
            # Retrieve the cited file details (dummy response here since we can't call OpenAI)
            # This should be replaced with actual file retrieval
            cited_file = {'filename': 'cited_document.pdf'}
            citations.append(
                f'[{index + 1}] {file_citation.quote} from {cited_file["filename"]}')
        elif (file_path := getattr(annotation, 'file_path', None)):
            # Placeholder for file download citation
            # This should be replaced with actual file retrieval
            cited_file = {'filename': 'downloaded_document.pdf'}
            # The download link should be replaced with the actual download path
            citations.append(
                f'[{index + 1}] Click [here](#) to download {cited_file["filename"]}')

    # Add footnotes to the end of the message content
    full_response = message_content.value + '\n\n' + '\n'.join(citations)
    return full_response


# Main chat interface setup
st.title("AI Chat With PDFs")
st.markdown("#### A Digital Brain for your Docs!")

# Initialize the model and messages list if not already in session state
if "openai_model" not in st.session_state:
    st.session_state.openai_model = "gpt-4-1106-preview"
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display existing messages in the chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input for the user
if prompt := st.chat_input("What is up?"):
    # Add user message to the state and display it
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Add the user's message to the existing thread
    pdf_assistant_manager.add_message_to_thread(
        role="user", content=prompt
    )

    # Create a run with additional instructions
    run = pdf_assistant_manager.run_assistant(
        instructions=ASSISTANT_SEED_PROMPT,
    )

    # Retrieve messages added by the assistant
    messages = pdf_assistant_manager.wait_for_completion(
        run=run, thread=thread)

    # Process and display assistant messages
    assistant_messages_for_run = [
        message for message in messages
        if message.run_id == run.id and message.role == "assistant"
    ]
    for message in assistant_messages_for_run:
        full_response = process_message_with_citations(message)
        st.session_state.messages.append(
            {"role": "assistant", "content": full_response})
        with st.chat_message("assistant"):
            st.markdown(full_response, unsafe_allow_html=True)
