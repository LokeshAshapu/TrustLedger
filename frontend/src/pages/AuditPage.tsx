import React, { useMemo } from "react";
import { FileText } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { TrustLedgerAPI } from "../lib/trustledger-api";
import { StatusBadge } from "../components/trustledger/StatusBadge";
import { AISignalBadge } from "../components/trustledger/AISignalBadge";
import { RiskMeter } from "../components/trustledger/RiskMeter";
import { MoneyDisplay } from "../components/trustledger/MoneyDisplay";
import { AuditTimeline } from "../components/audit/AuditTimeline";
import { ErrorState } from "../components/ui/ErrorState";

export const AuditPage: React.FC = () => {
  const navigate = useNavigate();

  const auditData = useMemo(() => {
    try {
      return TrustLedgerAPI.getAuditExplorerData();
    } catch (err) {
      console.error("Audit Explorer Error:", err);
      return null;
    }
  }, []);

  if (!auditData) {
    return (
      <ErrorState
        title="AUDIT DATA UNRETRIEVABLE"
        description="Could not load control plane audit trail dataset."
        onRetry={() => window.location.reload()}
      />
    );
  }

  const { records, timeline } = auditData;

  return (
    <div className="space-y-6">
      {/* 1. Header */}
      <div className="bg-background-surface/80 border border-border-subtle rounded-card p-5 flex items-center justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-accent-infra" />
            <span className="text-xs font-mono font-bold text-accent-infra uppercase tracking-widest">
              IMMUTABLE CRYPTOGRAPHIC AUDIT TRAIL
            </span>
          </div>
          <h2 className="text-xl font-mono font-extrabold text-text-primary tracking-tight">
            CANONICAL DECISION AUDIT EXPLORER
          </h2>
          <p className="text-xs text-text-muted">
            Reconstruct exactly why any financial action was allowed or blocked with SHA-256 cryptographic hashes.
          </p>
        </div>
      </div>

      {/* 2. Step-by-Step Decision Reconstruction Timeline */}
      <AuditTimeline events={timeline} />

      {/* 3. Canonical Audit Trail Table */}
      <div className="bg-background-surface/80 border border-border-subtle rounded-card overflow-hidden">
        <div className="p-4 border-b border-border-subtle flex items-center justify-between">
          <h3 className="text-xs font-mono font-bold text-text-primary uppercase tracking-wider">
            CANONICAL AUDIT LOG REGISTRY
          </h3>
          <span className="text-xs font-mono text-text-muted">
            {records.length} Sample Audit Records
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs font-mono">
            <thead>
              <tr className="bg-background-secondary/80 border-b border-border-subtle text-text-muted uppercase font-semibold">
                <th className="py-3 px-4">Time & Decision ID</th>
                <th className="py-3 px-4">Action</th>
                <th className="py-3 px-4">AI Signal</th>
                <th className="py-3 px-4">Risk Level</th>
                <th className="py-3 px-4">Verdict</th>
                <th className="py-3 px-4">SHA-256 Hash</th>
                <th className="py-3 px-4 text-right">Amount</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle/50 text-text-primary">
              {records.map((rec) => (
                <tr
                  key={rec.decision_id}
                  onClick={() => navigate(`/decisions/${rec.decision_id}`)}
                  className="hover:bg-background-hover/60 cursor-pointer transition-colors group"
                >
                  <td className="py-3.5 px-4 font-bold">
                    <div className="flex flex-col">
                      <span className="text-accent-infra group-hover:underline">{rec.decision_id}</span>
                      <span className="text-[10px] text-text-muted">{rec.timestamp}</span>
                    </div>
                  </td>
                  <td className="py-3.5 px-4">{rec.action_type}</td>
                  <td className="py-3.5 px-4">
                    <AISignalBadge recommendation={rec.ai_signal} />
                  </td>
                  <td className="py-3.5 px-4">
                    <RiskMeter level={rec.risk_level} />
                  </td>
                  <td className="py-3.5 px-4">
                    <StatusBadge verdict={rec.verdict} size="sm" />
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="text-[11px] text-text-muted font-mono">{rec.decision_hash.substring(0, 12)}...</span>
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <MoneyDisplay amountMinor={rec.amount_minor} size="sm" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
