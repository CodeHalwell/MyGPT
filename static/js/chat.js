let currentChatId = null;
let currentEventSource = null;

document.addEventListener('DOMContentLoaded', function() {
    console.log('Chat application initialized');
    const newChatBtn = document.getElementById('newChatBtn');
    const messageForm = document.getElementById('messageForm');
    const chatMessages = document.getElementById('chatMessages');
    const chatItems = document.querySelectorAll('.chat-item');
    const deleteChatBtns = document.querySelectorAll('.delete-chat-btn');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const chatArea = document.querySelector('.chat-area');

    // Initialize highlight.js
    hljs.configure({
        ignoreUnescapedHTML: true
    });
    hljs.highlightAll();

    // Load saved sidebar state
    const sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    if (sidebarCollapsed) {
        sidebar.classList.add('collapsed');
        chatArea.classList.add('sidebar-collapsed');
    }

    // Sidebar toggle functionality
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            chatArea.classList.toggle('sidebar-collapsed');
            
            // Save state
            localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
        });
    }

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

[Rest of the chat.js file remains unchanged...]
