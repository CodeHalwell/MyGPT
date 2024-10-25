let currentChatId = null;

document.addEventListener('DOMContentLoaded', function() {
    const newChatBtn = document.getElementById('newChatBtn');
    const messageForm = document.getElementById('messageForm');
    const chatMessages = document.getElementById('chatMessages');
    const chatItems = document.querySelectorAll('.chat-item');

    newChatBtn.addEventListener('click', createNewChat);
    messageForm.addEventListener('submit', sendMessage);
    chatItems.forEach(item => {
        item.addEventListener('click', () => loadChat(item.dataset.chatId));
    });

    // Load the first chat if it exists
    if (chatItems.length > 0) {
        loadChat(chatItems[0].dataset.chatId);
    }
});

function createNewChat() {
    fetch('/chat/new', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        currentChatId = data.chat_id;
        location.reload(); // Refresh to show new chat in sidebar
    });
}

function loadChat(chatId) {
    currentChatId = chatId;
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.innerHTML = '';

    fetch(`/chat/${chatId}/messages`)
        .then(response => response.json())
        .then(messages => {
            messages.forEach(message => {
                appendMessage(message.content, message.role);
            });
            chatMessages.scrollTop = chatMessages.scrollHeight;
        });

    // Update active state in sidebar
    document.querySelectorAll('.chat-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.chatId === chatId) {
            item.classList.add('active');
        }
    });
}

function sendMessage(e) {
    e.preventDefault();
    if (!currentChatId) return;

    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    if (!message) return;

    messageInput.value = '';
    appendMessage(message, 'user');

    fetch(`/chat/${currentChatId}/message`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message })
    })
    .then(response => response.json())
    .then(data => {
        appendMessage(data.ai_response, 'assistant');
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.scrollTop = chatMessages.scrollHeight;
    });
}

function appendMessage(content, role) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role} p-3 mb-2 ${role === 'user' ? 'bg-primary' : 'bg-secondary'} rounded`;
    messageDiv.textContent = content;
    chatMessages.appendChild(messageDiv);
}
