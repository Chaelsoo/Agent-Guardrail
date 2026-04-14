import { CheckCircle2, XCircle, AlertTriangle, Flag } from 'lucide-react';
import { TraceStatus } from '../types';

interface StatusBadgeProps {
  status: TraceStatus;
  size?: 'sm' | 'md';
}

const statusConfig: Record<TraceStatus, { color: string; icon: typeof CheckCircle2; label: string }> = {
  allowed: { color: '#10b981', icon: CheckCircle2, label: 'Allowed' },
  blocked: { color: '#ef4444', icon: XCircle, label: 'Blocked' },
  redacted: { color: '#f59e0b', icon: AlertTriangle, label: 'Redacted' },
  flagged: { color: '#eab308', icon: Flag, label: 'Flagged' },
};

export function StatusBadge({ status, size = 'sm' }: StatusBadgeProps) {
  const config = statusConfig[status];
  const Icon = config.icon;
  const iconSize = size === 'sm' ? 'w-3 h-3' : 'w-4 h-4';
  const textSize = size === 'sm' ? 'text-[10px]' : 'text-[11px]';
  const padding = size === 'sm' ? 'px-1.5 py-0.5' : 'px-2 py-1';
  
  return (
    <span
      className={`inline-flex items-center gap-1 ${padding} rounded uppercase tracking-wider ${textSize}`}
      style={{
        backgroundColor: `${config.color}20`,
        color: config.color,
      }}
    >
      <Icon className={iconSize} />
      {config.label}
    </span>
  );
}
