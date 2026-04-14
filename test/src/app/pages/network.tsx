import { useState, useEffect } from 'react';
import { DomainRule } from '../types';
import { Plus, Trash2, Shield, Lock } from 'lucide-react';
import { format } from 'date-fns';

const BASE = 'http://localhost:8765/v1';

function mapDomain(d: any, listType: string, idx: number): DomainRule {
  return {
    id: `${listType}-${d.domain ?? idx}`,
    domain: d.domain ?? d,
    addedBy: 'admin',
    addedAt: d.added_at ? new Date(d.added_at * 1000) : new Date(),
    reason: d.hits != null ? `${d.hits} hits` : undefined,
  };
}

const SYSTEM_BLOCKED: DomainRule[] = [
  { id: 'sys-1', domain: 'localhost', addedBy: 'System', addedAt: new Date(0), reason: 'Local loopback blocked' },
  { id: 'sys-2', domain: '127.0.0.0/8', addedBy: 'System', addedAt: new Date(0), reason: 'Loopback range' },
  { id: 'sys-3', domain: '10.0.0.0/8', addedBy: 'System', addedAt: new Date(0), reason: 'Private network' },
  { id: 'sys-4', domain: '172.16.0.0/12', addedBy: 'System', addedAt: new Date(0), reason: 'Private network' },
  { id: 'sys-5', domain: '192.168.0.0/16', addedBy: 'System', addedAt: new Date(0), reason: 'Private network' },
  { id: 'sys-6', domain: '169.254.169.254', addedBy: 'System', addedAt: new Date(0), reason: 'Cloud metadata endpoint' },
  { id: 'sys-7', domain: '::1', addedBy: 'System', addedAt: new Date(0), reason: 'IPv6 loopback' },
];

