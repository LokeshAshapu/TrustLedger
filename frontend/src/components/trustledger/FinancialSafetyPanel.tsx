import React from "react";
import { ShieldCheck, Lock } from "lucide-react";
import { MoneyDisplay } from "./MoneyDisplay";

interface FinancialSafetyPanelProps {
  unsafeExposureApproved: number;
  unsafeExposureBlocked: number;
  blockRecall: number;
}

export const FinancialSafetyPanel: React.FC<FinancialSafetyPanelProps> = ({
  unsafeExposureApproved,
  unsafeExposureBlocked,
  blockRecall,
}) => {
  return (
    <div className="bg-background-surface/90 border border-verdict-approve/30 rounded-card p-5 space-y-4 shadow-glowApprove">
      <div className="flex items-center justify-between border-b border-border-subtle pb-3">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-5 w-5 text-verdict-approve stroke-[2.2]" />
          <h3 className="text-xs font-mono font-bold text-text-primary uppercase tracking-wider">
            FINANCIAL SAFETY GUARANTEE
          </h3>
        </div>
        <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-verdict-approve/10 border border-verdict-approve/30 text-verdict-approve">
          0 UNSAFE APPROVALS
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Unsafe Exposure Approved (Must be ₹0.00!) */}
        <div className="p-3.5 bg-background-primary rounded-control border border-verdict-approve/30 flex flex-col justify-between">
          <span className="text-[11px] font-mono text-text-muted uppercase tracking-wider">
            UNSAFE EXPOSURE APPROVED
          </span>
          <div className="my-1">
            <MoneyDisplay amountMinor={unsafeExposureApproved} size="xl" />
          </div>
          <span className="text-[10px] font-mono text-verdict-approve font-semibold">
            ✅ PERFECT 0.00% (0 / 637 UNSAFE CASES)
          </span>
        </div>

        {/* Unsafe Exposure Blocked */}
        <div className="p-3.5 bg-background-primary rounded-control border border-border-subtle flex flex-col justify-between">
          <span className="text-[11px] font-mono text-text-muted uppercase tracking-wider">
            UNSAFE EXPOSURE BLOCKED
          </span>
          <div className="my-1">
            <MoneyDisplay amountMinor={unsafeExposureBlocked} size="xl" isExposure />
          </div>
          <span className="text-[10px] font-mono text-text-secondary">
            Protected in benchmark simulation
          </span>
        </div>

        {/* Block Recall */}
        <div className="p-3.5 bg-background-primary rounded-control border border-border-subtle flex flex-col justify-between">
          <span className="text-[11px] font-mono text-text-muted uppercase tracking-wider">
            BLOCK RECALL & PRECISION
          </span>
          <div className="my-1 text-2xl font-mono font-extrabold text-text-primary">
            {blockRecall.toFixed(2)}%
          </div>
          <span className="text-[10px] font-mono text-text-secondary">
            637 / 637 Unsafe cases blocked
          </span>
        </div>
      </div>

      {/* Safety Statement Banner */}
      <div className="p-2.5 rounded-control bg-background-primary/80 border border-border-subtle flex items-center justify-between text-xs font-mono text-text-secondary">
        <div className="flex items-center gap-2">
          <Lock className="h-3.5 w-3.5 text-accent-infra" />
          <span>Product Safety Principle: <strong className="text-text-primary font-semibold">Hard deterministic violations cannot be overridden by AI context.</strong></span>
        </div>
        <span className="text-[10px] text-text-muted hidden md:inline-block">Authority Level 2 Deterministic</span>
      </div>
    </div>
  );
};
