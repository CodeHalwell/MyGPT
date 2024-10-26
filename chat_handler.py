import os
from openai import OpenAI
from typing import Iterator, List, Dict, Set
from openai.types.chat import ChatCompletionMessage, ChatCompletionMessageParam, ChatCompletionSystemMessageParam

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def get_ai_response_stream(messages: List[Dict[str, str]]) -> Iterator[str]:
    formatted_messages: List[ChatCompletionMessageParam] = [
        {"role": m["role"], "content": m["content"]}
        for m in messages
    ]
    
    system_message: ChatCompletionSystemMessageParam = {
        "role": "system",
        "content": '''You are a helpful assistant that writes clean, well-formatted code. When providing code examples:
1. Always start with triple backticks and the language name on its own line
2. Put the code on the next line after the language specification
3. Put the closing triple backticks on a new line
4. Format your response like this:

Here's how you can do it:

```python
def example():
    pass
```

Never put code on the same line as the backticks or language specification.'''
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

def get_ai_response(messages: List[Dict[str, str]]) -> str:
    formatted_messages: List[ChatCompletionMessageParam] = [
        {"role": m["role"], "content": m["content"]}
        for m in messages
    ]
    
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=formatted_messages
    )
    
    return response.choices[0].message.content or ""

def generate_chat_summary(messages: List[Dict[str, str]]) -> str:
    if not messages:
        return "New Chat"
        
    formatted_messages: List[ChatCompletionMessageParam] = [
        {"role": m["role"], "content": m["content"]}
        for m in messages
    ]
    
    summary_prompt: ChatCompletionSystemMessageParam = {
        "role": "system",
        "content": "Please provide a brief summary (max 50 characters) of the following conversation. Focus on the main topic or question being discussed."
    }
    
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[summary_prompt] + formatted_messages
    )
    
    return response.choices[0].message.content or ""

def suggest_tags(messages: List[Dict[str, str]]) -> Set[str]:
    """Generate tag suggestions based on conversation content."""
    if not messages:
        return set()
        
    formatted_messages: List[ChatCompletionMessageParam] = [
        {"role": m["role"], "content": m["content"]}
        for m in messages
    ]
    
    tag_prompt: ChatCompletionSystemMessageParam = {
        "role": "system",
        "content": """Analyze the conversation and suggest 1-3 relevant tags.
Rules for tags:
1. Use lowercase letters only
2. Use single words or hyphenated phrases
3. Focus on technical topics, concepts, or programming languages
4. Respond with tags only, separated by commas
Example response: python, algorithms, data-structures"""
    }
    
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[tag_prompt] + formatted_messages
    )
    
    tags = response.choices[0].message.content.split(',')
    return {tag.strip().lower() for tag in tags if tag.strip()}
