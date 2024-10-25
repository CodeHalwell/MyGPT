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
    const errorSpan = errorDiv.querySelector('span');
    errorSpan.textContent = message;
    errorDiv.classList.add('visible');
    setTimeout(() => {
        errorDiv.classList.remove('visible');
    }, 5000);
}

async function createNewChat() {
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
        window.location.reload();
    } catch (error) {
        showError(error.message);
    }
}

async function loadChat(chatId) {
    try {
        // Update active state
        document.querySelectorAll('.chat-item').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.chatId === chatId) {
                item.classList.add('active');
            }
        });

        currentChatId = chatId;

        // Load messages
        const response = await fetch(`/chat/${chatId}/messages`);
        if (!response.ok) {
            throw new Error('Failed to load messages');
        }

        const messages = await response.json();
        displayMessages(messages);

        // Update chat title
        const titleResponse = await fetch(`/chat/${chatId}/title`);
        if (titleResponse.ok) {
            const titleData = await titleResponse.json();
            updateChatTitle(titleData.title, titleData.tags);
        }
    } catch (error) {
        showError(error.message);
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

        window.location.reload();
    } catch (error) {
        showError(error.message);
    }
}

async function sendMessage(event) {
    event.preventDefault();

    if (!currentChatId) {
        showError('No chat selected');
        return;
    }

    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();

    if (!message) {
        return;
    }

    try {
        // Send the message
        const response = await fetch(`/chat/${currentChatId}/message`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        });

        if (!response.ok) {
            throw new Error('Failed to send message');
        }

        // Clear input and show loading
        messageInput.value = '';
        showLoading(true);

        // Start streaming the response
        if (currentEventSource) {
            currentEventSource.close();
        }

        currentEventSource = new EventSource(`/chat/${currentChatId}/message/stream`);
        let assistantMessage = document.createElement('div');
        assistantMessage.className = 'message assistant';
        chatMessages.appendChild(assistantMessage);

        currentEventSource.onmessage = function(event) {
            if (event.data === '[DONE]') {
                currentEventSource.close();
                showLoading(false);
                hljs.highlightAll();
                chatMessages.scrollTop = chatMessages.scrollHeight;
            } else {
                assistantMessage.innerHTML += event.data;
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        };

        currentEventSource.onerror = function(error) {
            currentEventSource.close();
            showLoading(false);
            showError('Error receiving response');
        };

    } catch (error) {
        showError(error.message);
        showLoading(false);
    }
}

function displayMessages(messages) {
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.innerHTML = '';
    
    messages.forEach(message => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${message.role}`;
        messageDiv.innerHTML = message.content;
        chatMessages.appendChild(messageDiv);
    });

    hljs.highlightAll();
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function updateChatTitle(title, tags) {
    const chatTitle = document.querySelector('.chat-title');
    if (chatTitle) {
        chatTitle.textContent = title;
    }
}
