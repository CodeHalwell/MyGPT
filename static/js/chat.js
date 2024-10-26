let currentChatId = null;
let currentEventSource = null;

document.addEventListener('DOMContentLoaded', function() {
    console.log('Chat application initialized');
    const newChatBtn = document.getElementById('newChatBtn');
    const messageForm = document.getElementById('messageForm');
    const chatMessages = document.getElementById('chatMessages');
    const chatItems = document.querySelectorAll('.chat-item');
    const deleteChatBtns = document.querySelectorAll('.delete-chat-btn');

    // Initialize highlight.js
    hljs.configure({
        ignoreUnescapedHTML: true
    });
    hljs.highlightAll();

    newChatBtn.addEventListener('click', createNewChat);
    messageForm.addEventListener('submit', sendMessage);
    chatItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            loadChat(item.dataset.chatId);
        });
    });
    deleteChatBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            deleteChat(btn.dataset.chatId);
        });
    });

    // Only load first chat if it exists and URL has no chat_id parameter
    if (chatItems.length > 0 && !new URLSearchParams(window.location.search).has('chat_id')) {
        loadChat(chatItems[0].dataset.chatId);
    }
});

function showLoading(show = true) {
    const spinner = document.getElementById('loadingSpinner');
    if (show) {
        spinner.classList.add('visible');
    } else {
        spinner.classList.remove('visible');
    }
}

function showError(message) {
    console.error('Error:', message);
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.textContent = message;
    errorDiv.classList.add('visible');
    setTimeout(() => {
        errorDiv.classList.remove('visible');
    }, 5000);
}

async function createNewChat() {
    console.log('Creating new chat');
    showLoading();
    try {
        const response = await fetch('/chat/new', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to create new chat');
        }
        
        const data = await response.json();
        console.log('New chat created:', data);
        if (data.chat_id) {
            currentChatId = data.chat_id;
            // Add new chat to the list without full page reload
            const chatList = document.querySelector('.list-group');
            const newChatItem = document.createElement('div');
            newChatItem.className = 'd-flex flex-column chat-list-item';
            newChatItem.innerHTML = `
                <div class="d-flex align-items-center">
                    <a href="#" class="list-group-item list-group-item-action chat-item active" data-chat-id="${data.chat_id}">
                        ${data.title}
                    </a>
                    <button class="btn btn-sm btn-outline-danger delete-chat-btn ms-2" data-chat-id="${data.chat_id}">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
                <div class="chat-tags ms-3 mt-1"></div>
            `;
            
            // Add event listeners to new elements
            const chatItemLink = newChatItem.querySelector('.chat-item');
            const deleteBtn = newChatItem.querySelector('.delete-chat-btn');
            
            chatItemLink.addEventListener('click', (e) => {
                e.preventDefault();
                loadChat(data.chat_id);
            });
            
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                deleteChat(data.chat_id);
            });
            
            // Insert at the beginning of the list
            chatList.insertBefore(newChatItem, chatList.firstChild);
            
            // Clear existing messages
            document.getElementById('chatMessages').innerHTML = '';
            
            // Update active state
            document.querySelectorAll('.chat-item').forEach(item => {
                item.classList.remove('active');
            });
            chatItemLink.classList.add('active');
        } else {
            throw new Error('Invalid response from server');
        }
    } catch (error) {
        console.error('Error creating chat:', error);
        showError('Failed to create new chat: ' + error.message);
    } finally {
        showLoading(false);
    }
}

async function loadChat(chatId) {
    console.log('Loading chat:', chatId);
    if (currentEventSource) {
        currentEventSource.close();
    }
    
    currentChatId = chatId;
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.innerHTML = '';
    showLoading();

    try {
        const response = await fetch(`/chat/${chatId}/messages`);
        if (!response.ok) {
            throw new Error('Failed to load chat messages');
        }
        
        const messages = await response.json();
        console.log('Loaded messages:', messages);
        messages.forEach(message => {
            appendMessage(message.content, message.role, message.model);
        });

        // Apply syntax highlighting to code blocks
        document.querySelectorAll('pre code').forEach((block) => {
            block.removeAttribute('data-highlighted');
            hljs.highlightElement(block);
        });

        chatMessages.scrollTop = chatMessages.scrollHeight;

        // Update active state in sidebar
        document.querySelectorAll('.chat-item').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.chatId === chatId) {
                item.classList.add('active');
            }
        });

        // Update chat title
        await updateChatTitle(chatId);
    } catch (error) {
        showError('Failed to load chat: ' + error.message);
    } finally {
        showLoading(false);
    }
}

