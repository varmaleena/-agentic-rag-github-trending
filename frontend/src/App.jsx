import React, { useState } from 'react';
import ChatPanel from './components/ChatPanel';
import Dashboard from './components/Dashboard';
import { Bot, LayoutDashboard, MessageSquare } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('chat');

  return (
    <div className="flex flex-col h-screen max-h-screen bg-black text-white font-sans antialiased selection:bg-white selection:text-black overflow-hidden">
      
      {/* Black & White Header */}
      <header className="flex items-center justify-between px-6 py-3 border-b border-zinc-800 bg-black shrink-0">
        <div className="flex items-center space-x-3">
          <div className="w-7 h-7 rounded bg-white text-black font-bold flex items-center justify-center shadow-sm">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-xs font-mono font-bold tracking-widest text-white uppercase">Agentic RAG Studio</h1>
            <p className="text-[10px] font-mono text-zinc-500">GitHub Trending Repos • LangGraph • AWS Bedrock • Qdrant</p>
          </div>
        </div>

        {/* Black & White Minimal Tab Bar */}
        <div className="flex items-center space-x-1 bg-zinc-950 p-1 rounded border border-zinc-800 font-mono">
          <button
            onClick={() => setActiveTab('chat')}
            className={`flex items-center space-x-1.5 px-3 py-1 rounded text-xs font-semibold transition-all ${
              activeTab === 'chat'
                ? 'bg-white text-black'
                : 'text-zinc-400 hover:text-white'
            }`}
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span>Chat Assistant</span>
          </button>
          
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`flex items-center space-x-1.5 px-3 py-1 rounded text-xs font-semibold transition-all ${
              activeTab === 'dashboard'
                ? 'bg-white text-black'
                : 'text-zinc-400 hover:text-white'
            }`}
          >
            <LayoutDashboard className="w-3.5 h-3.5" />
            <span>System Analytics</span>
          </button>
        </div>
      </header>

      {/* Main Container with min-h-0 fix for inner scrolling */}
      <main className="flex-1 min-h-0 p-5 overflow-hidden bg-black">
        <div className="h-full max-w-7xl mx-auto min-h-0">
          {activeTab === 'chat' ? (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 h-full min-h-0">
              <div className="lg:col-span-2 h-full min-h-0">
                <ChatPanel />
              </div>
              <div className="hidden lg:block h-full min-h-0">
                <Dashboard />
              </div>
            </div>
          ) : (
            <div className="h-full min-h-0">
              <Dashboard />
            </div>
          )}
        </div>
      </main>

    </div>
  );
}
