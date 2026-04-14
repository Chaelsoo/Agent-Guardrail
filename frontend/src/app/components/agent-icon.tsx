import { Headphones, BarChart3, Code2, Search } from 'lucide-react';
import { AgentType } from '../types';

interface AgentIconProps {
  type: AgentType;
  className?: string;
}

export function AgentIcon({ type, className = "w-4 h-4" }: AgentIconProps) {
  const icons: Record<AgentType, typeof Headphones> = {
    'customer-support': Headphones,
    'data-analysis': BarChart3,
    'code-generation': Code2,
    'research': Search,
  };
  
  const Icon = icons[type];
  return <Icon className={className} />;
}
