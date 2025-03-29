class RAWebUI {
    constructor() {
        this.messageHistory = [];
        this.clientId = this.generateClientId();
        this.setupElements();
        this.setupEventListeners();
        this.connectWebSocket();
        this.currentPhase = null;
    }

    generateClientId() {
        // Generate a random UUID for client identification
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    setupElements() {
        this.userInput = document.getElementById('user-input');
        this.sendButton = document.getElementById('send-button');
        this.chatMessages = document.getElementById('chat-messages');
        this.streamOutput = document.getElementById('stream-output');
        this.historyList = document.getElementById('history-list');
        this.statusIndicator = document.createElement('div');
        this.statusIndicator.className = 'status-indicator';
        this.statusIndicator.textContent = 'Connecting...';
        this.chatMessages.appendChild(this.statusIndicator);
    }

    setupEventListeners() {
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
    }

    async connectWebSocket() {
        try {
            // Get the server port from the response header or default to 8000
            const serverPort = document.querySelector('meta[name="server-port"]')?.content || '8000';
            
            // Construct WebSocket URL using the server port and client ID
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.hostname}:${serverPort}/ws/${this.clientId}`;
            console.log('Attempting to connect to WebSocket URL:', wsUrl);
            
            console.log('Creating new WebSocket connection...');
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket connection established successfully');
                this.statusIndicator.textContent = 'Connected';
                this.statusIndicator.className = 'status-indicator connected';
                this.sendButton.disabled = false;
            };

            this.ws.onclose = () => {
                console.log('Disconnected from WebSocket server');
                this.statusIndicator.textContent = 'Disconnected. Reconnecting...';
                this.statusIndicator.className = 'status-indicator disconnected';
                this.sendButton.disabled = true;
                setTimeout(() => this.connectWebSocket(), 5000);
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.statusIndicator.textContent = 'Connection error';
                this.statusIndicator.className = 'status-indicator error';
            };

            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleServerMessage(data);
            };
        } catch (error) {
            console.error('Failed to connect to WebSocket:', error);
            this.statusIndicator.textContent = 'Connection failed. Retrying...';
            this.statusIndicator.className = 'status-indicator error';
            setTimeout(() => this.connectWebSocket(), 5000);
        }
    }

    handleServerMessage(data) {
        console.log('Received message:', data);
        
        switch (data.type) {
            case 'connection_established':
                this.statusIndicator.textContent = `Connected (ID: ${data.client_id})`;
                this.statusIndicator.className = 'status-indicator connected';
                this.sendButton.disabled = false;
                break;
                
            case 'task_received':
                this.appendMessage(`Task received by server: ${data.content.task}`, 'info');
                break;
                
            case 'phase_started':
                this.currentPhase = data.phase;
                this.appendMessage(`Starting phase: ${data.phase}`, 'phase');
                this.updatePhaseIndicator(data.phase, 'in-progress');
                break;
                
            case 'research_complete':
            case 'planning_complete':
            case 'implementation_complete':
                const phase = data.type.replace('_complete', '');
                this.appendMessage(`${phase.charAt(0).toUpperCase() + phase.slice(1)} complete`, 'phase');
                this.updatePhaseIndicator(phase, 'complete');
                if (data.content && Object.keys(data.content).length > 0) {
                    const contentStr = JSON.stringify(data.content, null, 2);
                    this.appendMessage(contentStr, 'system');
                }
                break;
                
            case 'task_complete':
                this.appendMessage('Task completed successfully', 'success');
                this.currentPhase = null;
                this.sendButton.disabled = false;
                break;
                
            case 'task_cancelled':
                this.appendMessage('Task cancelled', 'info');
                this.currentPhase = null;
                this.sendButton.disabled = false;
                break;
                
            case 'error':
                this.appendMessage(`Error: ${data.content}`, 'error');
                this.sendButton.disabled = false;
                break;
                
            case 'config_updated':
                this.appendMessage(`Configuration updated: ${JSON.stringify(data.content)}`, 'info');
                break;
                
            // Legacy message types for backward compatibility
            case 'stream_start':
                this.streamOutput.textContent = '';
                this.streamOutput.style.display = 'block';
                break;
                
            case 'stream_end':
                this.streamOutput.style.display = 'none';
                this.addToHistory(data.request);
                break;
                
            case 'chunk':
                this.handleChunk(data.chunk);
                break;
                
            default:
                console.warn('Unknown message type:', data.type);
                break;
        }
    }

    updatePhaseIndicator(phase, status) {
        // Remove any existing phase indicators
        const existingIndicators = document.querySelectorAll('.phase-indicator');
        existingIndicators.forEach(indicator => {
            indicator.remove();
        });
        
        // Create a new phase indicator
        const indicator = document.createElement('div');
        indicator.className = `phase-indicator ${status} ${phase}`;
        indicator.innerHTML = `
            <span class="phase-name">${phase}</span>
            <span class="phase-status">${status}</span>
        `;
        
        // Add a cancel button if the phase is in progress
        if (status === 'in-progress') {
            const cancelButton = document.createElement('button');
            cancelButton.className = 'cancel-button';
            cancelButton.textContent = 'Cancel';
            cancelButton.addEventListener('click', () => this.cancelTask());
            indicator.appendChild(cancelButton);
        }
        
        this.chatMessages.appendChild(indicator);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    cancelTask() {
        if (!this.currentPhase) return;
        
        try {
            this.ws.send(JSON.stringify({ type: 'cancel' }));
            this.appendMessage('Cancelling task...', 'info');
        } catch (error) {
            console.error('Error sending cancel request:', error);
            this.appendMessage(`Error cancelling task: ${error.message}`, 'error');
        }
    }

    handleChunk(chunk) {
        if (chunk.agent && chunk.agent.messages) {
            chunk.agent.messages.forEach(msg => {
                if (msg.content) {
                    if (Array.isArray(msg.content)) {
                        msg.content.forEach(content => {
                            if (content.type === 'text' && content.text.trim()) {
                                this.appendMessage(content.text.trim(), 'system');
                            }
                        });
                    } else if (msg.content.trim()) {
                        this.appendMessage(msg.content.trim(), 'system');
                    }
                }
            });
        } else if (chunk.tools && chunk.tools.messages) {
            chunk.tools.messages.forEach(msg => {
                if (msg.status === 'error' && msg.content) {
                    this.appendMessage(msg.content.trim(), 'error');
                }
            });
        }
    }

    appendMessage(content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        messageDiv.textContent = content;
        this.chatMessages.appendChild(messageDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    addToHistory(request) {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';
        historyItem.textContent = request.slice(0, 50) + (request.length > 50 ? '...' : '');
        historyItem.title = request;
        historyItem.addEventListener('click', () => {
            this.userInput.value = request;
            this.userInput.focus();
        });
        this.historyList.insertBefore(historyItem, this.historyList.firstChild);
        this.messageHistory.push(request);
    }

    sendMessage() {
        console.log('Send button clicked');
        const message = this.userInput.value.trim();
        console.log('Message content:', message);
        
        if (!message) {
            console.log('Message is empty, not sending');
            return;
        }

        console.log('WebSocket state:', this.ws.readyState);
        if (this.ws.readyState !== WebSocket.OPEN) {
            console.error('WebSocket is not connected');
            this.appendMessage('Error: WebSocket is not connected. Trying to reconnect...', 'error');
            this.connectWebSocket();
            return;
        }

        try {
            console.log('Sending message to server');
            this.appendMessage(message, 'user');
            
            // Use the 'task' message type for the enhanced server
            const payload = { type: 'task', content: message };
            console.log('Payload:', payload);
            
            this.ws.send(JSON.stringify(payload));
            console.log('Message sent successfully');
            
            this.userInput.value = '';
            this.sendButton.disabled = true;
        } catch (error) {
            console.error('Error sending message:', error);
            this.appendMessage(`Error sending message: ${error.message}`, 'error');
            this.sendButton.disabled = false;
        }
    }
}

// Initialize the UI when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.raWebUI = new RAWebUI();
});