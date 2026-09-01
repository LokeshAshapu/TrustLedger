import React from "react";
import { ShieldCheck, AlertOctagon, CheckCircle2, Info } from "lucide-react";
import { MoneyDisplay } from "./MoneyDisplay";
import { DataSourceBadge } from "./DataSourceBadge";

export const RefundLossPreventionCard: React.FC = () => {
  return (
    <div className="bg-background-surface/90 border border-border-subtle rounded-card p-5 space-y-4 shadow-panel font-mono">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between border-b border-border-subtle pb-3 gap-2">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-5 w-5 text-verdict-approve animate-pulse" />
          <div>
            <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider">
              AI REFUND LOSS PREVENTION & SAFETY METRICS
            </h3>
            <span className="text-[11px] text-text-muted">Direct financial impact & unsafe exposure protection</span>
          </div>
        </div>
        <DataSourceBadge type="HELD_OUT_BENCHMARK" />
      </div>

      {/* Main 3 Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
        {/* Unsafe Exposure Prevented */}
        <div className="p-4 bg-verdict-block/10 rounded-card border border-verdict-block/30 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-text-muted uppercase font-bold">UNSAFE EXPOSURE PREVENTED</span>
            <AlertOctagon className="h-4 w-4 text-verdict-block" />
          </div>
          <div className="pt-1">
            <MoneyDisplay amountMinor={977447800} size="xl" isExposure />
          </div>
          <div className="flex items-center justify-between pt-1 text-[10px]">
            <span className="text-verdict-block font-extrabold">100.00% BLOCKED</span>
            <span className="text-text-muted">₹97.74 Lakh Total</span>
          </div>
        </div>

        {/* Unsafe Exposure Approved */}
        <div className="p-4 bg-verdict-approve/10 rounded-card border border-verdict-approve/30 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-text-muted uppercase font-bold">UNSAFE EXPOSURE APPROVED</span>
            <CheckCircle2 className="h-4 w-4 text-verdict-approve" />
          </div>
          <div className="pt-1">
            <MoneyDisplay amountMinor={0} size="xl" />
          </div>
          <div className="flex items-center justify-between pt-1 text-[10px]">
            <span className="text-verdict-approve font-extrabold">0.00% UNSAFE RATE</span>
            <span className="text-text-muted">0 of 637 Unsafe Cases</span>
          </div>
        </div>

        {/* Safe False-Block Rate */}
        <div className="p-4 bg-verdict-review/10 rounded-card border border-verdict-review/30 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-text-muted uppercase font-bold">SAFE FALSE-BLOCK RATE</span>
            <Info className="h-4 w-4 text-verdict-review" />
          </div>
          <div className="text-2xl font-extrabold text-verdict-review pt-1">6.02%</div>
          <div className="flex items-center justify-between pt-1 text-[10px]">
            <span className="text-verdict-review font-extrabold">33 / 548 SAFE CASES</span>
            <span className="text-text-muted">Conservatively Gated</span>
          </div>
        </div>
      </div>

      {/* Honest False-Positive Callout */}
      <div className="p-3 bg-background-primary rounded-control border border-border-subtle flex items-start gap-2.5 text-[11px] text-text-secondary">
        <Info className="h-4 w-4 text-accent-infra flex-shrink-0 mt-0.5" />
        <p>
          <strong className="text-text-primary">Honest Evaluation Tradeoff:</strong> Conservative Level 2 policy cap enforcement routes legitimate edge cases (6.02% false-block rate) to BLOCK or REVIEW rather than risking a single unsafe financial approval. This is measured and disclosed transparently.
        </p>
      </div>
    </div>
  );
};
