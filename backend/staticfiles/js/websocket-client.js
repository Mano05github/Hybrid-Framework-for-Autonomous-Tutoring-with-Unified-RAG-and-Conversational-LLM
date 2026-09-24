/**
 * WebSocket Client for Vaathiyar Backend
 * Handles real-time communication for voice assistant and learning sessions
 */

class WebSocketClient {
    constructor() {
        this.ws = null;
        this.sessionId = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // Start with 1 second
        this.isConnecting = false;
        this.isManualClose = false;
        
        // Callbacks
        this.onMessageCallback = null;
        this.onAudioCallback = null;
        this.onBinaryMessageCallback = null;
        this.onConnectCallback = null;
        this.onDisconnectCallback = null;
        this.onErrorCallback = null;
    }

    /**
     * Connect to WebSocket server
     */
    connect(sessionId) {
        if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
            console.warn('WebSocket is already connected or connecting');
            return;
        }

        this.sessionId = sessionId;
        this.isConnecting = true;
        this.isManualClose = false;

        // Determine WebSocket protocol (ws:// or wss://)
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        const wsURL = `${protocol}//${host}/ws/learn/${sessionId}/`;

        console.log(`Connecting to WebSocket: ${wsURL}`);

        try {
            this.ws = new WebSocket(wsURL);
            this.setupEventHandlers();
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.isConnecting = false;
            this.handleReconnect();
        }
    }

    /**
     * Setup WebSocket event handlers
     */
    setupEventHandlers() {
        this.ws.onopen = () => {
            console.log('WebSocket connected successfully');
            this.isConnecting = false;
            this.reconnectAttempts = 0;
            this.reconnectDelay = 1000;
            
            if (this.onConnectCallback) {
                this.onConnectCallback();
            }
        };

        this.ws.onmessage = (event) => {
            this.handleMessage(event);
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.isConnecting = false;
            
            if (this.onErrorCallback) {
                this.onErrorCallback(error);
            }
        };

        this.ws.onclose = (event) => {
            console.log('WebSocket closed:', event.code, event.reason);
            this.isConnecting = false;
            
            if (this.onDisconnectCallback) {
                this.onDisconnectCallback(event);
            }

            // Attempt to reconnect if not manually closed
            if (!this.isManualClose && this.reconnectAttempts < this.maxReconnectAttempts) {
                this.handleReconnect();
            }
        };
    }

    /**
     * Handle incoming messages
     */
    handleMessage(event) {
        // Check if message is binary (audio data)
        if (event.data instanceof Blob) {
            // Convert Blob to ArrayBuffer for audio playback
            event.data.arrayBuffer().then(arrayBuffer => {
                if (this.onAudioCallback) {
                    this.onAudioCallback(arrayBuffer);
                }
                if (this.onBinaryMessageCallback) {
                    this.onBinaryMessageCallback(arrayBuffer);
                }
            });
        } else {
            // Text message (JSON)
            try {
                const data = JSON.parse(event.data);
                if (this.onMessageCallback) {
                    this.onMessageCallback(data);
                }
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error);
            }
        }
    }

    /**
     * Handle reconnection with exponential backoff
     */
    handleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            return;
        }

        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        
        console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

        setTimeout(() => {
            if (this.sessionId) {
                this.connect(this.sessionId);
            }
        }, delay);
    }

    /**
     * Send text message (JSON)
     */
    sendMessage(data) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.error('WebSocket is not connected');
            return false;
        }

        try {
            const message = typeof data === 'string' ? data : JSON.stringify(data);
            this.ws.send(message);
            return true;
        } catch (error) {
            console.error('Failed to send message:', error);
            return false;
        }
    }

    /**
     * Send audio data (binary)
     */
    sendAudio(audioBlob) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.error('WebSocket is not connected');
            return false;
        }

        try {
            this.ws.send(audioBlob);
            return true;
        } catch (error) {
            console.error('Failed to send audio:', error);
            return false;
        }
    }

    /**
     * Send audio buffer (ArrayBuffer or Uint8Array)
     */
    sendBinary(audioBuffer) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.error('WebSocket is not connected');
            return false;
        }

        try {
            this.ws.send(audioBuffer);
            return true;
        } catch (error) {
            console.error('Failed to send audio buffer:', error);
            return false;
        }
    }

    /**
     * Disconnect WebSocket
     */
    disconnect() {
        this.isManualClose = true;
        
        if (this.ws) {
            this.ws.close(1000, 'Client disconnecting');
            this.ws = null;
        }
        
        this.sessionId = null;
        this.reconnectAttempts = 0;
    }

    /**
     * Check if WebSocket is connected
     */
    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }

    /**
     * Get connection state
     */
    getState() {
        if (!this.ws) return 'CLOSED';
        
        switch (this.ws.readyState) {
            case WebSocket.CONNECTING:
                return 'CONNECTING';
            case WebSocket.OPEN:
                return 'OPEN';
            case WebSocket.CLOSING:
                return 'CLOSING';
            case WebSocket.CLOSED:
                return 'CLOSED';
            default:
                return 'UNKNOWN';
        }
    }

    // ==================== Callback Setters ====================

    /**
     * Set callback for text messages
     */
    onMessage(callback) {
        this.onMessageCallback = callback;
    }

    /**
     * Set callback for audio messages
     */
    onAudio(callback) {
        this.onAudioCallback = callback;
    }

    /**binary messages (including audio)
     */
    onBinaryMessage(callback) {
        this.onBinaryMessageCallback = callback;
    }

    /**
     * Set callback for 
     * Set callback for connection established
     */
    onConnect(callback) {
        this.onConnectCallback = callback;
    }

    /**
     * Set callback for disconnection
     */
    onDisconnect(callback) {
        this.onDisconnectCallback = callback;
    }

    /**
     * Set callback for errors
     */
    onError(callback) {
        this.onErrorCallback = callback;
    }
}

// Create global instance
window.wsClient = new WebSocketClient();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WebSocketClient;
}
