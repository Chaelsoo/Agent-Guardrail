import { Trace } from '../types';
import { StatusBadge } from './status-badge';
import {
  ArrowRight, Clock,
  Inbox, Shield, Send, RefreshCw, Box, ScanLine, Wrench, Brain,
  type LucideIcon,
} from 'lucide-react';
import { format } from 'date-fns';

interface TraceTimelineProps {
  traces: Trace[];
}

function spanIcon(name: string, isTool: boolean): LucideIcon {
  const base = name.replace(/:.*$/, '').trim().toLowerCase();
  if (base.includes('judge') || base.includes('llm')) return Brain;
  if (isTool) {
    if (base === 'sandbox')        return Box;
    if (base.includes('intent'))   return ScanLine;
    return Wrench;
  }
  if (base === 'input received')   return Inbox;
  if (base === 'input gate')       return Shield;
  if (base === 'output gate')      return Send;
  if (base === 'turn ended')       return RefreshCw;
  return Shield;
}

function iconColor(status: string, isTool: boolean): string {
  if (status === 'blocked')  return '#ef4444';
  if (status === 'hijacked') return '#ef4444';
  if (status === 'redacted') return '#f59e0b';
  if (status === 'uncertain') return '#f59e0b';
  if (status === 'flagged')  return '#eab308';
  if (status === 'aligned')  return '#10b981';
  return isTool ? '#6366f1' : '#10b981';
}

function formatSpanName(name: string): string {
  const toolPre = name.match(/^tool_pre:?(.*)$/);
  if (toolPre) return toolPre[1] ? `tool · ${toolPre[1]} (pre)` : 'tool pre';
  const toolPost = name.match(/^tool_post:?(.*)$/);
  if (toolPost) return toolPost[1] ? `tool · ${toolPost[1]} (post)` : 'tool post';
  const withTool = name.match(/^(.+):([^:]+)$/);
  if (withTool) {
    const phase = withTool[1].toLowerCase().replace(/\s+verification$/i, '').trim();
    return `${withTool[2]} · ${phase}`;
  }
  return name.replace(/_/g, ' ');
}

function stateLabel(status: string): string {
  if (status === 'blocked')  return 'blocked';
  if (status === 'hijacked') return 'HIJACKED';
  if (status === 'redacted') return 'redacted';
  if (status === 'uncertain') return 'UNCERTAIN';
  if (status === 'flagged')  return 'flagged';
  if (status === 'aligned')  return 'ALIGNED';
  return 'pass';
}

export function TraceTimeline({ traces }: TraceTimelineProps) {
  return (
    <div className="space-y-4">
      {traces.map((trace) => (
        <div
          key={trace.id}
          className={`bg-[#12171f] border rounded p-4 transition-colors ${
            !trace.finalized && Date.now() - trace.timestamp.getTime() < 30_000
              ? 'border-[#3b82f6]/40'
              : 'border-[#1e293b]'
          }`}
        >
          {/* Header */}
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              <StatusBadge status={trace.status} />
              {!trace.finalized && Date.now() - trace.timestamp.getTime() < 30_000 && (
                <div className="flex items-center gap-1.5 text-[11px] text-[#3b82f6]">
                  <div className="w-1.5 h-1.5 rounded-full bg-[#3b82f6] animate-pulse" />
                  processing…
                </div>
              )}
            </div>
            <div className="flex items-center gap-4 text-[11px] text-[#94a3b8]">
              <div className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                <span>{trace.totalDuration}ms</span>
              </div>
              <span>{format(trace.timestamp, 'HH:mm:ss')}</span>
            </div>
          </div>

          {/* Prompt content */}
          <div className="mb-3 text-[12px] text-[#94a3b8] font-mono leading-relaxed">
            {trace.content}
          </div>

          {/* LLM output */}
          {trace.llmOutput && (
            <div className="mb-3 border-t border-[#1e293b] pt-3">
              <div className="text-[10px] uppercase tracking-wider text-[#64748b] mb-1">Response</div>
              <div className="text-[12px] text-[#c4b5fd] font-mono whitespace-pre-wrap leading-relaxed">
                {trace.llmOutput}
              </div>
            </div>
          )}

          {/* Pipeline steps */}
          {trace.steps.length > 0 && (
            <div className="space-y-2">
              <div className="text-[10px] uppercase tracking-wider text-[#64748b] mb-2">
                Pipeline
              </div>
              {trace.steps.map((step, index) => {
                const isTool = step.isTool ?? false;
                const Icon   = spanIcon(step.name, isTool);
                const color  = iconColor(step.status, isTool);
                const state  = stateLabel(step.status);
                const detail = step.detail ? `${state} · ${step.detail}` : state;

                return (
                  <div key={step.id} className={`flex items-start gap-3 ${isTool ? 'ml-4' : ''}`}>
                    {/* Icon + connector */}
                    <div className="flex flex-col items-center pt-0.5">
                      <Icon className="w-3.5 h-3.5 flex-shrink-0" style={{ color }} />
                      {index < trace.steps.length - 1 && (
                        <div className="w-px flex-1 min-h-[20px] bg-[#1e293b] mt-1" />
                      )}
                    </div>

                    {/* Step content */}
                    <div className="flex-1 pb-3">
                      <div className="flex items-center justify-between mb-1">
                        <span className={`text-[12px] ${isTool ? 'text-[#a5b4fc]' : 'text-[#e4e7eb]'}`}>
                          {formatSpanName(step.name)}
                        </span>
                        <span className="text-[10px] text-[#64748b]">{step.duration}ms</span>
                      </div>

                      <div className="mt-1 text-[11px] font-mono text-[#94a3b8] break-all">
                        {detail}
                      </div>

                      {step.detections && step.detections.length > 0 && (
                        <div className="mt-1 space-y-1">
                          {step.detections.map((d, i) => (
                            <div key={i} className="flex items-start gap-2 text-[11px]">
                              <ArrowRight className="w-3 h-3 text-[#ef4444] mt-0.5 flex-shrink-0" />
                              <span className="text-[#ef4444]">{d}</span>
                            </div>
                          ))}
                        </div>
                      )}

                      {step.redactions && step.redactions.length > 0 && (
                        <div className="mt-1 space-y-1">
                          {step.redactions.map((r, i) => (
                            <div key={i} className="flex items-start gap-2 text-[11px]">
                              <ArrowRight className="w-3 h-3 text-[#f59e0b] mt-0.5 flex-shrink-0" />
                              <span className="text-[#f59e0b]">Redacted: {r}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
