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
    
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=formatted_messages,
        stream=True
    )
    
    for chunk in response:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

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
