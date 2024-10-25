let currentChatId = null;
let currentEventSource = null;

document.addEventListener('DOMContentLoaded', function() {
    console.log('Chat application initialized');
    const newChatBtn = document.getElementById('newChatBtn');
    const messageForm = document.getElementById('messageForm');
    const chatMessages = document.getElementById('chatMessages');
    const chatItems = document.querySelectorAll('.chat-item');

    newChatBtn.addEventListener('click', createNewChat);
    messageForm.addEventListener('submit', sendMessage);
    chatItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            loadChat(item.dataset.chatId);
        });
    });

    // Load the first chat if it exists
    if (chatItems.length > 0) {
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
        currentChatId = data.chat_id;
        location.reload(); // Refresh to show new chat in sidebar
    } catch (error) {
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
            appendMessage(message.content, message.role);
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
    
    if (!currentChatId) {
        showError('No chat selected');
        return;
    }

    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    if (!message) return;

    messageInput.value = '';
    appendMessage(message, 'user');
    showLoading();

    try {
        if (currentEventSource) {
            currentEventSource.close();
        }

        currentEventSource = new EventSource(`/chat/${currentChatId}/message?message=${encodeURIComponent(message)}`);
        let assistantResponse = '';
        let responseDiv = null;

        currentEventSource.onmessage = function(event) {
            if (event.data === '[DONE]') {
                currentEventSource.close();
                showLoading(false);
                updateChatTitle(currentChatId);
                return;
            }

            if (!responseDiv) {
                responseDiv = document.createElement('div');
                responseDiv.className = 'message assistant';
                document.getElementById('chatMessages').appendChild(responseDiv);
            }

            assistantResponse += event.data;
            responseDiv.textContent = assistantResponse;
            responseDiv.scrollIntoView({ behavior: 'smooth' });
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

function appendMessage(content, role) {
    console.log('Appending message:', { role, contentLength: content.length });
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.textContent = content;
    chatMessages.appendChild(messageDiv);
    messageDiv.scrollIntoView({ behavior: 'smooth' });
}
