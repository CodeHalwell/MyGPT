import os
from openai import OpenAI
from typing import Iterator

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def get_ai_response_stream(messages) -> Iterator[str]:
    formatted_messages = [
        {"role": m.role, "content": m.content}
        for m in messages
    ]
    
    # Add system message to ensure proper code formatting
    system_message = {
        "role": "system",
        "content": """When providing code examples, always start code blocks on a new line after the triple backticks and language specification. For example:

```python
def example():
    pass
```"""
    }
    formatted_messages.insert(0, system_message)
    
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=formatted_messages,
        stream=True
    )
    
    current_code_block = ""
    in_code_block = False
    
    for chunk in response:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            
            # Check for code block markers
            if "```" in content:
                # If we're in a code block and see ```, we're ending it
                if in_code_block:
                    current_code_block += content
                    yield current_code_block
                    current_code_block = ""
                    in_code_block = False
                else:
                    # Starting a new code block
                    yield content + "\n"  # Add newline after ```language
                    in_code_block = True
            else:
                if in_code_block:
                    current_code_block += content
                else:
                    yield content

def get_ai_response(messages):
    formatted_messages = [
        {"role": m.role, "content": m.content}
        for m in messages
    ]
    
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=formatted_messages
    )
    
    return response.choices[0].message.content

def generate_chat_summary(messages) -> str:
    if not messages:
        return "New Chat"
        
    formatted_messages = [
        {"role": m.role, "content": m.content}
        for m in messages
    ]
    
    summary_prompt = {
        "role": "system",
        "content": "Please provide a brief summary (max 50 characters) of the following conversation. Focus on the main topic or question being discussed."
    }
    
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[summary_prompt] + formatted_messages
    )
    
    return response.choices[0].message.content
