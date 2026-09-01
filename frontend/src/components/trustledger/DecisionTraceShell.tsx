import React from "react";
import { CheckCircle2, AlertTriangle, ShieldX, Info, ArrowRight } from "lucide-react";

export interface TraceStep {
  stage: "CONTRACT" | "EVIDENCE" | "POLICY" | "CONSISTENCY" | "RISK" | "AI CONTEXT" | "DECISION";
  status: "PASS" | "WARNING" | "FAIL" | "INFO";
  summary: string;
}

interface DecisionTraceShellProps {
  steps?: TraceStep[];
}

const DEFAULT_STEPS: TraceStep[] = [
  { stage: "CONTRACT", status: "PASS", summary: "Canonical DecisionRequest payload structure valid." },
  { stage: "EVIDENCE", status: "PASS", summary: "Attached evidence artifacts verified & fresh." },
  { stage: "POLICY", status: "PASS", summary: "Deterministic hard merchant policy thresholds met." },
  { stage: "CONSISTENCY", status: "PASS", summary: "Cross-ledger transaction state consistent." },
  { stage: "RISK", status: "PASS", summary: "Financial exposure risk assessed as LOW (0.165)." },
  { stage: "AI CONTEXT", status: "INFO", summary: "AI Contextual Verifier signal: SUPPORT." },
  { stage: "DECISION", status: "PASS", summary: "Decision Gate verdict: APPROVE (Rule TL-DG-010)." },
];

export const DecisionTraceShell: React.FC<DecisionTraceShellProps> = ({
  steps = DEFAULT_STEPS,
}) => {
  const statusStyles = {
    PASS: { icon: CheckCircle2, color: "text-verdict-approve", bg: "bg-verdict-approve/10 border-verdict-approve/30" },
    WARNING: { icon: AlertTriangle, color: "text-verdict-review", bg: "bg-verdict-review/10 border-verdict-review/30" },
    FAIL: { icon: ShieldX, color: "text-verdict-block", bg: "bg-verdict-block/10 border-verdict-block/30" },
    INFO: { icon: Info, color: "text-accent-ai", bg: "bg-accent-ai/10 border-accent-ai/30" },
  };

  return (
    <div className="w-full bg-background-surface/80 border border-border-subtle rounded-card p-4 space-y-3">
      <div className="flex items-center justify-between border-b border-border-subtle pb-2">
        <span className="text-xs font-mono font-bold text-text-primary tracking-wider uppercase flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-accent-infra animate-ping" />
          DETERMINISTIC VERIFICATION PIPELINE TRACE
        </span>
        <span className="text-[11px] font-mono text-text-muted">7-STAGE AUTHORITATIVE VERIFICATION</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-7 gap-2 pt-1">
        {steps.map((step, idx) => {
          const st = statusStyles[step.status] || statusStyles.PASS;
          const Icon = st.icon;
          return (
            <div key={idx} className="flex flex-col relative group">
              <div className={`p-2.5 rounded-lg border flex flex-col justify-between space-y-1.5 transition-all ${st.bg}`}>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono font-bold text-text-secondary">{step.stage}</span>
                  <Icon className={`h-3.5 w-3.5 ${st.color}`} />
                </div>
                <p className="text-[11px] text-text-muted line-clamp-2 leading-tight">{step.summary}</p>
              </div>
              {idx < steps.length - 1 && (
                <div className="hidden md:block absolute -right-2 top-1/2 -translate-y-1/2 z-10 text-border-active">
                  <ArrowRight className="h-3 w-3" />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
