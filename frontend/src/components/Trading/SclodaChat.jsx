import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FaPaperPlane, FaTimes, FaUserTie, FaUserCircle } from 'react-icons/fa';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import './SclodaChat.css';

const sclodaApi = axios.create({ baseURL: '/api/v1/scloda', withCredentials: true });

const SclodaChat = ({ isOpen, onClose, onOpen, contextAsset = null }) => {
    const [messages, setMessages] = useState([
        { role: 'assistant', content: "Hi! I'm Scloda, your AI market assistant. What would you like to know about trading?" }
    ]);
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isTyping]);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim()) return;

        const userMsg = input.trim();
        setInput('');

        // Add user message
        const newMessages = [...messages, { role: 'user', content: userMsg }];
        setMessages(newMessages);
        setIsTyping(true);

        try {
            // Build prompt — always instruct Scloda to reply in English
            const langPrefix = '[IMPORTANT: Always respond in English, regardless of the language this message is written in.] ';
            const contextPrefix = contextAsset ? `[Context: Viewing ${contextAsset.label}] ` : '';
            const prompt = `${langPrefix}${contextPrefix}${userMsg}`;

            const res = await sclodaApi.post('/message', {
                message: prompt,
                history: messages.slice(-5) // Send last 5 for context
            });

            setMessages(prev => [...prev, { role: 'assistant', content: res.data.response }]);
        } catch (err) {
            console.error('Scloda chat error:', err);
            const apiMessage = err.response?.data?.response
                || err.response?.data?.message
                || err.response?.data?.error
                || 'Oops! I had a connection error trying to answer that.';
            setMessages(prev => [...prev, { role: 'assistant', content: apiMessage }]);
        } finally {
            setIsTyping(false);
        }
    };

    return (
        <AnimatePresence>
            {isOpen ? (
                <motion.div
                    key="chat-window"
                    className="scloda-chat-window"
                    initial={{ opacity: 0, scale: 0.9, y: 20 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.9, y: 20 }}
                    transition={{ type: "spring", stiffness: 300, damping: 25 }}
                >
                    <div className="scloda-chat-header">
                        <div className="scloda-chat-title">
                            <div className="scloda-avatar-wrapper">
                                <FaUserTie size={16} />
                                <div className="scloda-online-indicator"></div>
                            </div>
                            Ask Scloda
                        </div>
                        <button className="scloda-chat-close" onClick={onClose} aria-label="Close Chat">
                            <FaTimes size={14} />
                        </button>
                    </div>

                    <div className="scloda-chat-body">
                        {messages.map((msg, i) => (
                            <div key={i} className={`scloda-message-row ${msg.role}`}>
                                <div className="scloda-message-avatar">
                                    {msg.role === 'assistant' ? <FaUserTie size={14} /> : <FaUserCircle size={14} />}
                                </div>
                                <div className={`scloda-message-bubble ${msg.role}`}>
                                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                                </div>
                            </div>
                        ))}
                        {isTyping && (
                            <div className="scloda-message-row assistant">
                                <div className="scloda-message-avatar">
                                    <FaUserTie size={14} />
                                </div>
                                <div className="scloda-message-bubble assistant typing">
                                    <div className="typing-dot"></div>
                                    <div className="typing-dot"></div>
                                    <div className="typing-dot"></div>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    <form className="scloda-chat-input-area" onSubmit={handleSend}>
                        <input
                            type="text"
                            className="scloda-input"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Ask about the market..."
                            autoFocus
                        />
                        <button
                            type="submit"
                            className="scloda-send-btn"
                            disabled={!input.trim() || isTyping}
                        >
                            <FaPaperPlane size={14} />
                        </button>
                    </form>
                </motion.div>
            ) : (
                <motion.button
                    key="fab"
                    className="scloda-chat-fab"
                    initial={{ scale: 0, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0, opacity: 0 }}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={onOpen}
                    aria-label="Open Scloda Chat"
                >
                    <FaUserTie size={24} />
                </motion.button>
            )}
        </AnimatePresence>
    );
};

export default SclodaChat;
