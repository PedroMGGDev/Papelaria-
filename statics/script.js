// Global variables
let isLoading = false;

// DOM elements
const chatForm = document.getElementById('chatForm');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const chatMessages = document.getElementById('chatMessages');
const loadingIndicator = document.getElementById('loadingIndicator');
const resetBtn = document.getElementById('resetBtn');
const successModal = new bootstrap.Modal(document.getElementById('successModal'));

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    console.log('Papelaria Digital Chat initialized');
    
    // Get or create session ID and store in localStorage
    if (!localStorage.getItem('chat_session_id')) {
        localStorage.setItem('chat_session_id', 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now());
    }
    
    messageInput.focus();
    
    // Add initial bot greeting message
    addMessage('bot', 'Olá! Bem-vindo à Papelaria Digital! 👋\n\nSou seu assistente virtual e estou aqui para ajudá-lo com todos os seus produtos de papelaria. Posso ajudá-lo a:\n\n• Consultar nosso catálogo de produtos\n• Fazer orçamentos\n• Processar pedidos\n• Calcular frete\n• Gerar pagamento via PIX\n\nQual produto você está procurando hoje?');
});

// Event listeners
chatForm.addEventListener('submit', handleSubmit);
resetBtn.addEventListener('click', resetConversation);

// Handle form submission
async function handleSubmit(e) {
    e.preventDefault();
    
    const message = messageInput.value.trim();
    if (!message || isLoading) return;
    
    // Add user message to chat
    addMessage('user', message);
    
    // Clear input and show loading
    messageInput.value = '';
    setLoading(true);
    
    try {
        // Send message to backend
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                message: message,
                session_id: localStorage.getItem('chat_session_id')
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            // Add bot response to chat
            addMessage('bot', data.response);
            
            // Check if response contains PIX information
            if (data.response.includes('PIX GERADO') || data.response.includes('Link de pagamento')) {
                showPixModal(data.response);
            }
        } else {
            addMessage('bot', 'Desculpe, ocorreu um erro. Tente novamente.');
        }
        
    } catch (error) {
        console.error('Error sending message:', error);
        addMessage('bot', 'Desculpe, ocorreu um erro de conexão. Verifique sua internet e tente novamente.');
    } finally {
        setLoading(false);
        messageInput.focus();
    }
}

// Add message to chat
function addMessage(sender, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const currentTime = new Date().toLocaleTimeString('pt-BR', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    
    const avatar = sender === 'user' ? 
        '<i class="fas fa-user"></i>' : 
        '<i class="fas fa-robot"></i>';
    
    // Format content for better display
    const formattedContent = formatMessageContent(content);
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            ${formattedContent}
            <div class="message-time">${currentTime}</div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

// Format message content for better display
function formatMessageContent(content) {
    // Convert line breaks to HTML
    content = content.replace(/\n/g, '<br>');
    
    // Format bold text
    content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Format URLs
    content = content.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" class="text-decoration-none">$1</a>');
    
    // Format PIX information with special styling
    if (content.includes('RESUMO DO PEDIDO') || content.includes('PAGAMENTO PIX')) {
        content = addPixStyling(content);
    }
    
    return content;
}

// Add special styling for PIX information
function addPixStyling(content) {
    // Add styling for PIX sections
    content = content.replace(/💳 \*\*PAGAMENTO PIX GERADO:\*\*/g, 
        '<div class="pix-info"><h6>💳 PAGAMENTO PIX GERADO:</h6>');
    
    content = content.replace(/🔗 \*\*Link de pagamento:\*\* (https?:\/\/[^\s]+)/g, 
        '<div class="pix-link"><strong>🔗 Link de pagamento:</strong><br><a href="$1" target="_blank">$1</a></div></div>');
    
    return content;
}

// Show PIX modal with payment information
function showPixModal(response) {
    const pixContent = document.getElementById('pixContent');
    
    // Extract PIX information from response
    const pixUrlMatch = response.match(/🔗 \*\*Link de pagamento:\*\* (https?:\/\/[^\s]+)/);
    const totalMatch = response.match(/\*\*Total: R\$ ([\d,\.]+)\*\*/);
    
    let modalContent = `
        <div class="pix-details text-center">
            <h5><i class="fas fa-qrcode me-2"></i>Pagamento PIX Gerado com Sucesso!</h5>
            <p>Seu pedido foi processado. Para finalizar a compra, realize o pagamento via PIX:</p>
    `;
    
    if (totalMatch) {
        modalContent += `<div class="alert alert-info">
            <strong>Valor Total: R$ ${totalMatch[1]}</strong>
        </div>`;
    }
    
    if (pixUrlMatch) {
        modalContent += `
            <div class="pix-code">
                <strong>Link de Pagamento:</strong><br>
                <a href="${pixUrlMatch[1]}" target="_blank" class="btn btn-success mt-2">
                    <i class="fas fa-external-link-alt me-2"></i>Abrir Link de Pagamento
                </a>
            </div>
        `;
    }
    
    modalContent += `
            <div class="mt-3">
                <small class="text-muted">
                    <i class="fas fa-clock me-1"></i>
                    Após a confirmação do pagamento, seu pedido será processado em até 2 dias úteis.
                </small>
            </div>
        </div>
    `;
    
    pixContent.innerHTML = modalContent;
    successModal.show();
}

// Set loading state
function setLoading(loading) {
    isLoading = loading;
    sendBtn.disabled = loading;
    
    if (loading) {
        loadingIndicator.classList.remove('d-none');
        sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    } else {
        loadingIndicator.classList.add('d-none');
        sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
    }
    
    scrollToBottom();
}

// Scroll to bottom of chat
function scrollToBottom() {
    setTimeout(() => {
        const chatWrapper = document.querySelector('.chat-wrapper');
        if (chatWrapper) {
            chatWrapper.scrollTop = chatWrapper.scrollHeight;
        }
    }, 100);
}

// Reset conversation
async function resetConversation() {
    if (isLoading) return;
    
    try {
        const response = await fetch('/reset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (response.ok) {
            // Create new session ID
            localStorage.setItem('chat_session_id', 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now());
            
            // Clear chat messages
            chatMessages.innerHTML = '';
            
            // Add welcome message back
            setTimeout(() => {
                addMessage('bot', 'Conversa reiniciada! 🔄\n\nOlá novamente! Como posso ajudá-lo hoje?');
            }, 500);
            
            // Focus input
            messageInput.focus();
        }
    } catch (error) {
        console.error('Error resetting conversation:', error);
        addMessage('bot', 'Erro ao reiniciar conversa. Recarregue a página.');
    }
}

// Handle enter key in input
messageInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
    }
});

