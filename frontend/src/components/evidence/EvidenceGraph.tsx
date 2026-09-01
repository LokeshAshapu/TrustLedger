import React from "react";
import { User, ShoppingBag, Receipt, Database, CheckCircle2, AlertTriangle } from "lucide-react";

export const EvidenceGraph: React.FC = () => {
  return (
    <div className="bg-background-surface/80 border border-border-subtle rounded-card p-4 space-y-3">
      <div className="flex items-center justify-between border-b border-border-subtle pb-2">
        <h4 className="text-xs font-mono font-bold text-text-primary uppercase tracking-wider flex items-center gap-2">
          <Database className="h-4 w-4 text-accent-infra" />
          <span>MULTI-LEDGER EVIDENCE LINKAGE GRAPH</span>
        </h4>
        <span className="text-[10px] font-mono text-text-muted">Entity Graph Schema</span>
      </div>

      <div className="p-4 bg-background-primary/90 rounded-control border border-border-subtle overflow-x-auto">
        <div className="flex items-center justify-between min-w-[540px] text-xs font-mono">
          {/* Node 1: Customer */}
          <div className="flex flex-col items-center p-3 rounded-lg border border-border-subtle bg-background-surface/80 space-y-1">
            <User className="h-5 w-5 text-accent-infra" />
            <span className="font-bold text-text-primary">CUSTOMER</span>
            <span className="text-[10px] text-text-muted">cust_100</span>
          </div>

          <div className="h-0.5 w-12 bg-border-active relative">
            <div className="absolute -top-1.5 left-1/2 -translate-x-1/2 text-[9px] text-text-muted">1:N</div>
          </div>

          {/* Node 2: Order */}
          <div className="flex flex-col items-center p-3 rounded-lg border border-border-subtle bg-background-surface/80 space-y-1">
            <ShoppingBag className="h-5 w-5 text-accent-infra" />
            <span className="font-bold text-text-primary">ORDER</span>
            <span className="text-[10px] text-text-muted">ord_88192</span>
          </div>

          <div className="h-0.5 w-12 bg-border-active relative">
            <div className="absolute -top-1.5 left-1/2 -translate-x-1/2 text-[9px] text-text-muted">1:1</div>
          </div>

          {/* Node 3: Transaction */}
          <div className="flex flex-col items-center p-3 rounded-lg border border-border-subtle bg-background-surface/80 space-y-1">
            <Receipt className="h-5 w-5 text-accent-infra" />
            <span className="font-bold text-text-primary">TRANSACTION</span>
            <span className="text-[10px] text-text-muted">txn_40192</span>
          </div>

          <div className="h-0.5 w-12 bg-border-active relative">
            <div className="absolute -top-1.5 left-1/2 -translate-x-1/2 text-[9px] text-text-muted">EVIDENCE</div>
          </div>

          {/* Node 4: Evidence Artifacts */}
          <div className="flex flex-col space-y-1.5">
            <div className="p-1.5 rounded border border-verdict-approve/30 bg-verdict-approve/10 text-verdict-approve flex items-center gap-1.5 text-[11px]">
              <CheckCircle2 className="h-3.5 w-3.5" />
              <span>Courier Delivery Receipt (VERIFIED)</span>
            </div>
            <div className="p-1.5 rounded border border-verdict-review/30 bg-verdict-review/10 text-verdict-review flex items-center gap-1.5 text-[11px]">
              <AlertTriangle className="h-3.5 w-3.5" />
              <span>Zendesk Support Ticket (STALE)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
