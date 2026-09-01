import React from "react";
import { Award } from "lucide-react";
import { DataSourceBadge } from "./DataSourceBadge";
import { TrustLedgerAPI } from "../../lib/trustledger-api";

export const RefundEvaluationPanel: React.FC = () => {
  const snapshot = TrustLedgerAPI.getEvaluationSnapshot();

  return (
    <div className="bg-background-surface/90 border border-border-subtle rounded-card p-5 space-y-4 shadow-panel font-mono">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between border-b border-border-subtle pb-3 gap-2">
        <div className="flex items-center gap-2">
          <Award className="h-5 w-5 text-accent-infra animate-pulse" />
          <div>
            <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider">
              HELD-OUT REFUND BENCHMARK EVALUATION SUMMARY
            </h3>
            <span className="text-[11px] text-text-muted">Rigorous 1,500 held-out evaluation baseline (Phase 8.1 frozen engine)</span>
          </div>
        </div>
        <DataSourceBadge type="HELD_OUT_BENCHMARK" />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
        <div className="p-3 bg-background-primary rounded border border-border-subtle space-y-1">
          <span className="text-[10px] text-text-muted uppercase">Decision Accuracy:</span>
          <div className="text-xl font-extrabold text-accent-infra">{snapshot.decisionAccuracy.toFixed(2)}%</div>
          <span className="text-[10px] text-text-muted">1,436 / 1,500 Matches</span>
        </div>

        <div className="p-3 bg-background-primary rounded border border-border-subtle space-y-1">
          <span className="text-[10px] text-text-muted uppercase">Macro F1 Score:</span>
          <div className="text-xl font-extrabold text-accent-infra">{snapshot.macroF1.toFixed(2)}%</div>
          <span className="text-[10px] text-text-muted">Balanced Performance</span>
        </div>

        <div className="p-3 bg-background-primary rounded border border-border-subtle space-y-1">
          <span className="text-[10px] text-text-muted uppercase">Unsafe Approval Rate:</span>
          <div className="text-xl font-extrabold text-verdict-approve">{snapshot.unsafeApprovalRate.toFixed(2)}%</div>
          <span className="text-[10px] text-text-muted">0 / 637 Unsafe Cases</span>
        </div>

        <div className="p-3 bg-background-primary rounded border border-border-subtle space-y-1">
          <span className="text-[10px] text-text-muted uppercase">Block Recall:</span>
          <div className="text-xl font-extrabold text-verdict-block">{snapshot.blockRecall.toFixed(2)}%</div>
          <span className="text-[10px] text-text-muted">100% Unsafe Blocked</span>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs pt-1">
        <div className="p-3 bg-background-primary rounded border border-border-subtle space-y-1">
          <span className="text-[10px] text-text-muted uppercase">Block Precision:</span>
          <div className="text-lg font-bold text-text-primary">{snapshot.blockPrecision.toFixed(2)}%</div>
        </div>

        <div className="p-3 bg-background-primary rounded border border-border-subtle space-y-1">
          <span className="text-[10px] text-text-muted uppercase">Safe Approval Rate:</span>
          <div className="text-lg font-bold text-text-primary">{snapshot.safeApprovalRate.toFixed(2)}%</div>
        </div>

        <div className="p-3 bg-background-primary rounded border border-border-subtle space-y-1">
          <span className="text-[10px] text-text-muted uppercase">Review Recall:</span>
          <div className="text-lg font-bold text-text-primary">{snapshot.reviewRecall.toFixed(2)}%</div>
        </div>

        <div className="p-3 bg-background-primary rounded border border-border-subtle space-y-1">
          <span className="text-[10px] text-text-muted uppercase">Security Suite:</span>
          <div className="text-lg font-bold text-verdict-approve">{snapshot.adversarialPassed}/{snapshot.adversarialTotal} Passed</div>
        </div>
      </div>
    </div>
  );
};
