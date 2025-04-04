# Additions needed:
# 1. Upload file to session doesn't work - throws an error that immediately disappears.
# 2. Need to get chat interaction updated to Responses API - most things should be the same otherwise.

import streamlit as st
from pathlib import Path
import json

class HotDawg:

    def __init__(self, client):
        """
        Initializes HotDawg with the given AI client and settings. Also initializes necessary session state keys for this class

        Args:
            client: The AI client (OpenAI, etc.) that handles chat and function calls.
            system_message: Default system message to provide context to the assistant.
            model (str): The AI model identifier to be used for generating responses.
        """

        self.client = client # currently OpenAI client, but could pass a different client from app.py
        
        # Offer UI dropdown for selecting a model and set model based on user selection
        self.model = "o3-mini" # can set model needed - will set default and allow user to pick others
        self.models = ["ft:gpt-4o-2024-08-06:affinity-openai:hotdocsai-v3-2025-03-31:BHBWF5Q4:ckpt-step-72","o3-mini", "o1"]
        st.session_state.model_selected = st.session_state.get('model_selected', None)

        self.vector_stores = ["vs_67a56bff53248191a727cac5b0494749"]
        st.session_state.vector_store_selected = st.session_state.get('vector_store_selected', None)
        # Add vs files to session state so they can be retrieved when vs selected
        st.session_state.vector_store_files = st.session_state.get('vector_store_files', [])

        # Add tracker for local files for edit_file use
        st.session_state.session_files = st.session_state.get('session_files', [])

        st.session_state.modality = st.session_state.get('modality', None)
        self.modality = st.session_state.modality

        st.session_state.modality_change = st.session_state.get('modality_change', False)

        self.new_message = False
        self.text_response = ""

        # Define system message
        self.system_message = """
Document Automation Agent: You assist users with questions or requests involving HotDocs component files by extracting parts of a file using the file_search tool and making edits using the edit_file function when necessary.

File Handling: You can locate specific logic or components within uploaded files semantically using the msearch tool. Once identified, you can modify the relevant sections using the edit_file function based on user requests.

Sample Components File: The sample components file is a real document automation file that uses real variables and logic. You can use it as a guide for understanding the structure and logic of components files. You will refer to this file when creating or editing sections of components files in response to user requests.

Citations: You will provide citations for any extracted information in the specified format, ensuring clarity and traceability of the information provided.

Reasoning: You use reasoning to complete the user's request, first describing the request to yourself, then breaking down the request into small problem-solving steps, writing out your reasoning and answers to each of the steps you take to complete the request, and finally writing a final answer or output for the user that completes their request. In a run, this may involve multiple message completions (e.g. one file_search tool call to retrieve the appropriate section(s) of the component file, one chat completion to allow yourself to reason and find an answer, one tool use to submit the answer to your edit_file tool, and then a final chat completion to tell the user what you did to complete their request).\n\nUser Clarification: Whenever you feel uncertain about a request, cannot locate the relevant sections of the file that the user wants to edit, or are unsure how to proceed with a request, you should ask the user for clarification in simple, direct ways that will help you understand the request or the problem they would like you to solve.

Final Guidelines: Take a deep breath and remember to reason through your tasks and ask the user whenever you aren't sure what to do next.
"""

        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "system", "content": self.system_message}]
        # Add system message to messages list, initialize messages in state if it doesn't exist.

        # Define available tools for interaction

        self.tools = [
            {
                "type": "file_search",
                "vector_store_ids": [st.session_state.vector_store_selected],
                "max_num_results": 20
            }
        ]
            # Remove the edit_file function until able to hold files in memory