// Auto-resize input based on content
messageInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
});

// Handle visibility change to refocus input
document.addEventListener('visibilitychange', function() {
    if (!document.hidden && !isLoading) {
        setTimeout(() => messageInput.focus(), 100);
    }
});

// Error handling for unhandled promise rejections
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    if (!isLoading) {
        addMessage('bot', 'Ocorreu um erro inesperado. Por favor, tente novamente.');
    }
});

// Service worker registration (for potential PWA features)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        // Service worker can be added later for offline functionality
        console.log('Service Worker support detected');
    });
}

// Handle online/offline status
window.addEventListener('online', function() {
    console.log('Connection restored');
    if (chatMessages.lastElementChild?.textContent?.includes('erro de conexão')) {
        addMessage('bot', 'Conexão restaurada! ✅ Você pode continuar nossa conversa.');
    }
});

window.addEventListener('offline', function() {
    console.log('Connection lost');
    addMessage('bot', 'Parece que você ficou offline. ⚠️ Verifique sua conexão com a internet.');
});

// Utility function to validate CPF (Brazilian tax ID)
function validateCPF(cpf) {
    cpf = cpf.replace(/[^\d]+/g, '');
    if (cpf.length !== 11 || !!cpf.match(/(\d)\1{10}/)) return false;
    
    let sum = 0;
    let remainder;
    
    for (let i = 1; i <= 9; i++) {
        sum += parseInt(cpf.substring(i - 1, i)) * (11 - i);
    }
    
    remainder = (sum * 10) % 11;
    if (remainder === 10 || remainder === 11) remainder = 0;
    if (remainder !== parseInt(cpf.substring(9, 10))) return false;
    
    sum = 0;
    for (let i = 1; i <= 10; i++) {
        sum += parseInt(cpf.substring(i - 1, i)) * (12 - i);
    }
    
    remainder = (sum * 10) % 11;
    if (remainder === 10 || remainder === 11) remainder = 0;
    if (remainder !== parseInt(cpf.substring(10, 11))) return false;
    
    return true;
}

// Format currency for display
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

// Format phone number for display
function formatPhone(phone) {
    phone = phone.replace(/\D/g, '');
    if (phone.length === 11) {
        return phone.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
    } else if (phone.length === 10) {
        return phone.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3');
    }
    return phone;
}

// Format CEP (Brazilian postal code)
function formatCEP(cep) {
    cep = cep.replace(/\D/g, '');
    if (cep.length === 8) {
        return cep.replace(/(\d{5})(\d{3})/, '$1-$2');
    }
    return cep;
}

console.log('Papelaria Digital Chat System loaded successfully! 🚀');
