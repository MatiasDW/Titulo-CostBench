import React, { useState, useRef, useEffect } from 'react';
import { FaUserTie, FaTimes, FaPaperPlane } from 'react-icons/fa';
import './SclodaChat.css';

/**
 * SclodaChat - Floating AI chat widget for financial analysis
 */
const SclodaChat = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState([
        {
            role: 'assistant',
            content: '¡Hola! 👋 Soy Scloda, tu analista financiero. Puedo ayudarte a entender datos del mercado chileno: UF, dólar, commodities, criptos y más. ¿En qué te puedo ayudar?'
        }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    // Scroll to bottom when messages change
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // Focus input when chat opens
    useEffect(() => {
        if (isOpen) {
            inputRef.current?.focus();
        }
    }, [isOpen]);

    const sendMessage = async () => {
        if (!input.trim() || loading) return;

        const userMessage = input.trim();
        setInput('');
        setLoading(true);

        // Add user message
        setMessages(prev => [...prev, { role: 'user', content: userMessage }]);

        try {
            // Build history for context (exclude welcome message)
            const history = messages.slice(1).map(m => ({
                role: m.role,
                content: m.content
            }));

            const response = await fetch('/api/v1/scloda/message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: userMessage,
                    history: history
                })
            });

            const data = await response.json();

            // Add assistant response
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: data.response || 'No pude procesar tu mensaje. Intenta de nuevo.'
            }]);

        } catch (error) {
            console.error('Chat error:', error);
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: '😅 Ups, tuve un problema de conexión. Intenta de nuevo.'
            }]);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    // Quick suggestions
    const suggestions = [
        '¿Cuánto vale la UF?',
        '¿Cómo está el dólar?',
        '¿Qué pasó con el cobre?'
    ];

    return (
        <>
            {/* Chat Button */}
            <button
                className={`scloda-chat-button ${isOpen ? 'hidden' : ''}`}
                onClick={() => setIsOpen(true)}
                aria-label="Abrir chat con Scloda"
            >
                <FaUserTie size={24} />
                <span className="scloda-chat-button-label">Pregúntale a Scloda</span>
            </button>

            {/* Chat Window */}
            {isOpen && (
                <div className="scloda-chat-window">
                    {/* Header */}
                    <div className="scloda-chat-header">
                        <div className="scloda-chat-header-info">
                            <div className="scloda-avatar">
                                <FaUserTie size={18} />
                            </div>
                            <div>
                                <h6>Scloda</h6>
                                <small>Analista Financiero AI</small>
                            </div>
                        </div>
                        <button
                            className="scloda-chat-close"
                            onClick={() => setIsOpen(false)}
                            aria-label="Cerrar chat"
                        >
                            <FaTimes size={16} />
                        </button>
                    </div>

                    {/* Messages */}
                    <div className="scloda-chat-messages">
                        {messages.map((msg, idx) => (
                            <div
                                key={idx}
                                className={`scloda-message ${msg.role}`}
                            >
                                {msg.role === 'assistant' && (
                                    <div className="scloda-message-avatar">
                                        <FaUserTie size={12} />
                                    </div>
                                )}
                                <div className="scloda-message-content">
                                    {msg.content}
                                </div>
                            </div>
                        ))}

                        {loading && (
                            <div className="scloda-message assistant">
                                <div className="scloda-message-avatar">
                                    <FaUserTie size={12} />
                                </div>
                                <div className="scloda-message-content scloda-typing">
                                    <span></span>
                                    <span></span>
                                    <span></span>
                                </div>
                            </div>
                        )}

                        <div ref={messagesEndRef} />
                    </div>

                    {/* Quick Suggestions (show only at start) */}
                    {messages.length === 1 && (
                        <div className="scloda-suggestions">
                            {suggestions.map((s, i) => (
                                <button
                                    key={i}
                                    className="scloda-suggestion"
                                    onClick={() => {
                                        setInput(s);
                                        inputRef.current?.focus();
                                    }}
                                >
                                    {s}
                                </button>
                            ))}
                        </div>
                    )}

                    {/* Input */}
                    <div className="scloda-chat-input">
                        <input
                            ref={inputRef}
                            type="text"
                            placeholder="Escribe tu pregunta..."
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyPress={handleKeyPress}
                            disabled={loading}
                        />
                        <button
                            onClick={sendMessage}
                            disabled={!input.trim() || loading}
                            aria-label="Enviar mensaje"
                        >
                            <FaPaperPlane size={14} />
                        </button>
                    </div>
                </div>
            )}
        </>
    );
};

export default SclodaChat;
