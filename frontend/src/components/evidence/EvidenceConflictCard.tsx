import React from "react";
import { AlertTriangle, ArrowRightLeft } from "lucide-react";

export const EvidenceConflictCard: React.FC = () => {
  return (
    <div className="bg-background-surface/80 border border-verdict-review/40 rounded-card p-4 space-y-3 shadow-glowReview">
      <div className="flex items-center justify-between border-b border-border-subtle pb-2">
        <div className="flex items-center gap-2 text-xs font-mono font-bold text-verdict-review uppercase">
          <AlertTriangle className="h-4 w-4" />
          <span>CONFLICTING EVIDENCE SIGNAL VISUALIZATION</span>
        </div>
        <span className="text-[10px] font-mono text-verdict-review font-bold px-2 py-0.5 rounded bg-verdict-review/10 border border-verdict-review/30">
          ROUTED TO REVIEW
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
        <div className="p-3 bg-background-primary rounded border border-border-subtle space-y-1">
          <span className="text-[10px] text-text-muted uppercase">SOURCE A: COURIER API</span>
          <div className="text-text-primary font-bold text-sm">Status: RETURNED</div>
          <span className="text-[11px] text-text-muted">Courier API Gateway reported package returned to hub.</span>
        </div>

        <div className="p-3 bg-background-primary rounded border border-border-subtle space-y-1">
          <span className="text-[10px] text-text-muted uppercase">SOURCE B: CUSTOMER SUPPORT LOG</span>
          <div className="text-verdict-review font-bold text-sm">Status: DELIVERED</div>
          <span className="text-[11px] text-text-muted">Customer agent note claimed item was delivered to customer.</span>
        </div>
      </div>

      <div className="p-2.5 bg-background-primary rounded border border-border-subtle flex items-center justify-between text-xs font-mono text-text-secondary">
        <div className="flex items-center gap-2">
          <ArrowRightLeft className="h-4 w-4 text-verdict-review" />
          <span>Conflict Outcome: <strong className="text-text-primary">TrustLedger routes evidence ambiguity directly to human review.</strong></span>
        </div>
        <span className="text-[10px] text-text-muted font-bold">Rule TL-DG-003</span>
      </div>
    </div>
  );
};
