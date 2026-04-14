import { Session } from '../types';
import { SeverityBadge } from './severity-badge';
import { AgentIcon } from './agent-icon';
import { formatDistanceToNow } from 'date-fns';

interface SessionListProps {
  sessions: Session[];
  selectedSessionId: string | null;
  onSelectSession: (sessionId: string) => void;
}

const agentTypeLabels: Record<string, string> = {
  'customer-support': 'Customer Support',
  'data-analysis': 'Data Analysis',
  'code-generation': 'Code Generation',
  'research': 'Research',
};

export function SessionList({ sessions, selectedSessionId, onSelectSession }: SessionListProps) {
  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-[#1e293b]">
        <h2 className="text-[13px] uppercase tracking-wide text-[#94a3b8]">
          Active Sessions
        </h2>
        <p className="text-[11px] text-[#64748b] mt-0.5">
          {sessions.length} running
        </p>
      </div>
      
      <div className="flex-1 overflow-y-auto">
        {sessions.map((session) => (
          <button
            key={session.id}
            onClick={() => onSelectSession(session.id)}
            className={`
              w-full text-left px-4 py-3 border-b border-[#1e293b] transition-colors
              ${selectedSessionId === session.id 
                ? 'bg-[#1e293b]' 
                : 'hover:bg-[#1e293b]/50'
              }
            `}
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <AgentIcon type={session.agentType} className="w-4 h-4 text-[#94a3b8]" />
                <span className="text-[13px] text-[#e4e7eb]">
                  {agentTypeLabels[session.agentType]}
                </span>
              </div>
              <SeverityBadge severity={session.severity} />
            </div>
            
            <div className="flex items-center justify-between text-[11px] text-[#94a3b8]">
              <span>Risk Score: {session.riskScore}</span>
              <span>{session.traceCount} traces</span>
            </div>
            
            <div className="mt-1 text-[10px] text-[#64748b]">
              Updated {formatDistanceToNow(session.lastActivity, { addSuffix: true })}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}