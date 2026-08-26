import React, { useState, useEffect } from 'react';
import { Clock, Zap, Award, RefreshCw, GitBranch, Server } from 'lucide-react';

export default function Dashboard() {
  const [stats, setStats] = useState({
    last_ingested_at: null,
    total_queries: 0,
    avg_latency_seconds: 0,
    avg_eval_score: 0,
    recent_queries: []
  });
  const [isLoading, setIsLoading] = useState(false);

  const fetchStats = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/dashboard/stats');
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (err) {
      console.log('Dashboard stats fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  const formatTime = (ts) => {
    if (!ts) return 'N/A';
    const date = new Date(ts.toString().length === 10 ? ts * 1000 : ts);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  return (
    <div className="flex flex-col h-full bg-black border border-zinc-800 rounded-lg p-6 shadow-2xl overflow-y-auto space-y-6">
      
      {/* Header */}
      <div className="flex items-center justify-between border-b border-zinc-800 pb-4">
        <div>
          <h2 className="text-xs font-mono font-semibold text-white uppercase tracking-widest flex items-center gap-2">
            <Server className="w-3.5 h-3.5" />
            System Analytics & Telemetry
          </h2>
          <p className="text-[11px] text-zinc-500 font-mono mt-0.5">Real-time status of LangGraph engine & vector index</p>
        </div>
        <button
          onClick={fetchStats}
          disabled={isLoading}
          className="p-1.5 rounded bg-zinc-900 border border-zinc-800 text-zinc-300 hover:bg-zinc-800 transition-all"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        
        {/* Ingestion Status */}
        <div className="bg-zinc-950 border border-zinc-800 rounded p-4 font-mono">
          <div className="flex items-center justify-between text-zinc-400 text-[11px] mb-2">
            <span>Last Ingestion</span>
            <Clock className="w-3.5 h-3.5" />
          </div>
          <div className="text-sm font-bold text-white">
            {formatTime(stats.last_ingested_at)}
          </div>
          <span className="text-[10px] text-zinc-400 bg-zinc-900 px-2 py-0.5 rounded border border-zinc-800 mt-2 inline-block">
            Scheduled (15m)
          </span>
        </div>

        {/* Avg Latency */}
        <div className="bg-zinc-950 border border-zinc-800 rounded p-4 font-mono">
          <div className="flex items-center justify-between text-zinc-400 text-[11px] mb-2">
            <span>Avg Latency</span>
            <Zap className="w-3.5 h-3.5" />
          </div>
          <div className="text-sm font-bold text-white">
            {stats.avg_latency_seconds}s
          </div>
          <span className="text-[10px] text-zinc-500 mt-2 block">
            Streaming Latency
          </span>
        </div>

        {/* Eval Score */}
        <div className="bg-zinc-950 border border-zinc-800 rounded p-4 font-mono">
          <div className="flex items-center justify-between text-zinc-400 text-[11px] mb-2">
            <span>Self-Eval Score</span>
            <Award className="w-3.5 h-3.5" />
          </div>
          <div className="text-sm font-bold text-white">
            {stats.avg_eval_score} <span className="text-[10px] text-zinc-500 font-normal">/ 1.0</span>
          </div>
          <span className="text-[10px] text-zinc-400 mt-2 block">
            Threshold: ≥ 0.70
          </span>
        </div>

      </div>

      {/* Query Trace History */}
      <div className="bg-zinc-950 border border-zinc-800 rounded p-4 flex-1">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xs font-mono font-semibold text-zinc-300 flex items-center gap-2">
            <GitBranch className="w-3.5 h-3.5" />
            Query Trace Log
          </h3>
          <span className="text-[10px] bg-zinc-900 border border-zinc-800 px-2 py-0.5 rounded text-zinc-400 font-mono">
            {stats.total_queries} Total Queries
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-zinc-300">
            <thead className="bg-zinc-900 text-zinc-400 font-mono text-[10px] uppercase">
              <tr>
                <th className="px-3 py-2">Query</th>
                <th className="px-3 py-2">Path</th>
                <th className="px-3 py-2">Retries</th>
                <th className="px-3 py-2">Eval</th>
                <th className="px-3 py-2">Latency</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60 font-mono text-xs">
              {stats.recent_queries.length > 0 ? (
                stats.recent_queries.map((q, idx) => (
                  <tr key={idx} className="hover:bg-zinc-900/60 transition-colors">
                    <td className="px-3 py-2.5 font-medium text-white max-w-xs truncate">{q.query}</td>
                    <td className="px-3 py-2.5 text-[10px]">
                      {q.retries > 0 ? (
                        <span className="px-2 py-0.5 bg-zinc-800 text-zinc-300 border border-zinc-700 rounded">
                          Corrected ({q.retries})
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 bg-zinc-900 text-zinc-400 border border-zinc-800 rounded">
                          Direct
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-2.5 font-mono text-center">{q.retries}</td>
                    <td className="px-3 py-2.5 font-mono text-white font-bold">{q.eval_score}</td>
                    <td className="px-3 py-2.5 font-mono text-zinc-500">{q.latency_seconds}s</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="px-3 py-6 text-center text-zinc-500 text-xs font-mono">
                    No queries logged yet. Ask a question in the Chat Assistant tab to populate telemetry!
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
