import React, { useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ShieldCheck, Lock, Database, Clock, FileText } from "lucide-react";
import { TrustLedgerAPI } from "../lib/trustledger-api";
import { VerdictHeaderPanel } from "../components/trustledger/VerdictHeaderPanel";
import { AISignalVsVerdictPanel } from "../components/trustledger/AISignalVsVerdictPanel";
import { InteractiveDecisionTrace } from "../components/trustledger/InteractiveDecisionTrace";
import { ReviewContextCard } from "../components/trustledger/ReviewContextCard";
import { AuditHashMetadata } from "../components/trustledger/AuditHashMetadata";
import { MoneyDisplay } from "../components/trustledger/MoneyDisplay";
import { ErrorState } from "../components/ui/ErrorState";

export const DecisionInvestigationPage: React.FC = () => {
  const { decisionId } = useParams<{ decisionId: string }>();
  const navigate = useNavigate();

  const targetId = decisionId || "dec_blk_pol_000042";

  // Fetch decision investigation payload from data adapter
  const investigation = useMemo(() => {
    try {
      return TrustLedgerAPI.getDecision(targetId);
    } catch (err) {
      console.error("Decision Retrieval Error:", err);
      return null;
    }
  }, [targetId]);

  if (!investigation) {
    return (
      <ErrorState
        title="DECISION DATA INCONSISTENT OR NOT FOUND"
        description={`The control plane could not retrieve decision payload for ID '${targetId}'.`}
        onRetry={() => navigate("/decisions")}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* 1. Decision Header & Verdict Banner */}
      <VerdictHeaderPanel investigation={investigation} />

      {/* 2. Side-by-Side AI Signal vs TrustLedger Verdict Comparison */}
      <AISignalVsVerdictPanel investigation={investigation} />

      {/* 3. 7-Stage Interactive Decision Verification Trace */}
      <InteractiveDecisionTrace investigation={investigation} />

      {/* 4. Review Context Card (rendered when review required) */}
      {investigation.review_context && (
        <ReviewContextCard reviewContext={investigation.review_context} />
      )}

      {/* 5. Grid Layout: Evidence Provenance & Policy Snapshot */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Evidence Artifacts Detail */}
        <div className="bg-background-surface/80 border border-border-subtle rounded-card p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-border-subtle pb-2">
            <div className="flex items-center gap-2 text-xs font-mono font-bold text-text-primary uppercase">
              <Database className="h-4 w-4 text-accent-infra" />
              <span>EVIDENCE PROVENANCE & FRESHNESS</span>
            </div>
            <span className="text-[10px] font-mono text-text-muted">{investigation.evidence_artifacts.length} Artifact(s)</span>
          </div>

          <div className="space-y-2">
            {investigation.evidence_artifacts.map((art) => (
              <div key={art.id} className="p-3 bg-background-primary rounded-control border border-border-subtle space-y-1 text-xs font-mono">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-text-primary">{art.type}</span>
                  <span className={`px-2 py-0.5 text-[10px] font-bold rounded ${art.status === "VERIFIED" ? "bg-verdict-approve/10 text-verdict-approve" : "bg-verdict-review/10 text-verdict-review"}`}>
                    {art.status}
                  </span>
                </div>
                <div className="text-text-muted">ID: {art.id} • Source: {art.source}</div>
                <div className="text-text-muted flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  <span>Timestamp: {art.timestamp}</span>
                </div>
                {art.freshness_detail && (
                  <div className="text-verdict-review font-semibold pt-1 border-t border-border-subtle/50">
                    {art.freshness_detail}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Policy Snapshot Detail */}
        <div className="bg-background-surface/80 border border-border-subtle rounded-card p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-border-subtle pb-2">
            <div className="flex items-center gap-2 text-xs font-mono font-bold text-text-primary uppercase">
              <FileText className="h-4 w-4 text-accent-infra" />
              <span>ACTIVE MERCHANT POLICY SNAPSHOT</span>
            </div>
            <span className="text-[10px] font-mono text-text-muted">{investigation.policy_snapshot.policy_version}</span>
          </div>

          <div className="p-3 bg-background-primary rounded-control border border-border-subtle space-y-2 text-xs font-mono">
            <div className="flex items-center justify-between font-bold">
              <span>Rule Evaluated:</span>
              <span className="text-accent-infra">{investigation.policy_snapshot.rule_id}</span>
            </div>
            <p className="text-text-muted text-[11px]">{investigation.policy_snapshot.rule_description}</p>

            <div className="p-2 bg-background-surface rounded border border-border-subtle flex items-center justify-between my-2">
              <div>
                <span className="text-[10px] text-text-muted uppercase">Policy Cap Limit:</span>
                <MoneyDisplay amountMinor={investigation.policy_snapshot.limit_minor} size="sm" />
              </div>
              <div className="text-right">
                <span className="text-[10px] text-text-muted uppercase">Requested Amount:</span>
                <MoneyDisplay amountMinor={investigation.policy_snapshot.requested_minor} size="sm" />
              </div>
            </div>

            <div className="flex items-center justify-between font-bold">
              <span>Policy Evaluation Outcome:</span>
              <span className={`px-2 py-0.5 rounded text-xs ${investigation.policy_snapshot.result === "PASS" ? "bg-verdict-approve/10 text-verdict-approve" : "bg-verdict-block/10 text-verdict-block"}`}>
                {investigation.policy_snapshot.result}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 6. Execution Authorization & Related Records */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Execution Boundary State */}
        <div className="bg-background-surface/80 border border-border-subtle rounded-card p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-border-subtle pb-2">
            <div className="flex items-center gap-2 text-xs font-mono font-bold text-text-primary uppercase">
              <Lock className="h-4 w-4 text-accent-infra" />
              <span>EXECUTION AUTHORIZATION BOUNDARY</span>
            </div>
            <span className="text-[10px] font-mono text-accent-infra">NON-BYPASS CONTROL</span>
          </div>

          <div className="p-3 bg-background-primary rounded-control border border-border-subtle space-y-2 text-xs font-mono">
            <div className="flex items-center justify-between">
              <span>Authorization Status:</span>
              <span className={`font-extrabold uppercase ${investigation.execution_status === "AUTHORIZED" ? "text-verdict-approve" : "text-verdict-block"}`}>
                {investigation.execution_status}
              </span>
            </div>

            {investigation.verdict !== "APPROVE" ? (
              <div className="p-2.5 bg-verdict-block/10 rounded border border-verdict-block/30 text-verdict-block font-bold text-[11px] text-center">
                ⛔ NO FINANCIAL EXECUTION AUTHORIZED
              </div>
            ) : (
              <div className="p-2.5 bg-verdict-approve/10 rounded border border-verdict-approve/30 text-verdict-approve font-bold text-[11px] text-center">
                ✅ EXECUTION AUTHORIZATION TOKEN ISSUED (TTL 300s)
              </div>
            )}
          </div>
        </div>

        {/* Cryptographic Audit Hash & Related Records */}
        <div className="bg-background-surface/80 border border-border-subtle rounded-card p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-border-subtle pb-2">
            <div className="flex items-center gap-2 text-xs font-mono font-bold text-text-primary uppercase">
              <ShieldCheck className="h-4 w-4 text-accent-infra" />
              <span>CRYPTOGRAPHIC AUDIT & CONTEXT</span>
            </div>
            <span className="text-[10px] font-mono text-text-muted">SHA-256 Verified</span>
          </div>

          <AuditHashMetadata
            decisionId={investigation.decision_id}
            decisionHash={investigation.decision_hash}
            gateVersion={investigation.gate_version}
          />

          <div className="grid grid-cols-3 gap-2 pt-1 text-[11px] font-mono text-text-secondary text-center">
            <div className="p-2 bg-background-primary rounded border border-border-subtle">
              <span className="text-text-muted text-[10px] block">Customer Orders</span>
              <strong className="text-text-primary">{investigation.related_records.customer_order_count}</strong>
            </div>
            <div className="p-2 bg-background-primary rounded border border-border-subtle">
              <span className="text-text-muted text-[10px] block">Total Refunds</span>
              <strong className="text-text-primary">{investigation.related_records.total_refunds_count}</strong>
            </div>
            <div className="p-2 bg-background-primary rounded border border-border-subtle">
              <span className="text-text-muted text-[10px] block">Account Age</span>
              <strong className="text-text-primary">{investigation.related_records.account_age_days} days</strong>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
