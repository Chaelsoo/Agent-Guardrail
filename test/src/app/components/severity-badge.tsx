import { SeverityLevel } from '../types';

interface SeverityBadgeProps {
  severity: SeverityLevel;
  size?: 'sm' | 'md';
}

const severityColors: Record<SeverityLevel, string> = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#3b82f6',
  info: '#64748b',
};

export function SeverityBadge({ severity, size = 'sm' }: SeverityBadgeProps) {
  const color = severityColors[severity];
  const textSize = size === 'sm' ? 'text-[10px]' : 'text-[11px]';
  const padding = size === 'sm' ? 'px-1.5 py-0.5' : 'px-2 py-1';
  
  return (
    <span
      className={`inline-flex items-center ${padding} rounded uppercase tracking-wider ${textSize}`}
      style={{
        backgroundColor: `${color}20`,
        color: color,
      }}
    >
      {severity}
    </span>
  );
}
