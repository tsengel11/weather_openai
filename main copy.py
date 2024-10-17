from typing import override
from dotenv import load_dotenv
from openai import AssistantEventHandler, OpenAI

import os
import sys

import get_current_temperature

# Load environment variables from .env file
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

def initialize_client():
    return OpenAI(api_key=api_key)

def get_assistant(client, assistan_id= None):

    if assistan_id is None:
        assistant = client.beta.assistants.create(
        instructions="You are a weather bot. Use the provided functions to answer questions.",
        model="gpt-4o",
        tools=[
            {
            "type": "function",
            "function": {
                "name": "get_current_temperature",
                "description": "Get the current temperature for a specific location",
                "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                    "type": "string",
                    "description": "The city and state, e.g., San Francisco, CA"
                    },
                    "unit": {
                    "type": "string",
                    "enum": ["Celsius", "Fahrenheit"],
                    "description": "The temperature unit to use. Infer this from the user's location."
                    }
                },
                "required": ["location", "unit"]
                }
            }
            },
            {
            "type": "function",
            "function": {
                "name": "get_rain_probability",
                "description": "Get the probability of rain for a specific location",
                "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                    "type": "string",
                    "description": "The city and state, e.g., San Francisco, CA"
                    }
                },
                "required": ["location"]
                }
            }
            }
        ]
        )
    else:
        assistant = client.beta.assistants.retrieve(assistan_id)
    return assistant
    #print("Welcome to the ChatGPT Interactive Assistant!")

def display_message(message):
    """
    Displays a message in a readable format.
    
    Args:
        message: The Message object to display.
    """
    role = message.role.capitalize()
    content_blocks = message.content

    # Concatenate all text from content blocks
    content_text = ""
    for block in content_blocks:
        if block.type == 'text':
            content_text += block.text.value + "\n"
        # You can handle other block types (e.g., images, attachments) here if needed

    # Remove trailing newline
    content_text = content_text.strip()
    content_text = content_text.replace('\\(', '(').replace('\\)', ')')
    print(f"{role}: {content_text}\n")

class EventHandler(AssistantEventHandler):
    @override
    def on_event(self, event):
      # Retrieve events that are denoted with 'requires_action'
      # since these will have our tool_calls
      if event.event == 'thread.run.requires_action':
        run_id = event.data.id  # Retrieve the run ID from the event data
        self.handle_requires_action(event.data, run_id)
 
    def handle_requires_action(self, data, run_id):
      tool_outputs = []
        
      for tool in data.required_action.submit_tool_outputs.tool_calls:
        print(tool.function)
        if tool.function.name == "get_current_temperature":
            tool_outputs.append({
                "tool_call_id": tool.id,
                "output": get_current_temperature()  # Call the dummy function here
            })
        elif tool.function.name == "get_rain_probability":
          tool_outputs.append({"tool_call_id": tool.id, "output": "0.06"})
        
      # Submit all tool_outputs at the same time
      self.submit_tool_outputs(tool_outputs, run_id)
 
    def submit_tool_outputs(self, tool_outputs, run_id):
      # Use the submit_tool_outputs_stream helper
      with client.beta.threads.runs.submit_tool_outputs_stream(
        thread_id=self.current_run.thread_id,
        run_id=self.current_run.id,
        tool_outputs=tool_outputs,
        event_handler=EventHandler(),
      ) as stream:
        for text in stream.text_deltas:
          print(text, end="", flush=True)
        print()

def main(client, assistant):
    """
    Main function to run the interactive ChatGPT assistant.
    
    Args:
        client: The initialized API client.
        assistant: The assistant instance to interact with.
    """
    print("Welcome to the ChatGPT Interactive Assistant!")
    print("Type 'exit' or 'quit' to end the conversation.\n")

    # Initialize the conversation with an empty message list
    messages = []
    
    try:
        # Create a new thread for the conversation
        thread = client.beta.threads.create()
    except Exception as e:
        print(f"Error creating thread: {e}")
        sys.exit(1)  # Exit the program if thread creation fails

    while True:
        try:
            # Get user input from the keyboard
            user_input = input("You: ").strip()
            
            if user_input.lower() in ["exit", "quit"]:
                print("Exiting the chat. Goodbye!")
                break

            if not user_input:
                print("Please enter a message or type 'exit' to quit.")
                continue

            # Create a user message in the thread
            message = client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=user_input
            )  

            # Initiate a run to get the assistant's response
            run = client.beta.threads.runs.create_and_poll(
                thread_id=thread.id,
                assistant_id=assistant.id,
                instructions=user_input
            )

            if run.status == 'completed': 
                # Retrieve all messages in the thread
                messages = client.beta.threads.messages.list(
                    thread_id=thread.id
                )
                if messages.data:
                    last_message = messages.data[0]  # Assuming the first item is the latest
                    display_message(last_message)
            else:
                print(f"Assistant is processing your request. Current status: {run.status}")

        except KeyboardInterrupt:
            print("\nDetected keyboard interrupt. Exiting the chat. Goodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            print("Please try again or type 'exit' to quit.")

# Example initialization (you need to replace these with your actual initialization code)
if __name__ == "__main__":
    try:
        assistant_id = 'asst_akeF6CGGZxaP3rzXqkf9Y95y'
        # Initialize your API client here
        client = initialize_client()  # Replace with actual client initialization
        assistant = get_assistant(client)  # Replace with actual assistant retrieval
    except Exception as init_e:
        print(f"Failed to initialize client or assistant: {init_e}")
        sys.exit(1)

    main(client, assistant)

