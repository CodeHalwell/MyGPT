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
    
    system_message = {
        "role": "system",
        "content": "When providing code examples, always format them properly with triple backticks and language specification."
    }
    formatted_messages.insert(0, system_message)
    
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=formatted_messages,
        stream=True
    )
    
    buffer = ""
    
    for chunk in response:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            buffer += content
            
            # Look for complete code blocks
            while True:
                # Try to find a complete code block
                start = buffer.find("```")
                if start == -1:
                    # No code block started, yield all buffer
                    yield buffer
                    buffer = ""
                    break
                    
                # Look for the end of this code block
                search_start = start + 3
                end = buffer.find("```", search_start)
                if end == -1:
                    # Code block not complete yet, keep in buffer
                    break
                    
                # We found a complete code block
                # Yield everything before it
                if start > 0:
                    yield buffer[:start]
                    
                # Yield the code block
                code_block = buffer[start:end + 3]
                yield code_block
                
                # Keep the rest in the buffer
                buffer = buffer[end + 3:]

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
