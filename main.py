
import json
from dotenv import load_dotenv
from openai import AssistantEventHandler, OpenAI

import os
import sys

import re
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Load environment variables from .env file
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

def initialize_client():
    return OpenAI(api_key=api_key)

import random
def get_current_temperature(**kwargs) -> str:
    location = kwargs.get("location", "Unknown Location")
    unit = kwargs.get("unit", "Celsius")  # Default to Celsius if not provided

    if unit not in ["Celsius", "Fahrenheit"]:
        raise ValueError("Invalid unit. Must be 'Celsius' or 'Fahrenheit'.")

    temperature = random.randint(30, 50)
    return f"{temperature} {unit}"

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
            # Define the list to store tool outputs
            tool_outputs = []
            
            # Loop through each tool in the required action section
            for tool in run.required_action.submit_tool_outputs.tool_calls:
                if tool.function.name == "get_current_temperature":
                    arguments = json.loads(tool.function.arguments)
                    logger.debug(f"Tool Call ID: {tool.id} | Arguments: {arguments}")
                    try:
                        temperature_output = get_current_temperature(**arguments)
                    except ValueError as ve:
                        temperature_output = f"Error: {ve}"

                    tool_outputs.append({
                        "tool_call_id": tool.id,
                        "output": temperature_output
                    })
                elif tool.function.name == "get_rain_probability":
                    tool_outputs.append({
                    "tool_call_id": tool.id,
                    "output": "0.06"
                    })
                else:
                    print(f"Assistant is processing your request. Current status: {run.status}")

            # Submit all tool outputs at once after collecting them in a list
            if tool_outputs:
                try:
                    run = client.beta.threads.runs.submit_tool_outputs_and_poll(
                    thread_id=thread.id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                    )
                    print("Tool outputs submitted successfully.")
                except Exception as e:
                    print("Failed to submit tool outputs:", e)
                else:
                    print("No tool outputs to submit.")
                
            if run.status == 'completed':
                messages = client.beta.threads.messages.list(
                    thread_id=thread.id
                )
            if messages.data:
                last_message = messages.data[0]  # Assuming the first item is the latest
                display_message(last_message)
            else:
                print(run.status)

        except KeyboardInterrupt:
            print("\nDetected keyboard interrupt. Exiting the chat. Goodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            print("Please try again or type 'exit' to quit.")

# Example initialization (you need to replace these with your actual initialization code)
if __name__ == "__main__":
    try:
        assistant_id = 'asst_qAFskEUFjndMGiSXOBKZg7AN'
        # Initialize your API client here
        client = initialize_client()  # Replace with actual client initialization
        assistant = get_assistant(client,assistant_id)  # Replace with actual assistant retrieval
    except Exception as init_e:
        print(f"Failed to initialize client or assistant: {init_e}")
        sys.exit(1)

    main(client, assistant)

