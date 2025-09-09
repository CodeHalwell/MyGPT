import os
import asyncio
from typing import Iterator, List, Dict, Optional
from openai import OpenAI
from anthropic import Anthropic
import google.generativeai as genai
from mistralai import Mistral

class MultiProviderChatHandler:
    def __init__(self):
        # Initialize API clients with better error handling
        try:
            openai_key = os.environ.get("OPENAI_API_KEY")
            if openai_key:
                self.openai_client = OpenAI(api_key=openai_key)
            else:
                self.openai_client = None
        except Exception as e:
            print(f"Error initializing OpenAI client: {e}")
            self.openai_client = None
        
        # Initialize other providers (will use OpenAI as fallback if keys not available)
        try:
            anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
            if anthropic_key:
                self.anthropic_client = Anthropic(api_key=anthropic_key)
            else:
                self.anthropic_client = None
        except Exception as e:
            print(f"Error initializing Anthropic client: {e}")
            self.anthropic_client = None
            
        try:
            google_key = os.environ.get("GOOGLE_API_KEY")
            if google_key:
                genai.configure(api_key=google_key)
                self.google_client = genai
            else:
                self.google_client = None
        except Exception as e:
            print(f"Error initializing Google client: {e}")
            self.google_client = None
            
        try:
            mistral_key = os.environ.get("MISTRAL_API_KEY")
            if mistral_key:
                self.mistral_client = Mistral(api_key=mistral_key)
            else:
                self.mistral_client = None
        except Exception as e:
            print(f"Error initializing Mistral client: {e}")
            self.mistral_client = None
        
        # Model mappings for each provider
        self.model_mappings = {
            # OpenAI models (map new models to available ones for now)
            "gpt-5": "gpt-4o",  # Fallback until API available
            "gpt-4.1": "gpt-4o",  # Fallback until API available  
            "o3": "gpt-4o",  # Fallback until API available
            "o3-mini": "gpt-4o-mini",  # Fallback until API available
            "gpt-4o": "gpt-4o",
            "gpt-4o-mini": "gpt-4o-mini",
            "gpt-realtime": "gpt-4o",  # Fallback for now
            
            # Anthropic models (map new models to available ones for now)
            "claude-opus-4.1": "claude-3-5-sonnet-20241022",  # Fallback
            "claude-sonnet-4": "claude-3-5-sonnet-20241022",  # Fallback
            "claude-3.7-sonnet": "claude-3-5-sonnet-20241022",  # Fallback
            "claude-3-5-sonnet-20241022": "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022": "claude-3-5-haiku-20241022",
            
            # Google models (map new models to available ones for now)
            "gemini-2.5-pro": "gemini-1.5-pro",  # Fallback
            "gemini-2.5-flash": "gemini-1.5-flash",  # Fallback
            "gemini-2.0-flash": "gemini-1.5-flash",  # Fallback
            "gemini-1.5-pro": "gemini-1.5-pro",
            "gemini-1.5-flash": "gemini-1.5-flash",
            
            # Mistral models (map new models to available ones for now)
            "mistral-large-24.11": "mistral-large-latest",  # Fallback
            "pixtral-large-2411": "mistral-large-latest",  # Fallback
            "codestral-25.01": "codestral-latest",  # Fallback
            "mistral-small-3.1": "mistral-small-latest",  # Fallback
        }
    
    def get_provider_for_model(self, model: str) -> str:
        """Determine which provider to use based on model name"""
        if any(provider in model for provider in ["gpt", "o3"]):
            return "openai"
        elif "claude" in model:
            return "anthropic"
        elif "gemini" in model:
            return "google"
        elif "mistral" in model or "pixtral" in model or "codestral" in model:
            return "mistral"
        else:
            return "openai"  # Default fallback
    
    def get_ai_response_stream(self, messages: List[Dict[str, str]], model: str = "gpt-4o") -> Iterator[str]:
        """Get streaming response from appropriate AI provider"""
        provider = self.get_provider_for_model(model)
        actual_model = self.model_mappings.get(model, model)
        
        try:
            if provider == "openai" and self.openai_client:
                return self._get_openai_response(messages, actual_model)
            elif provider == "anthropic" and self.anthropic_client:
                return self._get_anthropic_response(messages, actual_model)
            elif provider == "google" and self.google_client:
                return self._get_google_response(messages, actual_model)
            elif provider == "mistral" and self.mistral_client:
                return self._get_mistral_response(messages, actual_model)
            else:
                # Fallback to OpenAI if other providers not available
                if self.openai_client:
                    return self._get_openai_response(messages, "gpt-4o")
                else:
                    # Return a fallback response if no providers are available
                    return self._get_fallback_response()
        except Exception as e:
            # If any provider fails, fallback to OpenAI or fallback response
            print(f"Error with {provider}: {e}")
            if self.openai_client:
                return self._get_openai_response(messages, "gpt-4o")
            else:
                return self._get_fallback_response()
    
    def _get_openai_response(self, messages: List[Dict[str, str]], model: str) -> Iterator[str]:
        """Get response from OpenAI"""
        formatted_messages = [{"role": m["role"], "content": m["content"]} for m in messages]
        
        system_message = {
            "role": "system",
            "content": '''You are a helpful assistant that answers queries professionally. When providing code examples:
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
        
        response = self.openai_client.chat.completions.create(
            model=model,
            messages=formatted_messages,
            stream=True
        )
        
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
    
    def _get_anthropic_response(self, messages: List[Dict[str, str]], model: str) -> Iterator[str]:
        """Get response from Anthropic Claude"""
        # Convert messages format for Anthropic
        claude_messages = []
        system_prompt = "You are a helpful assistant that answers queries professionally."
        
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                claude_messages.append({"role": msg["role"], "content": msg["content"]})
        
        with self.anthropic_client.messages.stream(
            model=model,
            max_tokens=4000,
            system=system_prompt,
            messages=claude_messages
        ) as stream:
            for text in stream.text_stream:
                yield text
    
    def _get_google_response(self, messages: List[Dict[str, str]], model: str) -> Iterator[str]:
        """Get response from Google Gemini"""
        # Convert messages for Gemini
        gemini_model = self.google_client.GenerativeModel(model)
        
        # Combine all messages into a single prompt for Gemini
        prompt_parts = []
        for msg in messages:
            if msg["role"] != "system":
                role_prefix = "Human: " if msg["role"] == "user" else "Assistant: "
                prompt_parts.append(f"{role_prefix}{msg['content']}")
        
        prompt = "\n\n".join(prompt_parts)
        
        response = gemini_model.generate_content(
            prompt,
            stream=True,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=4000,
                temperature=0.7,
            )
        )
        
        for chunk in response:
            if chunk.text:
                yield chunk.text
    
    def _get_mistral_response(self, messages: List[Dict[str, str]], model: str) -> Iterator[str]:
        """Get response from Mistral"""
        # Convert messages for Mistral
        mistral_messages = [{"role": m["role"], "content": m["content"]} for m in messages]
        
        response = self.mistral_client.chat.stream(
            model=model,
            messages=mistral_messages,
            max_tokens=4000,
        )
        
        for chunk in response:
            if chunk.data and hasattr(chunk.data, 'choices') and chunk.data.choices:
                if chunk.data.choices[0].delta.content:
                    yield chunk.data.choices[0].delta.content
    
    def _get_fallback_response(self) -> Iterator[str]:
        """Fallback response when no AI providers are available"""
        fallback_message = "I apologize, but the AI service is currently unavailable. Please check your API keys and try again later."
        for char in fallback_message:
            yield char

# Create global instance
multi_provider_handler = MultiProviderChatHandler()

# Keep the original function for backwards compatibility
def get_ai_response_stream(messages: List[Dict[str, str]], model: str = "gpt-4o") -> Iterator[str]:
    return multi_provider_handler.get_ai_response_stream(messages, model)