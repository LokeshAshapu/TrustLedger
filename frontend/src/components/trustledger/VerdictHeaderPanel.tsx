import React from "react";
import { ArrowLeft, Hash } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { MoneyDisplay } from "./MoneyDisplay";
import { StatusBadge } from "./StatusBadge";
import { RiskMeter } from "./RiskMeter";
import { AISignalBadge } from "./AISignalBadge";
import { DataSourceBadge } from "./DataSourceBadge";
import type { DecisionInvestigation } from "../../data/mock/investigations";

interface VerdictHeaderPanelProps {
  investigation: DecisionInvestigation;
}

export const VerdictHeaderPanel: React.FC<VerdictHeaderPanelProps> = ({
  investigation,
}) => {
  const navigate = useNavigate();
  const isLive = investigation.decision_id.startsWith("dec_live_");

  return (
    <div className="bg-background-surface/80 border border-border-subtle rounded-card p-5 space-y-4">
      {/* Top Back Navigation Bar */}
      <div className="flex items-center justify-between border-b border-border-subtle pb-3">
        <button
          onClick={() => navigate("/decisions")}
          className="inline-flex items-center gap-1.5 text-xs font-mono text-text-muted hover:text-text-primary transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>← Back to Decisions Queue</span>
        </button>
        <div className="flex items-center gap-3">
          <DataSourceBadge type={isLive ? "LIVE_BACKEND" : "HELD_OUT_BENCHMARK"} />
          <div className="flex items-center gap-2 text-xs font-mono text-text-muted">
            <Hash className="h-3.5 w-3.5 text-accent-infra" />
            <span>ID: <strong className="text-text-primary">{investigation.decision_id}</strong></span>
            <span>({investigation.decision_rule})</span>
          </div>
        </div>
      </div>

      {/* Main Action & Verdict Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Left: Action & Amount */}
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-xs font-mono text-text-muted uppercase">
            <span>PROPOSED FINANCIAL ACTION</span>
            <span>• {investigation.merchant_id}</span>
          </div>
          <div className="flex items-baseline gap-3">
            <span className="text-xl font-mono font-extrabold text-text-primary uppercase tracking-tight">
              {investigation.action_type}
            </span>
            <MoneyDisplay amountMinor={investigation.amount_minor} size="xl" />
          </div>
        </div>

        {/* Right: Authoritative Verdict & Signals */}
        <div className="flex flex-wrap items-center gap-4">
          <div className="space-y-1 text-right">
            <span className="text-[10px] font-mono text-text-muted uppercase">AUTHORITATIVE VERDICT</span>
            <div>
              <StatusBadge verdict={investigation.verdict} size="md" />
            </div>
          </div>

          <div className="space-y-1 text-right">
            <span className="text-[10px] font-mono text-text-muted uppercase">AI SIGNAL</span>
            <div>
              <AISignalBadge recommendation={investigation.ai_recommendation} confidence={investigation.ai_confidence} />
            </div>
          </div>

          <div className="space-y-1 text-right">
            <span className="text-[10px] font-mono text-text-muted uppercase">RISK SCORE</span>
            <div>
              <RiskMeter level={investigation.risk_level} score={investigation.risk_score} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
