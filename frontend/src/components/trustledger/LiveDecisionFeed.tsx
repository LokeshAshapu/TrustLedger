import React from "react";
import { useNavigate } from "react-router-dom";
import { ArrowUpRight, Activity } from "lucide-react";
import { StatusBadge } from "./StatusBadge";
import { RiskMeter } from "./RiskMeter";
import { AISignalBadge } from "./AISignalBadge";
import { MoneyDisplay } from "./MoneyDisplay";
import { MOCK_DECISIONS } from "../../data/mock";

export const LiveDecisionFeed: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="bg-background-surface/80 border border-border-subtle rounded-card p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-accent-infra animate-pulse" />
          <h3 className="text-xs font-mono font-bold text-text-primary uppercase tracking-wider">
            BENCHMARK DECISION FEED & SIGNAL COMPARISON
          </h3>
        </div>
        <button
          onClick={() => navigate("/decisions")}
          className="inline-flex items-center gap-1 text-xs font-mono text-accent-infra hover:underline"
        >
          <span>View All Decisions</span>
          <ArrowUpRight className="h-3.5 w-3.5" />
        </button>
      </div>

      <div className="divide-y divide-border-subtle/50">
        {MOCK_DECISIONS.map((item) => (
          <div
            key={item.decision_id}
            onClick={() => navigate("/decisions")}
            className="py-3 px-2 flex items-center justify-between hover:bg-background-hover/60 rounded-control cursor-pointer transition-colors group"
          >
            {/* Left: Action & Verdict */}
            <div className="flex items-center gap-3">
              <StatusBadge verdict={item.verdict} size="sm" />
              <div className="flex flex-col">
                <div className="flex items-center gap-2 font-mono text-xs font-bold text-text-primary group-hover:text-accent-infra transition-colors">
                  <span>{item.action_type}</span>
                  <span className="text-text-muted font-normal">| {item.merchant_id}</span>
                </div>
                <span className="text-[11px] font-mono text-text-muted">
                  {item.decision_id} • Rule {item.decision_rule}
                </span>
              </div>
            </div>

            {/* Middle: AI Signal vs Final Verdict Separation */}
            <div className="hidden md:flex items-center gap-3">
              <div className="flex flex-col items-end">
                <span className="text-[10px] font-mono text-text-muted uppercase">ADVISORY SIGNAL</span>
                <AISignalBadge recommendation={item.ai_recommendation} />
              </div>
              <div className="h-6 w-px bg-border-subtle" />
              <div className="flex flex-col items-start">
                <span className="text-[10px] font-mono text-text-muted uppercase">RISK ENGINE</span>
                <RiskMeter level={item.risk_level} score={item.risk_score} />
              </div>
            </div>

            {/* Right: Amount */}
            <div className="flex items-center gap-3">
              <MoneyDisplay amountMinor={item.amount_minor} size="sm" />
              <ArrowUpRight className="h-4 w-4 text-text-muted group-hover:text-text-primary transition-colors" />
            </div>
          </div>
        ))}
      </div>

      <div className="p-2.5 rounded-control bg-background-primary border border-border-subtle text-[11px] font-mono text-text-muted flex items-center justify-between">
        <span>💡 Key Principle: Advisory AI Signals (<strong className="text-accent-ai font-semibold">SUPPORT</strong>) are strictly evaluated after hard deterministic policy rules (<strong className="text-verdict-block font-semibold">BLOCK</strong>).</span>
        <span className="hidden sm:inline">TrustLedger Decides</span>
      </div>
    </div>
  );
};
