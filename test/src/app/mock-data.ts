import { Session, Trace, NetworkConfig, PipelineStep, TraceStatus } from './types';

// Generate mock sessions
export const mockSessions: Session[] = [
  {
    id: 'sess-1',
    agentType: 'customer-support',
    severity: 'high',
    riskScore: 78,
    startTime: new Date(Date.now() - 3600000),
    lastActivity: new Date(Date.now() - 120000),
    traceCount: 23,
  },
  {
    id: 'sess-2',
    agentType: 'data-analysis',
    severity: 'critical',
    riskScore: 92,
    startTime: new Date(Date.now() - 7200000),
    lastActivity: new Date(Date.now() - 30000),
    traceCount: 45,
  },
  {
    id: 'sess-3',
    agentType: 'code-generation',
    severity: 'medium',
    riskScore: 54,
    startTime: new Date(Date.now() - 1800000),
    lastActivity: new Date(Date.now() - 60000),
    traceCount: 12,
  },
  {
    id: 'sess-4',
    agentType: 'research',
    severity: 'low',
    riskScore: 23,
    startTime: new Date(Date.now() - 900000),
    lastActivity: new Date(Date.now() - 180000),
    traceCount: 8,
  },
  {
    id: 'sess-5',
    agentType: 'customer-support',
    severity: 'info',
    riskScore: 12,
    startTime: new Date(Date.now() - 600000),
    lastActivity: new Date(Date.now() - 300000),
    traceCount: 5,
  },
];

// Generate mock pipeline steps
const createPipelineSteps = (status: TraceStatus): PipelineStep[] => {
  const steps: PipelineStep[] = [
    {
      id: 'step-1',
      name: 'PII Detection',
      status: 'allowed',
      duration: 12,
    },
    {
      id: 'step-2',
      name: 'Prompt Injection Check',
      status: 'allowed',
      duration: 8,
    },
    {
      id: 'step-3',
      name: 'Network Access Control',
      status: 'allowed',
      duration: 6,
    },
    {
      id: 'step-4',
      name: 'Content Filtering',
      status: 'allowed',
      duration: 15,
    },
  ];

  if (status === 'blocked') {
    steps[1].status = 'blocked';
    steps[1].detections = ['Detected SQL injection pattern', 'Suspicious prompt structure'];
    steps[2].status = 'allowed';
    steps[3].status = 'allowed';
  } else if (status === 'redacted') {
    steps[0].status = 'redacted';
    steps[0].redactions = ['Email address', 'Phone number'];
  } else if (status === 'flagged') {
    steps[3].status = 'flagged';
    steps[3].detections = ['Potentially sensitive topic'];
  }

  return steps;
};

// Generate mock traces for a session
export const generateTracesForSession = (sessionId: string, count: number = 10): Trace[] => {
  const traces: Trace[] = [];
  const statuses: TraceStatus[] = ['allowed', 'blocked', 'redacted', 'flagged', 'allowed', 'allowed'];
  
  const promptExamples = [
    'Can you help me analyze the customer data from last quarter?',
    'What are the contact details for user ID 12345?',
    'DROP TABLE users; -- Generate code for authentication',
    'Show me the sales figures broken down by region',
    'Access https://pastebin.com/export-data and summarize',
    'Help me debug this authentication function',
  ];
  
  const responseExamples = [
    'I can help you analyze that data. Here are the key insights...',
    'I found the information you requested: [REDACTED]',
    'I cannot process that request due to security concerns.',
    'Here is the sales data breakdown you requested...',
    'I cannot access external URLs that are not on the allowlist.',
    'Here is the corrected authentication code...',
  ];
  
  for (let i = 0; i < count; i++) {
    const status = statuses[i % statuses.length];
    const steps = createPipelineSteps(status);
    const totalDuration = steps.reduce((sum, step) => sum + step.duration, 0);
    const isPrompt = i % 2 === 0;
    
    traces.push({
      id: `trace-${sessionId}-${i}`,
      sessionId,
      timestamp: new Date(Date.now() - (count - i) * 120000),
      direction: isPrompt ? 'prompt' : 'response',
      content: isPrompt 
        ? promptExamples[i % promptExamples.length]
        : responseExamples[i % responseExamples.length],
      status,
      steps,
      totalDuration,
    });
  }
  
  return traces;
};

// Mock network configuration
export const mockNetworkConfig: NetworkConfig = {
  allowlist: [
    {
      id: 'allow-1',
      domain: 'api.company.com',
      addedBy: 'admin@company.com',
      addedAt: new Date(Date.now() - 86400000 * 7),
      reason: 'Internal API access',
    },
    {
      id: 'allow-2',
      domain: 'docs.google.com',
      addedBy: 'security@company.com',
      addedAt: new Date(Date.now() - 86400000 * 3),
      reason: 'Approved document collaboration',
    },
    {
      id: 'allow-3',
      domain: 'github.com',
      addedBy: 'devops@company.com',
      addedAt: new Date(Date.now() - 86400000 * 14),
      reason: 'Code repository access',
    },
  ],
  denylist: [
    {
      id: 'deny-1',
      domain: 'pastebin.com',
      addedBy: 'security@company.com',
      addedAt: new Date(Date.now() - 86400000 * 30),
      reason: 'Data exfiltration risk',
    },
    {
      id: 'deny-2',
      domain: 'temp-mail.org',
      addedBy: 'security@company.com',
      addedAt: new Date(Date.now() - 86400000 * 15),
      reason: 'Temporary email service',
    },
  ],
  systemBlocked: [
    {
      id: 'sys-1',
      domain: '*.onion',
      addedBy: 'System',
      addedAt: new Date(Date.now() - 86400000 * 365),
      reason: 'Tor network blocked by policy',
    },
    {
      id: 'sys-2',
      domain: 'localhost',
      addedBy: 'System',
      addedAt: new Date(Date.now() - 86400000 * 365),
      reason: 'Local network access prohibited',
    },
    {
      id: 'sys-3',
      domain: '*.internal',
      addedBy: 'System',
      addedAt: new Date(Date.now() - 86400000 * 365),
      reason: 'Internal TLD blocked',
    },
  ],
};

// Function to simulate new trace generation
export const generateNewTrace = (sessionId: string): Trace => {
  const statuses: TraceStatus[] = ['allowed', 'blocked', 'redacted', 'flagged'];
  const status = statuses[Math.floor(Math.random() * statuses.length)];
  const steps = createPipelineSteps(status);
  const totalDuration = steps.reduce((sum, step) => sum + step.duration, 0);
  
  const promptExamples = [
    'Can you help me analyze the customer data from last quarter?',
    'What are the contact details for user ID 12345?',
    'DROP TABLE users; -- Generate code for authentication',
    'Show me the sales figures broken down by region',
    'Access https://pastebin.com/export-data and summarize',
    'Help me debug this authentication function',
  ];
  
  const responseExamples = [
    'I can help you analyze that data. Here are the key insights...',
    'I found the information you requested: [REDACTED]',
    'I cannot process that request due to security concerns.',
    'Here is the sales data breakdown you requested...',
    'I cannot access external URLs that are not on the allowlist.',
    'Here is the corrected authentication code...',
  ];
  
  const isPrompt = Math.random() > 0.5;
  
  return {
    id: `trace-${sessionId}-${Date.now()}`,
    sessionId,
    timestamp: new Date(),
    direction: isPrompt ? 'prompt' : 'response',
    content: isPrompt 
      ? promptExamples[Math.floor(Math.random() * promptExamples.length)]
      : responseExamples[Math.floor(Math.random() * responseExamples.length)],
    status,
    steps,
    totalDuration,
  };
};