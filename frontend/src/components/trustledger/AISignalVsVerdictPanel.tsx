import React from "react";
import { Sparkles, ShieldCheck, AlertOctagon, Lock } from "lucide-react";
import { AISignalBadge } from "./AISignalBadge";
import { StatusBadge } from "./StatusBadge";
import type { DecisionInvestigation } from "../../data/mock/investigations";

interface AISignalVsVerdictPanelProps {
  investigation: DecisionInvestigation;
}

export const AISignalVsVerdictPanel: React.FC<AISignalVsVerdictPanelProps> = ({
  investigation,
}) => {
  return (
    <div className="space-y-3">
      {/* Deterministic Override Banner (when AI & TrustLedger disagree!) */}
      {investigation.is_override && (
        <div className="p-3 bg-verdict-block/10 border border-verdict-block/40 rounded-card flex items-center justify-between shadow-glowBlock animate-pulse">
          <div className="flex items-center gap-2 text-xs font-mono font-bold text-verdict-block uppercase tracking-wider">
            <AlertOctagon className="h-5 w-5" />
            <span>AI RECOMMENDATION DID NOT OVERRIDE SAFETY POLICY</span>
          </div>
          <span className="text-[11px] font-mono text-text-muted hidden sm:inline">Level 2 Hard Safety Precedence</span>
        </div>
      )}

      {/* Side-by-Side Comparison Container */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Left: AI Contextual Signal */}
        <div className="bg-background-surface/80 border border-accent-ai/30 rounded-card p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-border-subtle pb-2">
            <div className="flex items-center gap-2 text-xs font-mono font-bold text-accent-ai uppercase">
              <Sparkles className="h-4 w-4" />
              <span>AI CONTEXTUAL SIGNAL (ADVISORY)</span>
            </div>
            <span className="text-[10px] font-mono text-text-muted">{investigation.ai_model_id}</span>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <AISignalBadge recommendation={investigation.ai_recommendation} confidence={investigation.ai_confidence} />
              <span className="text-xs font-mono text-text-muted">Model Confidence: {Math.round(investigation.ai_confidence * 100)}%</span>
            </div>

            <div className="p-3 bg-background-primary rounded-control border border-border-subtle space-y-1">
              <span className="text-[10px] font-mono text-text-muted uppercase">Contextual Reasoning:</span>
              <p className="text-xs font-mono text-text-secondary leading-relaxed">
                "{investigation.ai_reasoning}"
              </p>
            </div>
          </div>

          <div className="text-[11px] font-mono text-text-muted italic">
            * Note: AI Signal is non-authoritative and serves as secondary reasoning input.
          </div>
        </div>

        {/* Right: Authoritative TrustLedger Verdict */}
        <div className="bg-background-surface/90 border border-border-active rounded-card p-4 space-y-3 shadow-panel">
          <div className="flex items-center justify-between border-b border-border-subtle pb-2">
            <div className="flex items-center gap-2 text-xs font-mono font-bold text-text-primary uppercase">
              <ShieldCheck className="h-4 w-4 text-accent-infra" />
              <span>TRUSTLEDGER VERDICT (AUTHORITATIVE)</span>
            </div>
            <span className="text-[10px] font-mono text-accent-infra font-bold">DECISION GATE V1</span>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <StatusBadge verdict={investigation.verdict} size="lg" />
              <span className="text-xs font-mono font-bold text-text-primary">Rule {investigation.decision_rule}</span>
            </div>

            <div className="p-3 bg-background-primary rounded-control border border-border-subtle space-y-1">
              <span className="text-[10px] font-mono text-text-muted uppercase">Primary Decision Reason:</span>
              <p className="text-xs font-mono text-text-primary font-semibold leading-relaxed">
                {investigation.primary_reason}
              </p>
            </div>
          </div>

          <div className="text-[11px] font-mono text-text-secondary flex items-center gap-1.5">
            <Lock className="h-3.5 w-3.5 text-accent-infra" />
            <span>Execution Boundary: <strong className="text-text-primary uppercase">{investigation.execution_status}</strong></span>
          </div>
        </div>
      </div>
    </div>
  );
};
