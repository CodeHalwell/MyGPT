import os
from openai import OpenAI
from typing import Iterator, List, Dict, Set
from openai.types.chat import ChatCompletionMessage, ChatCompletionMessageParam, ChatCompletionSystemMessageParam

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
try:
    if OPENAI_API_KEY:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
    else:
        openai_client = None
except Exception as e:
    print(f"Error initializing OpenAI client in chat_handler: {e}")
    openai_client = None

# Model mapping for custom model names
MODEL_MAPPING = {
    "gpt-4o": "gpt-4",
    "gpt-4o-mini": "gpt-3.5-turbo",
    "gpt-4": "gpt-4",
    "gpt-4-turbo": "gpt-4-1106-preview",
    "gpt-3.5-turbo": "gpt-3.5-turbo"
}


def get_ai_response_stream(messages: List[Dict[str, str]],
                           model: str = "gpt-4o") -> Iterator[str]:
    if not openai_client:
        # Fallback response when OpenAI client is not available
        fallback_message = "I apologize, but the AI service is currently unavailable. Please check your OpenAI API key and try again later."
        for char in fallback_message:
            yield char
        return
    
    # Map the model name to the actual OpenAI model
    actual_model = MODEL_MAPPING.get(model, "gpt-4o")

    formatted_messages: List[ChatCompletionMessageParam] = [{
        "role":
        m["role"],
        "content":
        m["content"]
    } for m in messages]

    system_message: ChatCompletionSystemMessageParam = {
        "role":
        "system",
        "content":
        '''You are a helpful assistant that answers generally queries to the user. You will help with with whatever you need to help with. You will answer in a way that is friendly and helpful. Should you be asked to write code;
        
        write clean, well-formatted code. When providing code examples:
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
        model=actual_model, messages=formatted_messages, stream=True)

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


def get_ai_response(messages: List[Dict[str, str]],
                    model: str = "gpt-4o") -> str:
    if not openai_client:
        return "AI service is currently unavailable. Please check your API keys."
    
    # Map the model name to the actual OpenAI model
    actual_model = MODEL_MAPPING.get(model, "gpt-4o")

    formatted_messages: List[ChatCompletionMessageParam] = [{
        "role":
        m["role"],
        "content":
        m["content"]
    } for m in messages]

    try:
        response = openai_client.chat.completions.create(
            model=actual_model, messages=formatted_messages)
        return response.choices[0].message.content or ""
    except Exception as e:
        print(f"Error in get_ai_response: {e}")
        return "Error generating response. Please try again."


def generate_chat_summary(messages: List[Dict[str, str]]) -> str:
    if not messages:
        return "New Chat"
    
    if not openai_client:
        # Fallback to simple summary when OpenAI client is not available
        first_message = next((m for m in messages if m["role"] == "user"), None)
        if first_message:
            content = first_message["content"][:40]
            return content + "..." if len(first_message["content"]) > 40 else content
        return "New Chat"

    formatted_messages: List[ChatCompletionMessageParam] = [{
        "role":
        m["role"],
        "content":
        m["content"]
    } for m in messages]

    summary_prompt: ChatCompletionSystemMessageParam = {
        "role":
        "system",
        "content":
        "Please provide a brief summary (max 50 characters) of the following conversation. Focus on the main topic or question being discussed."
    }

    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo", messages=[summary_prompt] + formatted_messages)
        return response.choices[0].message.content or "New Chat"
    except Exception as e:
        print(f"Error generating chat summary: {e}")
        # Fallback to simple summary
        first_message = next((m for m in messages if m["role"] == "user"), None)
        if first_message:
            content = first_message["content"][:40]
            return content + "..." if len(first_message["content"]) > 40 else content
        return "New Chat"


def suggest_tags(messages: List[Dict[str, str]]) -> Set[str]:
    """Generate tag suggestions based on conversation content."""
    if not messages:
        return set()
    
    if not openai_client:
        # Fallback to simple keyword-based tags when OpenAI client is not available
        content = " ".join([m["content"].lower() for m in messages if m["role"] == "user"])
        fallback_tags = set()
        
        # Simple keyword matching
        if "python" in content:
            fallback_tags.add("python")
        if "javascript" in content or "js" in content:
            fallback_tags.add("javascript")
        if "code" in content or "programming" in content:
            fallback_tags.add("coding")
        if "data" in content:
            fallback_tags.add("data")
        if "web" in content or "website" in content:
            fallback_tags.add("web")
        
        return fallback_tags if fallback_tags else {"general"}

    formatted_messages: List[ChatCompletionMessageParam] = [{
        "role":
        m["role"],
        "content":
        m["content"]
    } for m in messages]

    tag_prompt: ChatCompletionSystemMessageParam = {
        "role":
        "system",
        "content":
        """Analyze the conversation and suggest 1-3 relevant tags.
Rules for tags:
1. Use lowercase letters only
2. Use single words or hyphenated phrases
3. Focus on technical topics, concepts, or programming languages
4. Respond with tags only, separated by commas
Example response: python, algorithms, data-structures"""
    }

    try:
        response = openai_client.chat.completions.create(model="gpt-3.5-turbo",
                                                         messages=[tag_prompt] +
                                                         formatted_messages)

        if response.choices[0].message.content:
            tags = response.choices[0].message.content.split(',')
            return {tag.strip().lower() for tag in tags if tag.strip()}
        return {"general"}
    except Exception as e:
        print(f"Error generating tags: {e}")
        # Fallback to simple keyword-based tags
        content = " ".join([m["content"].lower() for m in messages if m["role"] == "user"])
        fallback_tags = set()
        
        if "python" in content:
            fallback_tags.add("python")
        if "javascript" in content or "js" in content:
            fallback_tags.add("javascript")
        if "code" in content or "programming" in content:
            fallback_tags.add("coding")
        if "data" in content:
            fallback_tags.add("data")
        if "web" in content or "website" in content:
            fallback_tags.add("web")
        
        return fallback_tags if fallback_tags else {"general"}
