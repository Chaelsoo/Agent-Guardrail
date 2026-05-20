import { SessionState } from '../types';

interface StateBadgeProps {
  state: SessionState;
}

const stateStyles: Record<SessionState, { bg: string; text: string; label: string }> = {
  'ACTIVE': {
    bg: 'bg-[#10b981]/10',
    text: 'text-[#10b981]',
    label: 'Active'
  },
  'FLAGGED': {
    bg: 'bg-[#f59e0b]/10',
    text: 'text-[#f59e0b]',
    label: 'Flagged'
  },
  'COMPROMISED': {
    bg: 'bg-[#ef4444]/10',
    text: 'text-[#ef4444]',
    label: 'Compromised'
  }
};

export function StateBadge({ state }: StateBadgeProps) {
  const style = stateStyles[state];

  return (
    <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${style.bg} ${style.text}`}>
      {style.label}
    </span>
  );
}
