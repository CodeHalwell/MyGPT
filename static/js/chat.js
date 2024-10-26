// ... Previous code remains the same until line 189 ...
        // Set up SSE connection for streaming response
        currentEventSource = new EventSource(`/chat/${currentChatId}/message/stream?model=${model}`);
        let assistantResponse = '';
        let responseDiv = null;

        currentEventSource.onmessage = function(event) {
            if (event.data === '[DONE]') {
                currentEventSource.close();
                showLoading(false);
                
                // Apply final formatting and highlighting
                if (responseDiv) {
                    responseDiv.innerHTML = `<div class="model-info">Model: ${model}</div>` + formatCodeBlocks(assistantResponse);
                    responseDiv.querySelectorAll('pre code').forEach((block) => {
                        block.removeAttribute('data-highlighted');
                        hljs.highlightElement(block);
                    });
                    
                    // Update chat title if this is a new chat
                    if (document.querySelector('.chat-item[data-chat-id="${currentChatId}"]').textContent === 'New Chat') {
                        updateChatTitle(currentChatId);
                    }
                }
                
                // Ensure the last message is visible
                responseDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
                return;
            }

            if (!responseDiv) {
                responseDiv = document.createElement('div');
                responseDiv.className = 'message assistant';
                // Add model information at the top of assistant message
                const modelInfo = document.createElement('div');
                modelInfo.className = 'model-info';
                modelInfo.textContent = `Model: ${model}`;
                responseDiv.appendChild(modelInfo);
                document.getElementById('chatMessages').appendChild(responseDiv);
            }

            assistantResponse += event.data;
            // Format and highlight code continuously as it streams in
            responseDiv.innerHTML = `<div class="model-info">Model: ${model}</div>` + formatCodeBlocks(assistantResponse);
            
            // Highlight any complete code blocks
            responseDiv.querySelectorAll('pre code').forEach((block) => {
                if (!block.hasAttribute('data-highlighted')) {
                    hljs.highlightElement(block);
                    block.setAttribute('data-highlighted', 'true');
                }
            });
            
            // Smooth scroll to follow the response
            responseDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
        };

        currentEventSource.onerror = function(error) {
            console.error('EventSource error:', error);
            currentEventSource.close();
            showLoading(false);
            showError('Connection lost. Please try again.');
        };
    } catch (error) {
        showError('Failed to send message: ' + error.message);
        showLoading(false);
    }
}

// ... Rest of the file remains the same ...