async function sendMessage(e) {
    e.preventDefault();
    console.log('Sending message');
    
    const messageInput = document.getElementById('messageInput');
    const modelSelect = document.getElementById('modelSelect');
    const message = messageInput.value.trim();
    const model = modelSelect.value;
    
    if (!message) return;

    // If no chat is selected, create a new one first
    if (!currentChatId) {
        try {
            const response = await fetch('/chat/new', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to create new chat');
            }
            
            const data = await response.json();
            if (!data.chat_id) {
                throw new Error('Invalid response from server');
            }
            currentChatId = data.chat_id;
            // Reload the page to show the new chat
            location.reload();
            return;
        } catch (error) {
            showError('Failed to create new chat: ' + error.message);
            return;
        }
    }

    messageInput.value = '';
    appendMessage(message, 'user');
    showLoading();

    try {
        // First, save the message
        const saveResponse = await fetch(`/chat/${currentChatId}/message`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message, model })
        });

        if (!saveResponse.ok) {
            throw new Error('Failed to save message');
        }

        // Close any existing SSE connection
        if (currentEventSource) {
            currentEventSource.close();
        }

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
                    const chatItem = document.querySelector(`.chat-item[data-chat-id="${currentChatId}"]`);
                    if (chatItem && chatItem.textContent === 'New Chat') {
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

async function deleteChat(chatId) {
    if (!confirm('Are you sure you want to delete this chat?')) {
        return;
    }

    try {
        const response = await fetch(`/chat/${chatId}/delete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error('Failed to delete chat');
        }

        const chatListItem = document.querySelector(`.chat-list-item:has(.chat-item[data-chat-id="${chatId}"])`);
        if (chatListItem) {
            chatListItem.remove();
        }

        // If deleted chat was current chat, clear messages
        if (currentChatId === chatId) {
            document.getElementById('chatMessages').innerHTML = '';
            currentChatId = null;
            
            // Load first available chat if exists
            const firstChat = document.querySelector('.chat-item');
            if (firstChat) {
                loadChat(firstChat.dataset.chatId);
            }
        }
    } catch (error) {
        showError('Failed to delete chat: ' + error.message);
    }
}

async function updateChatTitle(chatId) {
    try {
        const response = await fetch(`/chat/${chatId}/title`);
        if (!response.ok) {
            throw new Error('Failed to fetch chat title');
        }
        
        const data = await response.json();
        const chatItem = document.querySelector(`.chat-item[data-chat-id="${chatId}"]`);
        if (chatItem) {
            chatItem.textContent = data.title;
        }
    } catch (error) {
        console.error('Failed to update chat title:', error);
    }
}

function formatCodeBlocks(content) {
    // Handle triple backtick blocks
    content = content.replace(/```(\w+)?\n([\s\S]*?)\n```/g, (match, language, code) => {
        language = language || 'plaintext';
        // Remove any remaining backticks from the code
        code = code.replace(/`/g, '');
        const formattedCode = code.trim()
            .split('\n')
            .map(line => escapeHtml(line))
            .join('\n');
        return `<pre><code class="language-${language}">${formattedCode}</code></pre>`;
    });
    
    // Handle inline code blocks (single backticks)
    content = content.replace(/`([^`]+)`/g, (match, code) => {
        return `<code class="inline-code">${escapeHtml(code)}</code>`;
    });
    
    // Handle regular line breaks
    const parts = content.split(/(<pre>.*?<\/pre>)/gs);
    return parts.map((part, index) => {
        // If it's a code block, leave it unchanged
        if (index % 2 === 1) return part;
        // For non-code parts, convert newlines to <br>
        return part.replace(/\n/g, '<br>');
    }).join('');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function appendMessage(content, role, model = null) {
    console.log('Appending message:', { role, model, contentLength: content.length });
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    let innerHTML = '';
    
    // Add model information for assistant messages
    if (role === 'assistant' && model) {
        innerHTML += `<div class="model-info">Model: ${model}</div>`;
    }
    
    // Format content and handle code blocks
    innerHTML += formatCodeBlocks(content);
    messageDiv.innerHTML = innerHTML;
    
    chatMessages.appendChild(messageDiv);
    messageDiv.scrollIntoView({ behavior: 'smooth' });
    
    // Initialize syntax highlighting for new code blocks
    messageDiv.querySelectorAll('pre code').forEach((block) => {
        block.removeAttribute('data-highlighted');
        hljs.highlightElement(block);
    });
}
