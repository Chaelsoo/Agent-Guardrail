import { useState, useEffect } from 'react';
import { Plus, Trash2, Ban } from 'lucide-react';

const BASE = 'http://localhost:8765/v1';

const KNOWN_TOOLS = [
  'read', 'write', 'edit', 'apply_patch',
  'exec', 'process',
  'web_search', 'web_fetch',
  'memory_search', 'memory_get',
  'sessions_list', 'sessions_history', 'sessions_send', 'sessions_spawn',
  'subagents', 'session_status',
  'browser', 'canvas',
  'message', 'cron', 'gateway', 'nodes', 'agents_list',
  'image', 'tts',
];

export function ToolsPage() {
  const [denylist, setDenylist] = useState<string[]>([]);
  const [input, setInput] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);

  const fetchDenylist = async () => {
    try {
      const res = await fetch(`${BASE}/tools/denylist`);
      const data = await res.json();
      setDenylist(data.tools ?? []);
    } catch { /* ignore */ }
  };

  useEffect(() => { fetchDenylist(); }, []);

  const handleInputChange = (value: string) => {
    setInput(value);
    if (value.trim()) {
      setSuggestions(
        KNOWN_TOOLS.filter(
          (t) => t.includes(value.toLowerCase()) && !denylist.includes(t)
        ).slice(0, 6)
      );
    } else {
      setSuggestions([]);
    }
  };

  const handleAdd = async (tool: string) => {
    const name = tool.trim().toLowerCase();
    if (!name || denylist.includes(name)) return;
    try {
      await fetch(`${BASE}/tools/denylist`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tool_name: name }),
      });
      setInput('');
      setSuggestions([]);
      await fetchDenylist();
    } catch { /* ignore */ }
  };

  const handleRemove = async (tool: string) => {
    try {
      await fetch(`${BASE}/tools/denylist/${encodeURIComponent(tool)}`, { method: 'DELETE' });
      await fetchDenylist();
    } catch { /* ignore */ }
  };

  return (
    <div className="flex-1 overflow-hidden flex flex-col">
      <div className="border-b border-[#1e293b] bg-[#0f1419] px-6 py-4">
        <h1 className="text-[15px] text-[#e4e7eb] mb-1">Tool Access Control</h1>
        <p className="text-[11px] text-[#94a3b8]">
          Block specific tools from being called by the agent
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-2xl">
          {/* Add form */}
          <div className="bg-[#12171f] border border-[#1e293b] rounded p-4 mb-6">
            <h3 className="text-[12px] uppercase tracking-wider text-[#94a3b8] mb-4">
              Add to Denylist
            </h3>
            <div className="relative">
              <input
                type="text"
                value={input}
                onChange={(e) => handleInputChange(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAdd(input)}
                placeholder="tool name (e.g. exec, write)"
                className="w-full px-3 py-2 bg-[#0a0e1a] border border-[#1e293b] rounded text-[13px] text-[#e4e7eb] placeholder:text-[#64748b] focus:outline-none focus:ring-1 focus:ring-[#3b82f6]"
              />
              {suggestions.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-[#12171f] border border-[#1e293b] rounded z-10 overflow-hidden">
                  {suggestions.map((s) => (
                    <button
                      key={s}
                      onClick={() => handleAdd(s)}
                      className="w-full text-left px-3 py-2 text-[12px] text-[#94a3b8] hover:bg-[#1e293b] hover:text-[#e4e7eb] font-mono transition-colors"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}
            </div>
            <button
              onClick={() => handleAdd(input)}
              disabled={!input.trim()}
              className="mt-3 flex items-center gap-2 px-4 py-2 bg-[#ef4444] text-white rounded text-[12px] hover:bg-[#dc2626] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Plus className="w-4 h-4" />
              Block Tool
            </button>
          </div>

          {/* Denylist */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-[12px] uppercase tracking-wider text-[#94a3b8]">
                Blocked Tools
              </h3>
              <span className="text-[11px] text-[#64748b]">{denylist.length} tools</span>
            </div>

            {denylist.length === 0 ? (
              <div className="bg-[#12171f] border border-[#1e293b] rounded p-8 text-center">
                <p className="text-[12px] text-[#64748b]">No tools blocked — all tools are permitted</p>
              </div>
            ) : (
              <div className="space-y-2">
                {denylist.map((tool) => (
                  <div
                    key={tool}
                    className="bg-[#12171f] border border-[#1e293b] rounded px-4 py-3 flex items-center justify-between"
                  >
                    <div className="flex items-center gap-3">
                      <Ban className="w-3.5 h-3.5 text-[#ef4444] flex-shrink-0" />
                      <code className="text-[13px] text-[#e4e7eb] font-mono">{tool}</code>
                    </div>
                    <button
                      onClick={() => handleRemove(tool)}
                      className="p-2 text-[#94a3b8] hover:text-[#ef4444] transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
