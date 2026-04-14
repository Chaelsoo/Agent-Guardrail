export type SeverityLevel = 'critical' | 'high' | 'medium' | 'low' | 'info';
export type TraceStatus = 'allowed' | 'blocked' | 'redacted' | 'flagged';
export type AgentType = 'customer-support' | 'data-analysis' | 'code-generation' | 'research';

export interface Session {
  id: string;
  agentType: AgentType;
  severity: SeverityLevel;
  riskScore: number;
  startTime: Date;
  lastActivity: Date;
  traceCount: number;
}

export interface PipelineStep {
  id: string;
  name: string;
  status: TraceStatus;
  duration: number;
  detail?: string;
  detections?: string[];
  redactions?: string[];
  isTool?: boolean;
}

export interface Trace {
  id: string;
  sessionId: string;
  timestamp: Date;
  direction: 'prompt' | 'response';
  content: string;
  status: TraceStatus;
  steps: PipelineStep[];
  totalDuration: number;
  llmOutput?: string;
  finalized: boolean;
}

export interface DomainRule {
  id: string;
  domain: string;
  addedBy: string;
  addedAt: Date;
  reason?: string;
}

export interface NetworkConfig {
  allowlist: DomainRule[];
  denylist: DomainRule[];
  systemBlocked: DomainRule[];
}
