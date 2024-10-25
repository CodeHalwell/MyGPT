import os
from openai import OpenAI

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

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
