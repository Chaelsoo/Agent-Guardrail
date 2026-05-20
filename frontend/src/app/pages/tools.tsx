import { useState, useEffect } from 'react';
import { Plus, Trash2, Ban, Shield, Edit2, ChevronDown, ChevronRight } from 'lucide-react';

const BASE = 'http://localhost:8765/v1';

const KNOWN_TOOLS = [
  'read_file', 'write_file', 'edit', 'apply_patch',
  'bash', 'shell', 'exec', 'process',
  'http_request', 'web_search', 'web_fetch',
  'send_email', 'email',
  'memory_search', 'memory_get',
  'sessions_list', 'sessions_history', 'sessions_send', 'sessions_spawn',
  'subagents', 'session_status',
  'browser', 'canvas',
  'message', 'cron', 'gateway', 'nodes', 'agents_list',
  'image', 'tts',
];

interface PolpRule {
  blocked?: boolean;
  allowed_paths?: string[];
  allowed_domains?: string[];
  blocked_domains?: string[];
  allowed_recipient_domains?: string[];
}

interface PolpProfile {
  [tool_name: string]: PolpRule;
}

export function ToolsPage() {
  const [denylist, setDenylist] = useState<string[]>([]);
  const [input, setInput] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);

  // PoLP state
  const [polpProfile, setPolpProfile] = useState<PolpProfile>({});
  const [editingTool, setEditingTool] = useState<string | null>(null);
  const [expandedTools, setExpandedTools] = useState<Set<string>>(new Set());
  const [newToolName, setNewToolName] = useState('');

  // Form state for editing
  const [editForm, setEditForm] = useState<PolpRule>({});
  const [pathInput, setPathInput] = useState('');
  const [domainInput, setDomainInput] = useState('');

  const fetchDenylist = async () => {
    try {
      const res = await fetch(`${BASE}/tools/denylist`);
      const data = await res.json();
      setDenylist(data.tools ?? []);
    } catch { /* ignore */ }
  };

  const fetchPolpProfile = async () => {
    try {
      const res = await fetch(`${BASE}/polp/profile`);
      const data = await res.json();
      setPolpProfile(data ?? {});
    } catch { /* ignore */ }
  };

  useEffect(() => {
    fetchDenylist();
    fetchPolpProfile();
  }, []);

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

  // PoLP handlers
  const handleStartEditPolp = (tool: string) => {
    setEditingTool(tool);
    setEditForm(polpProfile[tool] || {});
    setPathInput('');
    setDomainInput('');
  };

  const handleCancelEditPolp = () => {
    setEditingTool(null);
    setEditForm({});
  };

  const handleSavePolp = async (tool: string) => {
    try {
      await fetch(`${BASE}/polp/tool/${encodeURIComponent(tool)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editForm),
      });
      await fetchPolpProfile();
      setEditingTool(null);
      setEditForm({});
      setNewToolName('');
    } catch { /* ignore */ }
  };

  const handleDeletePolp = async (tool: string) => {
    if (!confirm(`Remove PoLP rule for ${tool}?`)) return;
    try {
      await fetch(`${BASE}/polp/tool/${encodeURIComponent(tool)}`, { method: 'DELETE' });
      await fetchPolpProfile();
    } catch { /* ignore */ }
  };

  const handleAddPath = () => {
    if (!pathInput.trim()) return;
    setEditForm({
      ...editForm,
      allowed_paths: [...(editForm.allowed_paths || []), pathInput.trim()],
    });
    setPathInput('');
  };

  const handleRemovePath = (index: number) => {
    setEditForm({
      ...editForm,
      allowed_paths: (editForm.allowed_paths || []).filter((_, i) => i !== index),
    });
  };

  const handleAddAllowedDomain = () => {
    if (!domainInput.trim()) return;
    setEditForm({
      ...editForm,
      allowed_domains: [...(editForm.allowed_domains || []), domainInput.trim()],
    });
    setDomainInput('');
  };

  const handleRemoveAllowedDomain = (index: number) => {
    setEditForm({
      ...editForm,
      allowed_domains: (editForm.allowed_domains || []).filter((_, i) => i !== index),
    });
  };

  const handleAddBlockedDomain = () => {
    if (!domainInput.trim()) return;
    setEditForm({
      ...editForm,
      blocked_domains: [...(editForm.blocked_domains || []), domainInput.trim()],
    });
    setDomainInput('');
  };

  const handleRemoveBlockedDomain = (index: number) => {
    setEditForm({
      ...editForm,
      blocked_domains: (editForm.blocked_domains || []).filter((_, i) => i !== index),
    });
  };

  const handleAddRecipientDomain = () => {
    if (!domainInput.trim()) return;
    setEditForm({
      ...editForm,
      allowed_recipient_domains: [...(editForm.allowed_recipient_domains || []), domainInput.trim()],
    });
    setDomainInput('');
  };

  const handleRemoveRecipientDomain = (index: number) => {
    setEditForm({
      ...editForm,
      allowed_recipient_domains: (editForm.allowed_recipient_domains || []).filter((_, i) => i !== index),
    });
  };

  const toggleExpanded = (tool: string) => {
    const newExpanded = new Set(expandedTools);
    if (newExpanded.has(tool)) {
      newExpanded.delete(tool);
    } else {
      newExpanded.add(tool);
    }
    setExpandedTools(newExpanded);
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

          {/* PoLP Granular Rules */}
          <div className="mt-8">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-[12px] uppercase tracking-wider text-[#94a3b8] flex items-center gap-2">
                  <Shield className="w-4 h-4" />
                  Granular Tool Rules (PoLP)
                </h3>
                <p className="text-[10px] text-[#64748b] mt-1">
                  Fine-grained argument-level constraints for tools
                </p>
              </div>
              <span className="text-[11px] text-[#64748b]">{Object.keys(polpProfile).length} rules</span>
            </div>

            {/* Add new rule */}
            {editingTool === '__new__' ? (
              <div className="bg-[#12171f] border border-[#3b82f6] rounded p-4 mb-4">
                <h4 className="text-[11px] uppercase tracking-wider text-[#94a3b8] mb-3">New PoLP Rule</h4>
                <input
                  type="text"
                  value={newToolName}
                  onChange={(e) => setNewToolName(e.target.value)}
                  placeholder="Tool name (e.g. read_file, http_request)"
                  className="w-full px-3 py-2 bg-[#0a0e1a] border border-[#1e293b] rounded text-[13px] text-[#e4e7eb] placeholder:text-[#64748b] focus:outline-none focus:ring-1 focus:ring-[#3b82f6] mb-3"
                />
                {renderRuleEditor()}
                <div className="flex gap-2 mt-3">
                  <button
                    onClick={() => newToolName.trim() && handleSavePolp(newToolName.trim())}
                    disabled={!newToolName.trim()}
                    className="px-4 py-2 bg-[#3b82f6] text-white rounded text-[12px] hover:bg-[#2563eb] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    Save Rule
                  </button>
                  <button
                    onClick={() => { setEditingTool(null); setNewToolName(''); setEditForm({}); }}
                    className="px-4 py-2 bg-[#1e293b] text-[#e4e7eb] rounded text-[12px] hover:bg-[#334155] transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={() => setEditingTool('__new__')}
                className="w-full bg-[#12171f] border border-dashed border-[#1e293b] rounded p-4 mb-4 flex items-center justify-center gap-2 text-[12px] text-[#94a3b8] hover:border-[#3b82f6] hover:text-[#3b82f6] transition-colors"
              >
                <Plus className="w-4 h-4" />
                Add New Tool Rule
              </button>
            )}

            {/* Existing rules */}
            {Object.keys(polpProfile).length === 0 ? (
              <div className="bg-[#12171f] border border-[#1e293b] rounded p-8 text-center">
                <p className="text-[12px] text-[#64748b]">No PoLP rules configured</p>
              </div>
            ) : (
              <div className="space-y-2">
                {Object.entries(polpProfile).map(([tool, rule]) => (
                  <div key={tool} className="bg-[#12171f] border border-[#1e293b] rounded overflow-hidden">
                    {editingTool === tool ? (
                      <div className="p-4">
                        <h4 className="text-[13px] text-[#e4e7eb] font-mono mb-3">{tool}</h4>
                        {renderRuleEditor()}
                        <div className="flex gap-2 mt-3">
                          <button
                            onClick={() => handleSavePolp(tool)}
                            className="px-4 py-2 bg-[#3b82f6] text-white rounded text-[12px] hover:bg-[#2563eb] transition-colors"
                          >
                            Save
                          </button>
                          <button
                            onClick={handleCancelEditPolp}
                            className="px-4 py-2 bg-[#1e293b] text-[#e4e7eb] rounded text-[12px] hover:bg-[#334155] transition-colors"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <>
                        <div className="px-4 py-3 flex items-center justify-between">
                          <div className="flex items-center gap-3 flex-1">
                            <button
                              onClick={() => toggleExpanded(tool)}
                              className="text-[#94a3b8] hover:text-[#e4e7eb] transition-colors"
                            >
                              {expandedTools.has(tool) ? (
                                <ChevronDown className="w-4 h-4" />
                              ) : (
                                <ChevronRight className="w-4 h-4" />
                              )}
                            </button>
                            <Shield className="w-3.5 h-3.5 text-[#3b82f6] flex-shrink-0" />
                            <code className="text-[13px] text-[#e4e7eb] font-mono">{tool}</code>
                            {rule.blocked && (
                              <span className="px-2 py-0.5 bg-[#ef4444]/10 text-[#ef4444] text-[10px] rounded">BLOCKED</span>
                            )}
                          </div>
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleStartEditPolp(tool)}
                              className="p-2 text-[#94a3b8] hover:text-[#3b82f6] transition-colors"
                            >
                              <Edit2 className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleDeletePolp(tool)}
                              className="p-2 text-[#94a3b8] hover:text-[#ef4444] transition-colors"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>

                        {expandedTools.has(tool) && (
                          <div className="px-4 pb-4 pt-0 border-t border-[#1e293b] space-y-2">
                            {rule.blocked && (
                              <div className="text-[11px] text-[#ef4444]">• Tool completely blocked</div>
                            )}
                            {rule.allowed_paths && rule.allowed_paths.length > 0 && (
                              <div>
                                <div className="text-[10px] uppercase text-[#64748b] mb-1">Allowed Paths:</div>
                                {rule.allowed_paths.map((p, i) => (
                                  <div key={i} className="text-[11px] text-[#94a3b8] font-mono">• {p}</div>
                                ))}
                              </div>
                            )}
                            {rule.allowed_domains && rule.allowed_domains.length > 0 && (
                              <div>
                                <div className="text-[10px] uppercase text-[#64748b] mb-1">Allowed Domains:</div>
                                {rule.allowed_domains.map((d, i) => (
                                  <div key={i} className="text-[11px] text-[#94a3b8] font-mono">• {d}</div>
                                ))}
                              </div>
                            )}
                            {rule.blocked_domains && rule.blocked_domains.length > 0 && (
                              <div>
                                <div className="text-[10px] uppercase text-[#64748b] mb-1">Blocked Domains:</div>
                                {rule.blocked_domains.map((d, i) => (
                                  <div key={i} className="text-[11px] text-[#ef4444] font-mono">• {d}</div>
                                ))}
                              </div>
                            )}
                            {rule.allowed_recipient_domains && rule.allowed_recipient_domains.length > 0 && (
                              <div>
                                <div className="text-[10px] uppercase text-[#64748b] mb-1">Allowed Recipient Domains:</div>
                                {rule.allowed_recipient_domains.map((d, i) => (
                                  <div key={i} className="text-[11px] text-[#94a3b8] font-mono">• {d}</div>
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                      </>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );

  function renderRuleEditor() {
    return (
      <div className="space-y-4">
        {/* Blocked toggle */}
        <label className="flex items-center gap-2 text-[12px] text-[#e4e7eb]">
          <input
            type="checkbox"
            checked={editForm.blocked || false}
            onChange={(e) => setEditForm({ ...editForm, blocked: e.target.checked })}
            className="w-4 h-4 rounded border-[#1e293b] bg-[#0a0e1a] text-[#3b82f6] focus:ring-1 focus:ring-[#3b82f6]"
          />
          Block tool completely
        </label>

        {/* Allowed paths (for read_file) */}
        {!editForm.blocked && (
          <>
            <div>
              <div className="text-[11px] text-[#94a3b8] mb-2">Allowed Paths (for read_file):</div>
              {(editForm.allowed_paths || []).map((path, i) => (
                <div key={i} className="flex items-center gap-2 mb-2">
                  <code className="flex-1 px-3 py-1.5 bg-[#0a0e1a] border border-[#1e293b] rounded text-[11px] text-[#e4e7eb] font-mono">
                    {path}
                  </code>
                  <button
                    onClick={() => handleRemovePath(i)}
                    className="p-1 text-[#94a3b8] hover:text-[#ef4444] transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
              <div className="flex gap-2">
                <input
                  type="text"
                  value={pathInput}
                  onChange={(e) => setPathInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAddPath()}
                  placeholder="/home/user/workspace/"
                  className="flex-1 px-3 py-1.5 bg-[#0a0e1a] border border-[#1e293b] rounded text-[11px] text-[#e4e7eb] placeholder:text-[#64748b] focus:outline-none focus:ring-1 focus:ring-[#3b82f6]"
                />
                <button
                  onClick={handleAddPath}
                  className="px-3 py-1.5 bg-[#1e293b] text-[#e4e7eb] rounded text-[11px] hover:bg-[#334155] transition-colors"
                >
                  <Plus className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Allowed domains (for http_request) */}
            <div>
              <div className="text-[11px] text-[#94a3b8] mb-2">Allowed Domains (for http_request):</div>
              {(editForm.allowed_domains || []).map((domain, i) => (
                <div key={i} className="flex items-center gap-2 mb-2">
                  <code className="flex-1 px-3 py-1.5 bg-[#0a0e1a] border border-[#1e293b] rounded text-[11px] text-[#e4e7eb] font-mono">
                    {domain}
                  </code>
                  <button
                    onClick={() => handleRemoveAllowedDomain(i)}
                    className="p-1 text-[#94a3b8] hover:text-[#ef4444] transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
              <div className="flex gap-2">
                <input
                  type="text"
                  value={domainInput}
                  onChange={(e) => setDomainInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAddAllowedDomain()}
                  placeholder="api.company.com"
                  className="flex-1 px-3 py-1.5 bg-[#0a0e1a] border border-[#1e293b] rounded text-[11px] text-[#e4e7eb] placeholder:text-[#64748b] focus:outline-none focus:ring-1 focus:ring-[#3b82f6]"
                />
                <button
                  onClick={handleAddAllowedDomain}
                  className="px-3 py-1.5 bg-[#1e293b] text-[#e4e7eb] rounded text-[11px] hover:bg-[#334155] transition-colors"
                >
                  <Plus className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Blocked domains (for http_request) */}
            <div>
              <div className="text-[11px] text-[#94a3b8] mb-2">Blocked Domains (for http_request):</div>
              {(editForm.blocked_domains || []).map((domain, i) => (
                <div key={i} className="flex items-center gap-2 mb-2">
                  <code className="flex-1 px-3 py-1.5 bg-[#0a0e1a] border border-[#1e293b] rounded text-[11px] text-[#ef4444] font-mono">
                    {domain}
                  </code>
                  <button
                    onClick={() => handleRemoveBlockedDomain(i)}
                    className="p-1 text-[#94a3b8] hover:text-[#ef4444] transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
              <div className="flex gap-2">
                <input
                  type="text"
                  value={domainInput}
                  onChange={(e) => setDomainInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAddBlockedDomain()}
                  placeholder="pastebin.com"
                  className="flex-1 px-3 py-1.5 bg-[#0a0e1a] border border-[#1e293b] rounded text-[11px] text-[#e4e7eb] placeholder:text-[#64748b] focus:outline-none focus:ring-1 focus:ring-[#3b82f6]"
                />
                <button
                  onClick={handleAddBlockedDomain}
                  className="px-3 py-1.5 bg-[#1e293b] text-[#e4e7eb] rounded text-[11px] hover:bg-[#334155] transition-colors"
                >
                  <Plus className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Allowed recipient domains (for send_email) */}
            <div>
              <div className="text-[11px] text-[#94a3b8] mb-2">Allowed Recipient Domains (for send_email):</div>
              {(editForm.allowed_recipient_domains || []).map((domain, i) => (
                <div key={i} className="flex items-center gap-2 mb-2">
                  <code className="flex-1 px-3 py-1.5 bg-[#0a0e1a] border border-[#1e293b] rounded text-[11px] text-[#e4e7eb] font-mono">
                    {domain}
                  </code>
                  <button
                    onClick={() => handleRemoveRecipientDomain(i)}
                    className="p-1 text-[#94a3b8] hover:text-[#ef4444] transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
              <div className="flex gap-2">
                <input
                  type="text"
                  value={domainInput}
                  onChange={(e) => setDomainInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAddRecipientDomain()}
                  placeholder="company.com"
                  className="flex-1 px-3 py-1.5 bg-[#0a0e1a] border border-[#1e293b] rounded text-[11px] text-[#e4e7eb] placeholder:text-[#64748b] focus:outline-none focus:ring-1 focus:ring-[#3b82f6]"
                />
                <button
                  onClick={handleAddRecipientDomain}
                  className="px-3 py-1.5 bg-[#1e293b] text-[#e4e7eb] rounded text-[11px] hover:bg-[#334155] transition-colors"
                >
                  <Plus className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    );
  }
}