#         {
#                "type": "function",
#                "name": "edit_file",
#                "description": "Edit a chunk or chunks of a file and return pairs of original and edited chunk(s) as your arguments to have them written to the cmp file",
#                "strict": True,
#                "parameters": {
#                    "type": "object",
#                    "required": [
#                    "chunks"
#                    ],
#                   "properties": {
#                    "chunks": {
#                        "type": "array",
#                        "description": "List of chunk objects for find-and-replace editing of the file",
#                        "items": {
#                        "type": "object",
#                        "properties": {
#                            "original": {
#                            "type": "string",
#                            "description": "Text originally retrieved"
#                            },
#                            "edited": {
#                            "type": "string",
#                            "description": "Edited version of the original text"
#                            }
#                        },
#                        "required": [
#                            "original",
#                            "edited"
#                        ],
#                        "additionalProperties": False
#                        }
#                    }
#                    },
#                    "additionalProperties": False
#
#                }
#            }

    def setup_ui(self):
        """Setup the user interface components for interaction."""
        st.title(":hotdog: HotDawg Test Environment")
        st.sidebar.title(":material/mic: Input Modality :material/chat:")
        st.write("*Model defaults to fine-tuned GPT. A chatbox or audio input will appear once you choose an input on the left.*")

        new_modality = st.sidebar.selectbox(
            "Input Modality", ("Text", "Speech"), index=None, placeholder="Choose input mode", label_visibility="collapsed", key="modality"
        )
        
        if new_modality != self.modality:
            st.session_state["modality_change"] = True
            self.modality = new_modality
        
        # Offer choice of AI Models
        st.sidebar.title(":material/smart_toy: AI Models")
        model_selection = st.sidebar.selectbox(label='Pick an AI model', options=self.models, index=0, label_visibility='collapsed')
        st.session_state.model_selection = model_selection


        # Place vector store region in sidebar below input type
        upload_widget = st.sidebar

        # Vector Stores
        upload_widget.title(':material/database: Vector Stores')
        vs_container = upload_widget.container()
        vs_selected = vs_container.selectbox(label=':material/left_click: Choose vector store', index=0, options=self.vector_stores)
        if vs_selected != st.session_state.vector_store_selected:
            st.spinner("Retrieving vector store files list...")
            st.session_state.vector_store_selected = vs_selected
            vs_contents_response = self.client.vector_stores.files.list(vector_store_id=st.session_state.vector_store_selected)
            
            # Create new list of file id and file name tuples
            st.session_state.vector_store_files = []
            for file in vs_contents_response.data:
                file_id = file.id
                file_name_response = self.client.files.retrieve(file_id=file_id)
                file_name = file_name_response.filename
                st.session_state.vector_store_files.append((file_name, file_id))

        # Allow user to delete files from vs
        vs_files_selected = vs_container.multiselect(label=":material/folder_open: Vector Store Contents", options=st.session_state.vector_store_files) # original: st.session_state.file_ids
        if vs_files_selected:
            print(vs_files_selected) # debug
            vs_container.write('File(s) selected. See options below:')
            delete_files = vs_container.button(':material/delete: Delete file(s)')
            
            selected_file_ids = {filename: file_id for filename, file_id in st.session_state.vector_store_files}

            if delete_files:
                for file in vs_files_selected:
                    print(file) # debug
                    print(selected_file_ids)
                    filename = file[0] # alternatively, name, _ = file
                    file_id = selected_file_ids[filename]

                    print(filename) #debug
                    print(file_id) #debug
                    st.spinner("Deleting file(s) from vector store...")
                    vs_delete_response = self.client.vector_stores.files.delete(file_id=file_id, vector_store_id=st.session_state.vector_store_selected)
                    files_delete_response = self.client.files.delete(file_id=file_id)
                    if vs_delete_response and files_delete_response:
                        st.success("File(s) successfully deleted!")
                        
                        # Rerun logic to populate the vector store list properly
                        st.spinner("Retrieving updated vector store file list to display...")
                        vs_contents_response = self.client.vector_stores.files.list(vector_store_id=st.session_state.vector_store_selected)
                        
                        # Create new list of file id and file name tuples
                        st.session_state.vector_store_files = []
                        for file in vs_contents_response.data:
                            file_id = file.id
                            file_name_response = self.client.files.retrieve(file_id=file_id)
                            file_name = file_name_response.filename
                            st.session_state.vector_store_files.append((file_name, file_id))

                        st.success("Vector Store Contents Successfully Updated!")

        # Allow user to work with local files, or use uploader to add file to vector store
        upload_widget.title(':material/folder: Your Files')
        uploaded_files = upload_widget.file_uploader(
            label="**Add file(s) to vector store or your session for AI edits**", accept_multiple_files=True, label_visibility="visible"
        )
        button1, button2 = upload_widget.columns([1,1])
        with button1:
            upload_local_files = st.button(label=":material/attach_file: Set Edit File Target (OFF)")
        with button2:
            upload_vs_files = st.button(':material/upload_file: Upload file(s) to Vector Store')
        if upload_vs_files:
            self.upload_files_to_vector_store(uploaded_files=uploaded_files)
        if upload_local_files:
            self.upload_files_to_local_session(uploaded_files=uploaded_files)



    def upload_files_to_vector_store(self, uploaded_files):
        if len(uploaded_files) > 0:
            st.spinner("Uploading file(s) to vector store...")
            for file in uploaded_files:
                vs_upload_response = self.client.vector_stores.files.upload_and_poll(
                    vector_store_id=st.session_state.vector_store_selected,
                    file=file
                )
                if vs_upload_response:
                    st.success("New file added successfully to vector store!")
                    
                    # Rerun logic to populate the vector store list properly
                    st.spinner("Retrieving updated vector store file list to display...")
                    vs_contents_response = self.client.vector_stores.files.list(vector_store_id=st.session_state.vector_store_selected)
                    
                    # Create new list of file id and file name tuples
                    st.session_state.vector_store_files = []
                    for file in vs_contents_response.data:
                        file_id = file.id
                        file_name_response = self.client.files.retrieve(file_id=file_id)
                        file_name = file_name_response.filename
                        st.session_state.vector_store_files.append((file_name, file_id))

                    st.success("Vector Store Contents Successfully Updated!")

        else:
            st.sidebar.error("No files selected - add files and try uploading again")

    def upload_files_to_local_session(self, uploaded_files):
        if len(uploaded_files) > 0:
            st.spinner("Uploading file(s) to this session...")
            try:
                num_session_files = len(st.session_state.session_files)
                for file in uploaded_files:
                    with open(file, 'r', encoding='utf-8') as f:
                        st.session_state.session_files.append(f.read())
                new_num_session_files = len(st.session_state.session_files)
                if new_num_session_files > num_session_files:
                    st.success("File(s) successfully added to session!")
            except Exception as e:
                st.error(f"Error in Local Files: {e}")
                print(f"Error in Local Files: {e}")

        else:
            st.sidebar.error("No files selected - add files and try uploading again")

    def handle_input(self):
        """Handle user input based on selected modality (Text or Speech)."""
        if st.session_state["modality"] == "Text":
            self.handle_text_input()
        elif st.session_state["modality"] == "Speech":
            self.handle_speech_input()

    def handle_text_input(self):
        """Process text input from the user."""
        text_input = st.chat_input("Type your message", disabled=(self.modality != "Text"))
        if text_input and not self.new_message:
            st.session_state.messages.append({"role": "user", "content": text_input})
            self.new_message = True
            with st.chat_message("user"):
                st.markdown(text_input)

    def handle_speech_input(self):
        """Process speech input from the user."""
        audio_input = st.audio_input('Click the icon to start and stop recording', disabled=(self.modality != "Speech"))
        if audio_input and not self.new_message:
            transcription = self.client.audio.transcriptions.create(
                model="whisper-1", file=audio_input, response_format="text"
            )
            st.session_state.messages.append({"role": "user", "content": transcription})
            self.new_message = True
            with st.chat_message("user"):
                st.markdown(transcription)

    def stream_handler(self):
    
        for chunk in self.stream:
            try:
                if chunk.type == "response.output_text.delta":
                    yield chunk.delta
                
            except Exception as e:
                print(f"Error in stream: {e}")
                st.error(f"Error in stream: {e}")

    def generate_assistant_response(self):
        """Generate assistant's response using AI model."""

        if self.new_message:
            with st.chat_message("assistant"):

                # If stream is True, use the helper stream_handler()
                self.stream = self.client.responses.create(
                    model=self.model,
                    input=st.session_state.messages,
                    stream=True,
                    tools=self.tools,
                    truncation="auto"
                )
                
                
                response = self.stream_handler()
                final_response = st.write_stream(response)
                
                # Use a handler to yield text stream
                for text in self.stream_handler():
                   st.write_stream(text)
                # Add final response to messages list
                st.session_state.messages.append({"role": "assistant", "content": final_response})




                        

                

    def process_stream_placeholder(self, response):
            
            # Original logic for handling tools
            # may eliminate streaming to simplify responses.

            for chunk in response:
                tool_calls = None
                if chunk.choices[0].message.tool_calls is not None:
                    tool_calls = chunk.choices[0].message.tool_calls
                # Write message if no tool call

                if tool_calls is not None:
                    # You MUST append the tool call message as its native message object or OpenAI will throw errors
                    st.session_state.messages.append(response.choices[0].message)
                    
                    for tool_call in tool_calls:
                        func_name = tool_call.function.name
                        args = tool_call.function.arguments
                        args = json.loads(args)
                        tool_call_id = tool_call.id
                        
                        self.handle_function_input(
                            func_name,
                            args,
                            tool_call_id
                        )
                    self.tool_use_completion()


                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=st.session_state.messages,
                    stream=False,
                    tools=self.tools,
                )
                self.process_unstreamed_response(response)
                self.new_message = False

    def process_unstreamed_response(self, response):
        """
        Process AI model response, including any tool calls, and update messages.

        Args:
            response: The response object from the AI model.
        """
        tool_calls = None

        if response.choices[0].message.tool_calls is not None:
            tool_calls = response.choices[0].message.tool_calls
        
        # Debug
        print(f"Here is the full assistant response:\n>>>{response}")

        if tool_calls is not None:
            # You MUST append the tool call message as its native message object or OpenAI will throw errors
            st.session_state.messages.append(response.choices[0].message)
            
            for tool_call in tool_calls:
                func_name = tool_call.function.name
                args = tool_call.function.arguments
                args = json.loads(args)
                tool_call_id = tool_call.id
                
                self.handle_function_input(
                    func_name,
                    args,
                    tool_call_id
                )
            self.tool_use_completion()
        else: # this doesn't work when called, bypassing in Tool Use Completion
            text_response = response.choices[0].message.content
            if text_response:
                st.markdown(text_response)
                st.session_state.messages.append({"role": "assistant", "content": text_response})
                self.text_response = text_response

    def handle_function_input(self, func_name, args, tool_call_id):
        """Handle a user input by making a request to the MicrosoftGraphAgent."""
        try:
            if func_name == 'call_graph_agent':
                st.markdown("Making a request to the Microsoft Graph Agent...")
                result = self.call_graph_agent(args.get('operator_request'))
                print(f"Here is the full call_graph_agent result:\n>>>{result}") #debug
                function_call_result_message = {"role": "tool", "content": str(result), "tool_call_id": tool_call_id}
                
                # Debug
                print(f"Here is the full function call result message:\n>>>{function_call_result_message}")
                
                st.session_state.messages.append(function_call_result_message)
        except Exception as e:
            st.error(f"Function call error: {e}")

    def tool_use_completion(self):
        """Generate a completion from the AI model after a tool use."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=st.session_state.messages,
                stream=False,
                tools=self.tools,
            )
            # Keep processing via recursion if agent wants to use tools again
            if response.choices[0].message.tool_calls is not None:
                self.process_unstreamed_response(response)

            elif response.choices[0].message.content is not None:
                st.session_state.messages.append({'role': 'assistant', 'content': response.choices[0].message.content})
                print(f"Printing full messages from tool_use_completion:\n>>>{st.session_state.messages}")
                # Already inside an assistant message, can print content in markdown
                st.markdown(response.choices[0].message.content)

        except Exception as e:
            st.error(f"Tool use completion error: {e}")

    def display_messages(self):
        """Display all user and assistant messages to the chat interface."""
        # if st.session_state["modality_change"]:
        for message in st.session_state.messages:
            # Dispense with any tool message prior to processing messages into chat flow
            if isinstance(message, dict):
                if message["role"] not in ["system", "tool"]:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])
                # st.session_state["modality_change"] = False

            # Check if the message is a ChatCompletion object (response from OpenAI API)
            elif isinstance(message, object):  # This will catch all messages, but we narrow down with attributes below
                # Ensure the message has 'choices' and 'content' attributes (typical for OpenAI responses)
                if hasattr(message, "tool_calls") and hasattr(message, "refusal"):
                    # Ensure it's not a tool call (if tool_calls attribute exists)
                    if not getattr(message, "tool_calls", None):
                        # Display the assistant's message content
                        with st.chat_message(message.role):
                            st.markdown(message.content)

        # Debug
        if isinstance(st.session_state.messages, list):
            print(f"Printing all messages every time display_messages runs:\n>>>{st.session_state.messages}")

    def main(self):
        """Main function to run the Affinity Assist application."""
        self.setup_ui()
        self.display_messages()
        self.handle_input()
        self.generate_assistant_response()