export function NetworkPage() {
  const [allowlist, setAllowlist] = useState<DomainRule[]>([]);
  const [denylist, setDenylist] = useState<DomainRule[]>([]);
  const [newDomain, setNewDomain] = useState('');
  const [newReason, setNewReason] = useState('');
  const [activeTab, setActiveTab] = useState<'allowlist' | 'denylist' | 'system'>('allowlist');

  const fetchLists = async () => {
    try {
      const [aRes, dRes] = await Promise.all([
        fetch(`${BASE}/network/allowlist`),
        fetch(`${BASE}/network/denylist`),
      ]);
      const aData = await aRes.json();
      const dData = await dRes.json();
      setAllowlist((aData.domains ?? []).map((d: any, i: number) => mapDomain(d, 'allow', i)));
      setDenylist((dData.domains ?? []).map((d: any, i: number) => mapDomain(d, 'deny', i)));
    } catch { /* ignore */ }
  };

  useEffect(() => { fetchLists(); }, []);

  const handleAddDomain = async (list: 'allowlist' | 'denylist') => {
    if (!newDomain.trim()) return;
    try {
      await fetch(`${BASE}/network/${list}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ domain: newDomain.trim() }),
      });
      setNewDomain('');
      setNewReason('');
      await fetchLists();
    } catch { /* ignore */ }
  };

  const handleRemoveDomain = async (list: 'allowlist' | 'denylist', domain: string) => {
    try {
      await fetch(`${BASE}/network/${list}/${encodeURIComponent(domain)}`, { method: 'DELETE' });
      await fetchLists();
    } catch { /* ignore */ }
  };

  const renderDomainList = (rules: DomainRule[], editable: boolean, listType: 'allowlist' | 'denylist') => {
    if (rules.length === 0) {
      return (
        <div className="bg-[#12171f] border border-[#1e293b] rounded p-8 text-center">
          <p className="text-[12px] text-[#64748b]">No domains in this list</p>
        </div>
      );
    }

    return (
      <div className="space-y-2">
        {rules.map((rule) => (
          <div
            key={rule.id}
            className="bg-[#12171f] border border-[#1e293b] rounded p-4 flex items-start justify-between"
          >
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <code className="text-[13px] text-[#e4e7eb] font-mono">
                  {rule.domain}
                </code>
              </div>
              {rule.reason && (
                <p className="text-[11px] text-[#94a3b8] mb-2">{rule.reason}</p>
              )}
              <div className="text-[10px] text-[#64748b]">
                Added by {rule.addedBy} • {format(rule.addedAt, 'MMM d, yyyy')}
              </div>
            </div>
            {editable && (
              <button
                onClick={() => handleRemoveDomain(listType, rule.domain)}
                className="p-2 text-[#94a3b8] hover:text-[#ef4444] transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="flex-1 overflow-hidden flex flex-col">
      {/* Header */}
      <div className="border-b border-[#1e293b] bg-[#0f1419] px-6 py-4">
        <h1 className="text-[15px] text-[#e4e7eb] mb-1">Network Access Control</h1>
        <p className="text-[11px] text-[#94a3b8]">
          Manage domain allowlist and denylist
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-[#1e293b] bg-[#0f1419] px-6">
        <div className="flex gap-1">
          {[
            { id: 'allowlist' as const, label: 'Allowlist', icon: Shield },
            { id: 'denylist' as const, label: 'Denylist', icon: Shield },
            { id: 'system' as const, label: 'System Blocked', icon: Lock },
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  flex items-center gap-2 px-4 py-3 text-[12px] border-b-2 transition-colors
                  ${activeTab === tab.id
                    ? 'border-[#3b82f6] text-[#e4e7eb]'
                    : 'border-transparent text-[#94a3b8] hover:text-[#e4e7eb]'
                  }
                `}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl">
          {/* Add domain form */}
          {activeTab !== 'system' && (
            <div className="bg-[#12171f] border border-[#1e293b] rounded p-4 mb-6">
              <h3 className="text-[12px] uppercase tracking-wider text-[#94a3b8] mb-4">
                Add Domain
              </h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-[11px] text-[#94a3b8] mb-1.5">Domain</label>
                  <input
                    type="text"
                    value={newDomain}
                    onChange={(e) => setNewDomain(e.target.value)}
                    placeholder="example.com"
                    className="w-full px-3 py-2 bg-[#0a0e1a] border border-[#1e293b] rounded text-[13px] text-[#e4e7eb] placeholder:text-[#64748b] focus:outline-none focus:ring-1 focus:ring-[#3b82f6]"
                  />
                </div>
                <div>
                  <label className="block text-[11px] text-[#94a3b8] mb-1.5">Reason (optional)</label>
                  <input
                    type="text"
                    value={newReason}
                    onChange={(e) => setNewReason(e.target.value)}
                    placeholder="Why is this domain being added?"
                    className="w-full px-3 py-2 bg-[#0a0e1a] border border-[#1e293b] rounded text-[13px] text-[#e4e7eb] placeholder:text-[#64748b] focus:outline-none focus:ring-1 focus:ring-[#3b82f6]"
                  />
                </div>
                <button
                  onClick={() => handleAddDomain(activeTab)}
                  disabled={!newDomain.trim()}
                  className="flex items-center gap-2 px-4 py-2 bg-[#3b82f6] text-white rounded text-[12px] hover:bg-[#2563eb] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  Add to {activeTab === 'allowlist' ? 'Allowlist' : 'Denylist'}
                </button>
              </div>
            </div>
          )}

          {/* Domain list */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-[12px] uppercase tracking-wider text-[#94a3b8]">
                {activeTab === 'allowlist' && 'Allowed Domains'}
                {activeTab === 'denylist' && 'Denied Domains'}
                {activeTab === 'system' && 'System-Level Blocks'}
              </h3>
              <span className="text-[11px] text-[#64748b]">
                {activeTab === 'allowlist' && `${allowlist.length} domains`}
                {activeTab === 'denylist' && `${denylist.length} domains`}
                {activeTab === 'system' && `${SYSTEM_BLOCKED.length} rules`}
              </span>
            </div>

            {activeTab === 'allowlist' && renderDomainList(allowlist, true, 'allowlist')}
            {activeTab === 'denylist' && renderDomainList(denylist, true, 'denylist')}
            {activeTab === 'system' && (
              <div className="space-y-4">
                <div className="bg-[#12171f] border border-[#1e293b] rounded p-4 mb-4">
                  <div className="flex items-start gap-3">
                    <Lock className="w-4 h-4 text-[#64748b] mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-[12px] text-[#94a3b8] mb-1">
                        System-level blocks are enforced by Aegis and cannot be modified from this interface.
                      </p>
                      <p className="text-[11px] text-[#64748b]">
                        Includes loopback, private CIDRs, and cloud metadata endpoints.
                      </p>
                    </div>
                  </div>
                </div>
                {renderDomainList(SYSTEM_BLOCKED, false, 'allowlist')}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
