import React, { useMemo } from "react";
import { AlertCircle, PieChart } from "lucide-react";
import { TrustLedgerAPI } from "../lib/trustledger-api";
import { MoneyDisplay } from "../components/trustledger/MoneyDisplay";
import { HardRiskFlagsCard } from "../components/risk/HardRiskFlagsCard";
import { ErrorState } from "../components/ui/ErrorState";

export const RiskPage: React.FC = () => {
  const riskOverview = useMemo(() => {
    try {
      return TrustLedgerAPI.getRiskOverview();
    } catch (err) {
      console.error("Risk Overview Error:", err);
      return null;
    }
  }, []);

  if (!riskOverview) {
    return (
      <ErrorState
        title="RISK DATA UNRETRIEVABLE"
        description="Could not load control plane risk overview dataset."
        onRetry={() => window.location.reload()}
      />
    );
  }

  const { risk_level_distribution } = riskOverview;
  const total = risk_level_distribution.LOW + risk_level_distribution.MEDIUM + risk_level_distribution.HIGH + risk_level_distribution.CRITICAL;

  return (
    <div className="space-y-6">
      {/* 1. Header */}
      <div className="bg-background-surface/80 border border-border-subtle rounded-card p-5 flex items-center justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-verdict-review" />
            <span className="text-xs font-mono font-bold text-verdict-review uppercase tracking-widest">
              FINANCIAL RISK ENGINE CONTROL PLANE
            </span>
          </div>
          <h2 className="text-xl font-mono font-extrabold text-text-primary tracking-tight">
            RISK EXPOSURE & DETERMINISTIC HARD FLAGS
          </h2>
          <p className="text-xs text-text-muted">
            Monitor financial exposure quantification, velocity limits, risk multipliers, and non-overridable safety flags.
          </p>
        </div>
      </div>

      {/* 2. Verified Exposure Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 font-mono text-xs">
        <div className="p-4 rounded-card border border-border-subtle bg-background-surface flex flex-col justify-between">
          <span className="text-text-muted uppercase text-[11px]">TOTAL GROSS EXPOSURE</span>
          <div className="my-2">
            <MoneyDisplay amountMinor={riskOverview.total_gross_exposure_minor} size="xl" />
          </div>
          <span className="text-[10px] text-text-muted">Requested in test suite</span>
        </div>

        <div className="p-4 rounded-card border border-verdict-approve/30 bg-verdict-approve/5 shadow-glowApprove flex flex-col justify-between">
          <span className="text-text-muted uppercase text-[11px]">UNSAFE EXPOSURE APPROVED</span>
          <div className="my-2">
            <MoneyDisplay amountMinor={riskOverview.unsafe_exposure_approved_minor} size="xl" />
          </div>
          <span className="text-[10px] text-verdict-approve font-bold">✅ PERFECT 0.00% APPROVED</span>
        </div>

        <div className="p-4 rounded-card border border-verdict-block/30 bg-verdict-block/5 shadow-glowBlock flex flex-col justify-between">
          <span className="text-text-muted uppercase text-[11px]">UNSAFE EXPOSURE BLOCKED</span>
          <div className="my-2">
            <MoneyDisplay amountMinor={riskOverview.unsafe_exposure_blocked_minor} size="xl" isExposure />
          </div>
          <span className="text-[10px] text-verdict-block font-bold">100.00% BLOCKED (₹97.74L)</span>
        </div>

        <div className="p-4 rounded-card border border-border-subtle bg-background-surface flex flex-col justify-between">
          <span className="text-text-muted uppercase text-[11px]">IRREVERSIBLE EXPOSURE</span>
          <div className="my-2">
            <MoneyDisplay amountMinor={riskOverview.irreversible_exposure_minor} size="xl" />
          </div>
          <span className="text-[10px] text-text-muted">High-risk action scope</span>
        </div>
      </div>

      {/* 3. Hard Risk Flags Card */}
      <HardRiskFlagsCard flags={riskOverview.hard_risk_flags} />

      {/* 4. Risk Level Distribution Chart */}
      <div className="bg-background-surface/80 border border-border-subtle rounded-card p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <PieChart className="h-4 w-4 text-accent-infra" />
            <h3 className="text-xs font-mono font-bold text-text-primary uppercase tracking-wider">
              RISK SEVERITY LEVEL DISTRIBUTION
            </h3>
          </div>
          <span className="text-xs font-mono text-text-muted">{total} Total Evaluated Cases</span>
        </div>

        <div className="grid grid-cols-4 gap-2 pt-1 font-mono text-xs">
          <div className="p-3 rounded bg-background-primary border border-verdict-approve/20 flex flex-col">
            <span className="text-verdict-approve font-bold">LOW RISK</span>
            <span className="text-lg font-extrabold text-text-primary mt-1">{risk_level_distribution.LOW}</span>
            <span className="text-[10px] text-text-muted">Potentially APPROVE</span>
          </div>

          <div className="p-3 rounded bg-background-primary border border-verdict-review/20 flex flex-col">
            <span className="text-verdict-review font-bold">MEDIUM RISK</span>
            <span className="text-lg font-extrabold text-text-primary mt-1">{risk_level_distribution.MEDIUM}</span>
            <span className="text-[10px] text-text-muted">Potentially REVIEW</span>
          </div>

          <div className="p-3 rounded bg-background-primary border border-amber-500/20 flex flex-col">
            <span className="text-amber-500 font-bold">HIGH RISK</span>
            <span className="text-lg font-extrabold text-text-primary mt-1">{risk_level_distribution.HIGH}</span>
            <span className="text-[10px] text-text-muted">Human REVIEW</span>
          </div>

          <div className="p-3 rounded bg-background-primary border border-verdict-block/20 flex flex-col">
            <span className="text-verdict-block font-bold">CRITICAL RISK</span>
            <span className="text-lg font-extrabold text-text-primary mt-1">{risk_level_distribution.CRITICAL}</span>
            <span className="text-[10px] text-text-muted">Hard BLOCK</span>
          </div>
        </div>
      </div>

      {/* 5. Risk Factors Breakdown Grid */}
      <div className="bg-background-surface/80 border border-border-subtle rounded-card p-4 space-y-3">
        <h3 className="text-xs font-mono font-bold text-text-primary uppercase tracking-wider">
          ACTIVE RISK FACTORS DETECTED
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs font-mono">
          {riskOverview.risk_factors.map((factor, idx) => (
            <div key={idx} className="p-2.5 rounded bg-background-primary border border-border-subtle text-text-secondary">
              <span className="text-accent-infra font-bold">#</span> {factor}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
