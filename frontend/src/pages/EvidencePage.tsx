import React, { useMemo, useState } from "react";
import { Database, CheckCircle2, AlertTriangle, ShieldX, ArrowUpRight } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { TrustLedgerAPI } from "../lib/trustledger-api";
import { EvidenceGraph } from "../components/evidence/EvidenceGraph";
import { EvidenceConflictCard } from "../components/evidence/EvidenceConflictCard";
import { DataSourceBadge } from "../components/trustledger/DataSourceBadge";
import { ErrorState } from "../components/ui/ErrorState";

export const EvidencePage: React.FC = () => {
  const navigate = useNavigate();
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");

  const evidenceData = useMemo(() => {
    try {
      return TrustLedgerAPI.getEvidenceExplorerData();
    } catch (err) {
      console.error("Evidence Explorer Error:", err);
      return null;
    }
  }, []);

  if (!evidenceData) {
    return (
      <ErrorState
        title="EVIDENCE DATA UNRETRIEVABLE"
        description="Could not load control plane evidence explorer dataset."
        onRetry={() => window.location.reload()}
      />
    );
  }

  const { summary, artifacts } = evidenceData;

  const rawFiltered = selectedStatus === "ALL"
    ? artifacts
    : artifacts.filter((a: any) => a.status === selectedStatus);
  const filteredArtifacts: any[] = rawFiltered as any[];

  return (
    <div className="space-y-6">
      {/* 1. Evidence Control Header */}
      <div className="bg-background-surface/80 border border-border-subtle rounded-card p-5 flex items-center justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Database className="h-4 w-4 text-accent-infra" />
            <span className="text-xs font-mono font-bold text-accent-infra uppercase tracking-widest">
              EVIDENCE PROVENANCE & FRESHNESS EXPLORER
            </span>
          </div>
          <h2 className="text-xl font-mono font-extrabold text-text-primary tracking-tight">
            EVIDENCE PROVENANCE & FRESHNESS CONTROL
          </h2>
          <p className="text-xs text-text-muted max-w-xl">
            Inspect verified evidence, stale artifacts (&gt;30 days old), signal conflicts, and multi-ledger evidence linkage graph.
          </p>
        </div>

        <DataSourceBadge type="HELD_OUT_BENCHMARK" />
      </div>

      {/* 2. 4 Overview Status Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <button
          onClick={() => setSelectedStatus("VERIFIED")}
          className={`p-4 rounded-card border font-mono text-left transition-all ${
            selectedStatus === "VERIFIED"
              ? "bg-verdict-approve/15 border-verdict-approve ring-1 ring-verdict-approve"
              : "bg-background-surface/80 border-border-subtle hover:border-border-active"
          }`}
        >
          <div className="flex items-center justify-between text-xs text-text-muted mb-1">
            <span className="font-bold uppercase">VERIFIED</span>
            <CheckCircle2 className="h-4 w-4 text-verdict-approve" />
          </div>
          <div className="text-2xl font-extrabold text-verdict-approve">{summary.verified_count.toLocaleString()}</div>
          <div className="text-[10px] text-text-muted mt-1">Fresh & verified artifacts</div>
        </button>

        <button
          onClick={() => setSelectedStatus("STALE")}
          className={`p-4 rounded-card border font-mono text-left transition-all ${
            selectedStatus === "STALE"
              ? "bg-verdict-review/15 border-verdict-review ring-1 ring-verdict-review"
              : "bg-background-surface/80 border-border-subtle hover:border-border-active"
          }`}
        >
          <div className="flex items-center justify-between text-xs text-text-muted mb-1">
            <span className="font-bold uppercase">STALE (&gt;30 DAYS)</span>
            <AlertTriangle className="h-4 w-4 text-verdict-review" />
          </div>
          <div className="text-2xl font-extrabold text-verdict-review">{summary.stale_count.toLocaleString()}</div>
          <div className="text-[10px] text-text-muted mt-1">Triggers human review</div>
        </button>

        <button
          onClick={() => setSelectedStatus("CONFLICTING")}
          className={`p-4 rounded-card border font-mono text-left transition-all ${
            selectedStatus === "CONFLICTING"
              ? "bg-verdict-block/15 border-verdict-block ring-1 ring-verdict-block"
              : "bg-background-surface/80 border-border-subtle hover:border-border-active"
          }`}
        >
          <div className="flex items-center justify-between text-xs text-text-muted mb-1">
            <span className="font-bold uppercase">CONFLICTING</span>
            <ShieldX className="h-4 w-4 text-verdict-block" />
          </div>
          <div className="text-2xl font-extrabold text-verdict-block">{summary.conflicting_count.toLocaleString()}</div>
          <div className="text-[10px] text-text-muted mt-1">Courier vs Support mismatch</div>
        </button>

        <button
          onClick={() => setSelectedStatus("MISSING")}
          className={`p-4 rounded-card border font-mono text-left transition-all ${
            selectedStatus === "MISSING"
              ? "bg-accent-infra/15 border-accent-infra ring-1 ring-accent-infra"
              : "bg-background-surface/80 border-border-subtle hover:border-border-active"
          }`}
        >
          <div className="flex items-center justify-between text-xs text-text-muted mb-1">
            <span className="font-bold uppercase">MISSING</span>
            <Database className="h-4 w-4 text-accent-infra" />
          </div>
          <div className="text-2xl font-extrabold text-accent-infra">{summary.missing_count.toLocaleString()}</div>
          <div className="text-[10px] text-text-muted mt-1">Unattached evidence IDs</div>
        </button>
      </div>

      {/* 3. Conflicting Evidence Signal Visualizer Card */}
      <EvidenceConflictCard />

      {/* 4. Multi-Ledger Evidence Linkage Graph */}
      <EvidenceGraph />

      {/* 5. Technical Registry Table */}
      <div className="bg-background-surface/80 border border-border-subtle rounded-card overflow-hidden">
        <div className="p-4 border-b border-border-subtle flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-mono font-bold text-text-primary uppercase">
            <Database className="h-4 w-4 text-accent-infra" />
            <span>TECHNICAL EVIDENCE REGISTRY</span>
          </div>
          <span className="text-xs font-mono text-text-muted">{filteredArtifacts.length} Artifact(s) Displayed</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs font-mono">
            <thead>
              <tr className="bg-background-secondary/80 border-b border-border-subtle text-text-muted uppercase font-semibold">
                <th className="py-3 px-4">Evidence ID</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Source System</th>
                <th className="py-3 px-4">Linked Decision</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Age (Days)</th>
                <th className="py-3 px-4 text-center">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle/50 text-text-primary">
              {filteredArtifacts.map((item) => (
                <tr key={item.evidence_id || item.id} className="hover:bg-background-hover/60 transition-colors">
                  <td className="py-3 px-4 font-bold text-accent-infra">{item.evidence_id || item.id}</td>
                  <td className="py-3 px-4 font-medium">{item.type}</td>
                  <td className="py-3 px-4 text-text-secondary">{item.source_system || item.source}</td>
                  <td className="py-3 px-4">
                    <button
                      onClick={() => navigate(`/decisions/${item.linked_decision_id || "dec_blk_pol_000042"}`)}
                      className="text-text-primary hover:text-accent-infra font-semibold underline decoration-border-subtle underline-offset-2"
                    >
                      {item.linked_decision_id || "dec_blk_pol_000042"}
                    </button>
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`px-2 py-0.5 text-[10px] font-bold rounded ${
                        item.status === "VERIFIED"
                          ? "bg-verdict-approve/10 text-verdict-approve"
                          : item.status === "STALE"
                          ? "bg-verdict-review/10 text-verdict-review"
                          : item.status === "CONFLICTING"
                          ? "bg-verdict-block/10 text-verdict-block"
                          : "bg-accent-infra/10 text-accent-infra"
                      }`}
                    >
                      {item.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right font-bold">{item.age_days || 1}d</td>
                  <td className="py-3 px-4 text-center">
                    <button
                      onClick={() => navigate(`/decisions/${item.linked_decision_id || "dec_blk_pol_000042"}`)}
                      className="text-text-muted hover:text-text-primary"
                    >
                      <ArrowUpRight className="h-4 w-4 inline-block" />
                    </button>
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
