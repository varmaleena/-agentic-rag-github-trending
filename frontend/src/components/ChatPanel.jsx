import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, ArrowRight } from 'lucide-react';

export default function ChatPanel() {
  const [messages, setMessages] = useState([
    {
      sender: 'bot',
      text: "Welcome to **Agentic RAG Studio**.\n\nAsk questions about trending GitHub repositories. The system fetches real-time repo data every 15 minutes, embeds text into Qdrant, and runs a self-evaluating LangGraph loop.",
      eval_score: null
    }
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [activeNode, setActiveNode] = useState(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);

  const samplePrompts = [
    "Explain Qdrant vector search and Ollama integration",
    "What are top Android hardware & ADK repositories?",
    "Show trending Python AI agent frameworks"
  ];

  useEffect(() => {
    const wsUrl = `ws://${window.location.hostname}:8000/ws/chat`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => console.log('WS Connected');
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'node_transition') {
          setActiveNode(data.node);
        } else if (data.type === 'stream_start') {
          setIsStreaming(true);
          setMessages(prev => [...prev, { sender: 'bot', text: '', eval_score: null }]);
        } else if (data.type === 'token') {
          setMessages(prev => {
            if (prev.length === 0) return prev;
            const lastIndex = prev.length - 1;
            const lastMsg = prev[lastIndex];
            if (lastMsg && lastMsg.sender === 'bot') {
              return [...prev.slice(0, lastIndex), { ...lastMsg, text: lastMsg.text + data.content }];
            }
            return prev;
          });
        } else if (data.type === 'stream_end') {
          setIsStreaming(false);
        } else if (data.type === 'node_transition' && data.node === 'evaluate') {
          setActiveNode(null);
          if (data.eval_score) {
            setMessages(prev => {
              if (prev.length === 0) return prev;
              const lastIndex = prev.length - 1;
              const lastMsg = prev[lastIndex];
              if (lastMsg && lastMsg.sender === 'bot') {
                return [...prev.slice(0, lastIndex), { ...lastMsg, eval_score: data.eval_score }];
              }
              return prev;
            });
          }
        }
      } catch (err) {
        console.error('WS Error:', err);
      }
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN) ws.close();
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  const handleSend = (textToSend) => {
    const query = textToSend || inputQuery;
    if (!query.trim() || isStreaming) return;

    setMessages(prev => [...prev, { sender: 'user', text: query }]);

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ query }));
    }

    if (!textToSend) setInputQuery('');
  };

  const graphNodes = [
    { key: 'route_query', label: 'Route' },
    { key: 'retrieve', label: 'Retrieve' },
    { key: 'grade_documents', label: 'Grade' },
    { key: 'generate', label: 'Generate' },
    { key: 'evaluate', label: 'Evaluate' }
  ];

  return (
    <div className="flex flex-col h-full max-h-full bg-black border border-zinc-800 rounded-lg overflow-hidden shadow-2xl min-h-0">
      
      {/* Minimal Pipeline Strip */}
      <div className="px-5 py-3 border-b border-zinc-800/80 bg-zinc-950 flex items-center justify-between shrink-0">
        <span className="text-[10px] font-mono font-semibold text-zinc-400 uppercase tracking-widest">
          LangGraph Execution Pipeline
        </span>

        <div className="flex items-center space-x-1.5">
          {graphNodes.map((node) => {
            const isActive = activeNode === node.key;
            return (
              <span
                key={node.key}
                className={`text-[10px] px-2.5 py-1 rounded font-mono border transition-all ${
                  isActive
                    ? 'bg-white text-black font-bold border-white shadow-sm'
                    : 'bg-zinc-900 border-zinc-800 text-zinc-500'
                }`}
              >
                {node.label}
              </span>
            );
          })}
        </div>
      </div>

      {/* Black & White Scrollable Chat Feed with min-h-0 fix */}
      <div className="flex-1 min-h-0 p-6 overflow-y-auto space-y-4 scrollbar-thin scrollbar-thumb-zinc-800">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex items-start space-x-3 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.sender === 'bot' && (
              <div className="w-7 h-7 rounded bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-100 shrink-0 mt-0.5">
                <Bot className="w-3.5 h-3.5" />
              </div>
            )}

            <div className={`max-w-[80%] rounded-lg p-4 text-xs leading-relaxed ${
              msg.sender === 'user'
                ? 'bg-white text-black font-medium shadow-sm'
                : 'bg-zinc-900/90 border border-zinc-800 text-zinc-200 font-sans'
            }`}>
              <div className="whitespace-pre-wrap">{msg.text}</div>

              {msg.eval_score && (
                <div className="mt-3 pt-2 border-t border-zinc-800 flex items-center justify-between text-[10px] font-mono text-zinc-400">
                  <span>Self-Eval Score</span>
                  <span className="text-white font-bold bg-zinc-800 px-2 py-0.5 rounded border border-zinc-700">
                    {msg.eval_score} / 1.0
                  </span>
                </div>
              )}
            </div>

            {msg.sender === 'user' && (
              <div className="w-7 h-7 rounded bg-white text-black flex items-center justify-center font-bold shrink-0 mt-0.5">
                <User className="w-3.5 h-3.5" />
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Section */}
      <div className="p-4 border-t border-zinc-800 bg-zinc-950 space-y-3 shrink-0">
        {/* Sample Prompt Chips */}
        <div className="flex items-center gap-2 overflow-x-auto">
          {samplePrompts.map((prompt, i) => (
            <button
              key={i}
              onClick={() => handleSend(prompt)}
              disabled={isStreaming}
              className="text-[11px] font-mono bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 px-3 py-1.5 rounded transition-all flex items-center gap-1 shrink-0"
            >
              <span className="truncate max-w-[200px]">{prompt}</span>
              <ArrowRight className="w-3 h-3 text-zinc-500 shrink-0" />
            </button>
          ))}
        </div>

        {/* Input Bar */}
        <div className="flex items-center space-x-2">
          <input
            type="text"
            className="flex-1 bg-black border border-zinc-800 focus:border-white rounded px-4 py-2.5 text-xs text-white placeholder-zinc-500 focus:outline-none transition-all font-mono"
            placeholder="Type query..."
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            disabled={isStreaming}
          />
          <button
            onClick={() => handleSend()}
            disabled={isStreaming || !inputQuery.trim()}
            className="px-4 py-2.5 bg-white text-black hover:bg-zinc-200 text-xs font-semibold rounded shadow-sm disabled:opacity-40 transition-all flex items-center gap-1 font-mono shrink-0"
          >
            <span>SEND</span>
            <Send className="w-3 h-3" />
          </button>
        </div>
      </div>

    </div>
  );
}
