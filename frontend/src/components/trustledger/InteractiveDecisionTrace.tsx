import React, { useState } from "react";
import { CheckCircle2, AlertTriangle, ShieldX, Info, ChevronDown, ChevronUp } from "lucide-react";
import type { DecisionInvestigation } from "../../data/mock/investigations";
import { MoneyDisplay } from "./MoneyDisplay";

interface InteractiveDecisionTraceProps {
  investigation: DecisionInvestigation;
}

export const InteractiveDecisionTrace: React.FC<InteractiveDecisionTraceProps> = ({
  investigation,
}) => {
  const [expandedStage, setExpandedStage] = useState<string | null>("POLICY");

  const toggleStage = (stage: string) => {
    setExpandedStage(expandedStage === stage ? null : stage);
  };

  // Build dynamic pipeline steps based on investigation data
  const steps = [
    {
      id: "CONTRACT",
      label: "1. CONTRACT",
      status: "PASS" as const,
      summary: `Payload valid (${investigation.action_type})`,
      detail: (
        <div className="space-y-1 text-xs font-mono text-text-secondary">
          <div>Contract Schema: <span className="text-text-primary">trustledger.contract.v1</span></div>
          <div>Action Type: <span className="text-text-primary">{investigation.action_type}</span></div>
          <div>Currency / Amount: <span className="text-text-primary">{investigation.currency} {(investigation.amount_minor / 100).toFixed(2)}</span></div>
          <div>Payload Status: <span className="text-verdict-approve font-bold">VALID</span></div>
        </div>
      ),
    },
    {
      id: "EVIDENCE",
      label: "2. EVIDENCE",
      status: investigation.evidence_artifacts.some((e) => e.status === "STALE" || e.status === "CONFLICTING")
        ? ("WARNING" as const)
        : investigation.evidence_artifacts.some((e) => e.status === "MISSING")
        ? ("FAIL" as const)
        : ("PASS" as const),
      summary: `${investigation.evidence_artifacts.length} Artifact(s) verified`,
      detail: (
        <div className="space-y-2 text-xs font-mono text-text-secondary">
          {investigation.evidence_artifacts.map((art) => (
            <div key={art.id} className="p-2 bg-background-primary rounded border border-border-subtle space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-bold text-text-primary">{art.type}</span>
                <span className={`px-1.5 py-0.5 text-[10px] font-bold rounded ${art.status === "VERIFIED" ? "bg-verdict-approve/10 text-verdict-approve" : "bg-verdict-review/10 text-verdict-review"}`}>
                  {art.status}
                </span>
              </div>
              <div className="text-[11px] text-text-muted">Source: {art.source}</div>
              <div className="text-[11px] text-text-muted">Timestamp: {art.timestamp}</div>
              {art.freshness_detail && (
                <div className="text-[11px] font-bold text-verdict-review">{art.freshness_detail}</div>
              )}
            </div>
          ))}
        </div>
      ),
    },
    {
      id: "POLICY",
      label: "3. POLICY",
      status: investigation.policy_snapshot.result === "PASS" ? ("PASS" as const) : ("FAIL" as const),
      summary: investigation.policy_snapshot.result === "PASS" ? "Policy limits met" : `Violation: ${investigation.policy_snapshot.rule_id}`,
      detail: (
        <div className="space-y-1 text-xs font-mono text-text-secondary">
          <div>Policy Ruleset: <span className="text-text-primary">{investigation.policy_snapshot.policy_version}</span></div>
          <div>Rule Evaluated: <span className="text-text-primary font-bold">{investigation.policy_snapshot.rule_id}</span> ({investigation.policy_snapshot.rule_description})</div>
          <div className="flex items-center gap-2 my-1">
            <span>Policy Limit:</span>
            <MoneyDisplay amountMinor={investigation.policy_snapshot.limit_minor} size="sm" />
            <span>vs Requested:</span>
            <MoneyDisplay amountMinor={investigation.policy_snapshot.requested_minor} size="sm" />
          </div>
          <div>Evaluation Outcome: <span className={`font-extrabold ${investigation.policy_snapshot.result === "PASS" ? "text-verdict-approve" : "text-verdict-block"}`}>{investigation.policy_snapshot.result}</span></div>
        </div>
      ),
    },
    {
      id: "CONSISTENCY",
      label: "4. CONSISTENCY",
      status: "PASS" as const,
      summary: "Ledger transaction state consistent",
      detail: (
        <div className="space-y-1 text-xs font-mono text-text-secondary">
          <div>Entity ID Linkage: <span className="text-text-primary">{investigation.merchant_id} / {investigation.customer_id || "N/A"}</span></div>
          <div>Cross-Ledger Check: <span className="text-verdict-approve font-bold">MATCHED</span></div>
          <div>State Check: <span className="text-text-primary">NO_DUPLICATE_FOUND</span></div>
        </div>
      ),
    },
    {
      id: "RISK",
      label: "5. RISK",
      status: investigation.risk_level === "LOW" ? ("PASS" as const) : investigation.risk_level === "MEDIUM" ? ("WARNING" as const) : ("FAIL" as const),
      summary: `Score: ${investigation.risk_score} (${investigation.risk_level})`,
      detail: (
        <div className="space-y-1.5 text-xs font-mono text-text-secondary">
          <div className="flex items-center justify-between">
            <span>Gross Exposure:</span>
            <MoneyDisplay amountMinor={investigation.risk_assessment.gross_exposure_minor} size="sm" />
          </div>
          <div>Risk Level: <span className="text-text-primary font-bold">{investigation.risk_level} ({investigation.risk_score})</span></div>
          <div>Risk Factors: <span className="text-text-muted">{investigation.risk_assessment.risk_factors.join(", ") || "None"}</span></div>
          {investigation.risk_assessment.hard_risk_flags.length > 0 && (
            <div className="text-verdict-block font-bold">Hard Flags: {investigation.risk_assessment.hard_risk_flags.join(", ")}</div>
          )}
        </div>
      ),
    },
    {
      id: "AI CONTEXT",
      label: "6. AI CONTEXT",
      status: "INFO" as const,
      summary: `Signal: ${investigation.ai_recommendation}`,
      detail: (
        <div className="space-y-1 text-xs font-mono text-text-secondary">
          <div>Model Recommendation: <span className="text-accent-ai font-bold">{investigation.ai_recommendation}</span></div>
          <div>Model Confidence: <span className="text-text-primary">{Math.round(investigation.ai_confidence * 100)}%</span></div>
          <div>Model ID: <span className="text-text-muted">{investigation.ai_model_id}</span></div>
        </div>
      ),
    },
    {
      id: "DECISION",
      label: "7. DECISION",
      status: investigation.verdict === "APPROVE" ? ("PASS" as const) : investigation.verdict === "REVIEW" ? ("WARNING" as const) : ("FAIL" as const),
      summary: `Verdict: ${investigation.verdict}`,
      detail: (
        <div className="space-y-1 text-xs font-mono text-text-secondary">
          <div>Authoritative Rule: <span className="text-text-primary font-bold">{investigation.decision_rule}</span></div>
          <div>Final Verdict: <span className={`font-extrabold ${investigation.verdict === "APPROVE" ? "text-verdict-approve" : investigation.verdict === "REVIEW" ? "text-verdict-review" : "text-verdict-block"}`}>{investigation.verdict}</span></div>
          <div>Boundary Action: <span className="text-text-primary">{investigation.execution_status}</span></div>
        </div>
      ),
    },
  ];

  const statusIcons = {
    PASS: { icon: CheckCircle2, color: "text-verdict-approve", bg: "bg-verdict-approve/10 border-verdict-approve/30" },
    WARNING: { icon: AlertTriangle, color: "text-verdict-review", bg: "bg-verdict-review/10 border-verdict-review/30" },
    FAIL: { icon: ShieldX, color: "text-verdict-block", bg: "bg-verdict-block/10 border-verdict-block/30" },
    INFO: { icon: Info, color: "text-accent-ai", bg: "bg-accent-ai/10 border-accent-ai/30" },
  };

  return (
    <div className="bg-background-surface/80 border border-border-subtle rounded-card p-4 space-y-4">
      <div className="flex items-center justify-between border-b border-border-subtle pb-2">
        <h3 className="text-xs font-mono font-bold text-text-primary uppercase tracking-wider flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-accent-infra animate-pulse" />
          7-STAGE INTERACTIVE VERIFICATION PIPELINE TRACE
        </h3>
        <span className="text-[11px] font-mono text-text-muted">Click stage to inspect</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-7 gap-2">
        {steps.map((step) => {
          const st = statusIcons[step.status];
          const Icon = st.icon;
          const isExpanded = expandedStage === step.id;

          return (
            <button
              key={step.id}
              onClick={() => toggleStage(step.id)}
              className={`p-2.5 rounded-lg border flex flex-col justify-between text-left transition-all ${st.bg} ${
                isExpanded ? "ring-2 ring-accent-infra shadow-glowAI" : "hover:border-border-active"
              }`}
            >
              <div className="flex items-center justify-between w-full">
                <span className="text-[10px] font-mono font-bold text-text-secondary">{step.label}</span>
                <Icon className={`h-3.5 w-3.5 ${st.color}`} />
              </div>
              <p className="text-[11px] font-mono text-text-muted line-clamp-2 mt-1">{step.summary}</p>
              <div className="mt-2 flex items-center justify-between text-[10px] font-mono text-accent-infra">
                <span>{isExpanded ? "Hide" : "Inspect"}</span>
                {isExpanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
              </div>
            </button>
          );
        })}
      </div>

      {/* Expanded Stage Contextual Information Panel */}
      {expandedStage && (
        <div className="p-4 bg-background-primary/90 rounded-card border border-accent-infra/30 animate-in fade-in zoom-in-95 duration-150 space-y-2">
          <div className="flex items-center justify-between border-b border-border-subtle pb-2 text-xs font-mono font-bold text-accent-infra">
            <span>DETAILED STAGE INSPECTION: {expandedStage}</span>
            <button onClick={() => setExpandedStage(null)} className="text-text-muted hover:text-text-primary text-[10px]">
              Close Inspector ✕
            </button>
          </div>
          {steps.find((s) => s.id === expandedStage)?.detail}
        </div>
      )}
    </div>
  );
};
