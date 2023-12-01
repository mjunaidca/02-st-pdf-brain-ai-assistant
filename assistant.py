# A Class to Manage All Open API Assistant Calls and Functions
from openai.types.beta.threads import Run, ThreadMessage
from openai.types.beta.thread import Thread
from openai.types.beta.assistant_create_params import Tool
from openai.types.beta.assistant_deleted import AssistantDeleted
from openai.types.beta.assistant import Assistant
from openai.types.file_deleted import FileDeleted
from openai.types import FileDeleted
from openai.types.beta.assistant_deleted import AssistantDeleted
from openai.types.beta.assistants import FileDeleteResponse, AssistantFile
from openai.types.beta.assistant_create_params import ToolAssistantToolsRetrieval

import time
import json

from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
from typing import Callable, Literal


_: bool = load_dotenv(find_dotenv())  # read local .env file

client: OpenAI = OpenAI()

available_functions: dict[str, Callable] = {}

# Define available tools as a list of Tool objects
avalible_tools = [{"type": "retrieval"}]


class PDFChatManager:
    def __init__(self, model: str = "gpt-3.5-turbo-1106"):
        self.client = OpenAI()
        self.model = model
        self.assistant: Assistant | None = None
        self.thread: Thread | None = None
        self.run: Run | None = None

    def list_files(self, purpose: str = 'assistants') -> list:
        """Retrieve a list of files with the specified purpose."""
        files = client.files.list(purpose=purpose)
        file_list = files.model_dump()
        return file_list['data'] if 'data' in file_list else []

    def find_file_id_by_name(self, filename: str, purpose: str = 'assistants') -> str | None:
        """Check if the file exists in the OpenAI account and return its ID."""
        files = self.list_files(purpose=purpose)
        for file in files:
            print("Is this a Duplicate File?", file['filename'] == filename)
            if file['filename'] == filename:
                print("file['id']", file['id'])
                return file['id']
        return None

    def create_file(self, file_path: str, purpose: Literal['fine-tune', 'assistants'] = 'assistants') -> str:
        """Create or find a file in OpenAI. 
        https://platform.openai.com/docs/api-reference/files/list
        If file is already uploaded with same name then 
        we will use it rather than creating a new one. """

        existing_file_id = self.find_file_id_by_name(file_path, purpose)

        print("found existing file...", existing_file_id)

        if existing_file_id:
            self.file_id = existing_file_id
            return existing_file_id
        else:
            with open(file_path, "rb") as file:
                file_obj = self.client.files.create(file=file, purpose=purpose)
                self.file_id = file_obj.id
                return file_obj.id

    def list_assistants(self) -> list:
        """Retrieve a list of assistants."""
        assistants_list = self.client.beta.assistants.list()
        assistants = assistants_list.model_dump()
        return assistants['data'] if 'data' in assistants else []

    def modifyAssistant(self, assistant_id: str, new_instructions: str, tools: list, file_obj: list[str]) -> Assistant:
        """Update an existing assistant."""
        print("Updating edisting assistant...")
        self.assistant = self.client.beta.assistants.update(
            assistant_id=assistant_id,
            instructions=new_instructions,
            tools=tools,
            model=self.model,
            file_ids=file_obj
        )
        return self.assistant

    def find_and_set_assistant_by_name(self, name: str, instructions: str, tools: list[Tool], file_obj: list[str]) -> None:
        """Find an assistant by name and set it if found."""
        assistants = self.list_assistants()
        print("Retrieved assistants list...")
        if self.assistant is None:  # Check if assistant is not already set
            for assistant in assistants:
                if assistant['name'] == name:
                    print("Found assistant...",  assistant['name'] == name)
                    print("Existing Assitant ID", assistant['id'])
                    # self.assistant = assistant
                    self.modifyAssistant(
                        assistant_id=assistant['id'],
                        new_instructions=instructions,
                        tools=tools,
                        file_obj=file_obj
                    )
                    break

    def create_assistant(self, name: str, instructions: str, tools: list, file_obj: list[str], model: str = "gpt-3.5-turbo-1106") -> Assistant:
        """Create or find an assistant."""
        self.find_and_set_assistant_by_name(
            name=name,
            instructions=instructions,
            tools=tools,
            file_obj=file_obj)
        if self.assistant is None:  # Check if assistant is not already set
            print("Creating new assistant...")
            self.assistant = self.client.beta.assistants.create(
                name=name,
                instructions=instructions,
                tools=tools,
                model=model,
                file_ids=file_obj
            )
        return self.assistant  # Return the assistant object

    def create_thread(self) -> Thread:
        self.thread = self.client.beta.threads.create()
        return self.thread

    def add_message_to_thread(self, role: Literal['user'], content: str, file_ids: list = []) -> None:
        if self.thread is None:
            raise ValueError("Thread is not set!")

        self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role=role,
            content=content,
            file_ids=file_ids
        )

    def run_assistant(self, instructions: str) -> Run:
        if self.assistant is None:
            raise ValueError(
                "Assistant is not set. Cannot run assistant without an assistant.")

        if self.thread is None:
            raise ValueError(
                "Thread is not set!")

        self.run = self.client.beta.threads.runs.create(
            thread_id=self.thread.id,
            assistant_id=self.assistant.id,  # Now safe to access id
            instructions=instructions
        )
        return self.run

    def wait_for_completion(self, run: Run, thread: Thread):

        if self.run is None:
            raise ValueError("Run is not set!")

        while run.status in ["in_progress", "queued"]:
            run_status = self.client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=self.run.id
            )
            print(f"Run is {run.status} ...")
            time.sleep(3)  # Wait for 3 seconds before checking again

            if run_status.status == 'completed':
                processed_response = self.process_messages()
                return processed_response
                # break
            elif run_status.status == 'requires_action' and run_status.required_action is not None:
                print("Function Calling ...")
                self.call_required_functions(
                    run_status.required_action.submit_tool_outputs.model_dump())
            elif run.status == "failed":
                print("Run failed.")
                break
            else:
                print(f"Waiting for the Assistant to process...: {run.status}")

    def process_messages(self):
        messages = self.client.beta.threads.messages.list(
            thread_id=self.thread.id)
        return messages

    def call_required_functions(self, required_actions):
        tool_outputs = []

        for action in required_actions["tool_calls"]:
            function_name = action['function']['name']
            arguments = json.loads(action['function']['arguments'])
            print('function_name', function_name)
            print('function_arguments', arguments)

            if function_name in available_functions:
                function_to_call = available_functions[function_name]
                output = function_to_call(**arguments)
                tool_outputs.append({
                    "tool_call_id": action['id'],
                    "output": output,
                })

            else:
                raise ValueError(f"Unknown function: {function_name}")

        print("Submitting outputs back to the Assistant...")
        self.client.beta.threads.runs.submit_tool_outputs(
            thread_id=self.thread.id,
            run_id=self.run.id,
            tool_outputs=tool_outputs
        )

    # List, Modify And Destroy Files & Assistants

    def deleteFile(self, file_id: str) -> dict[str, FileDeleted | str]:
        response: dict[str, FileDeleted | str] = {}
        try:
            response['data'] = self.client.files.delete(file_id)
            response['status'] = 'success'
            print("Deleted File", response['data'])

        except Exception as e:
            # Handle other potential exceptions
            response['status'] = 'error'
            response['error'] = str(e)

        return response

    def retriveAssistantFile(self) -> AssistantFile:
        if self.assistant is None:
            raise ValueError(
                "Assistant is not set. Cannot run assistant without an assistant.")
        return client.beta.assistants.files.retrieve(
            assistant_id=self.assistant.id,
            file_id=self.file_id
        )

    def delAssistantFile(self, file_id: str) -> dict[str, FileDeleteResponse | str]:
        if self.assistant is None:
            raise ValueError(
                "Assistant is not set. Cannot run assistant without an assistant.")

        response: dict[str, FileDeleteResponse | str] = {}
        try:
            response['data'] = client.beta.assistants.files.delete(
                assistant_id=self.assistant.id,
                file_id=file_id
            )
            print("Deleted Assistant File", response['data'])
            response['status'] = 'success'
        except Exception as e:
            # Handle other potential exceptions
            response['status'] = 'error'
            response['error'] = str(e)

        return response

    def deleteAssistant(self) -> AssistantDeleted:
        if self.assistant is None:
            raise ValueError(
                "Assistant is not set. Cannot run assistant without an assistant.")

        return self.client.beta.assistants.delete(self.assistant.id)
