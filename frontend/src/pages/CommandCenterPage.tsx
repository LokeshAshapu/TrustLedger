import React, { useMemo } from "react";
import { TrustLedgerAPI } from "../lib/trustledger-api";
import { PrimaryMetricCard } from "../components/trustledger/PrimaryMetricCard";
import { FinancialSafetyPanel } from "../components/trustledger/FinancialSafetyPanel";
import { DecisionDistributionBar } from "../components/trustledger/DecisionDistributionBar";
import { LiveDecisionFeed } from "../components/trustledger/LiveDecisionFeed";
import { DecisionTraceShell } from "../components/trustledger/DecisionTraceShell";
import { BenchmarkIntegrityPanel } from "../components/trustledger/BenchmarkIntegrityPanel";
import { LiveVerificationRunner } from "../components/trustledger/LiveVerificationRunner";
import { DataSourceBadge } from "../components/trustledger/DataSourceBadge";
import { MoneyDisplay } from "../components/trustledger/MoneyDisplay";
import { ErrorState } from "../components/ui/ErrorState";

export const CommandCenterPage: React.FC = () => {
  // Retrieve verified evaluation snapshot with runtime invariant assertions
  const snapshot = useMemo(() => {
    try {
      return TrustLedgerAPI.getEvaluationSnapshot();
    } catch (err) {
      console.error("Evaluation Data Error:", err);
      return null;
    }
  }, []);

  if (!snapshot) {
    return (
      <ErrorState
        title="EVALUATION SNAPSHOT DATA INTEGRITY ERROR"
        description="The frontend evaluation data adapter detected a metric invariant failure or corrupted snapshot payload."
        onRetry={() => window.location.reload()}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* 1. Hero Header & Data Source Badges */}
      <div className="bg-background-surface/80 border border-border-subtle rounded-card p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-verdict-approve animate-pulse" />
            <span className="text-xs font-mono font-bold text-accent-infra uppercase tracking-widest">
              TRUSTLEDGER CONTROL PLANE
            </span>
          </div>
          <h2 className="text-xl font-mono font-extrabold text-text-primary tracking-tight">
            TRUSTLEDGER COMMAND CENTER
          </h2>
          <p className="text-xs text-text-muted max-w-xl">
            Verify before AI moves money. Real-time decision verification, policy evaluation, and financial execution boundary control.
          </p>
        </div>

        <div className="flex flex-col md:items-end gap-1.5">
          <DataSourceBadge type="HELD_OUT_BENCHMARK" />
          <span className="text-[11px] text-text-muted font-mono">
            1,500 Held-Out Benchmark Cases Baseline
          </span>
        </div>
      </div>

      {/* 2. Interactive Real Backend Decision Verification Runner */}
      <LiveVerificationRunner />

      {/* 3. Primary 4-Metric Hierarchy Cards (Held-Out Benchmark Baseline) */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-mono font-bold text-text-secondary uppercase tracking-wider">
            HELD-OUT EVALUATION BENCHMARK METRICS (PHASE 8.1 FROZEN BASELINE)
          </h3>
          <DataSourceBadge type="HELD_OUT_BENCHMARK" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <PrimaryMetricCard
            number="01"
            title="PROTECTED EXPOSURE"
            value={<MoneyDisplay amountMinor={snapshot.unsafeExposureBlockedMinor} size="xl" isExposure />}
            subtitle="Unsafe potential exposure blocked"
            badgeText="100% BLOCKED"
            variant="block"
          />

          <PrimaryMetricCard
            number="02"
            title="UNSAFE APPROVALS"
            value={`${snapshot.unsafeApprovalRate.toFixed(2)}%`}
            subtitle="0 of 637 unsafe cases approved"
            badgeText="PERFECT SAFETY"
            variant="approve"
          />

          <PrimaryMetricCard
            number="03"
            title="DECISION ACCURACY"
            value={`${snapshot.decisionAccuracy.toFixed(2)}%`}
            subtitle="1,436 / 1,500 exact verdict matches"
            badgeText="95.65% MACRO F1"
            variant="infra"
          />

          <PrimaryMetricCard
            number="04"
            title="REVIEW RATE"
            value={`${snapshot.reviewRate.toFixed(2)}%`}
            subtitle="284 Cases routed to human review"
            badgeText="90.16% RECALL"
            variant="review"
          />
        </div>
      </div>

      {/* 4. Financial Safety Panel */}
      <FinancialSafetyPanel
        unsafeExposureApproved={snapshot.unsafeExposureApprovedMinor}
        unsafeExposureBlocked={snapshot.unsafeExposureBlockedMinor}
        blockRecall={snapshot.blockRecall}
      />

      {/* 5. Decision Verdict Distribution */}
      <DecisionDistributionBar distribution={snapshot.verdictDistribution} />

      {/* 6. Live Decision Feed & Signal Comparison */}
      <LiveDecisionFeed />

      {/* 7. Verification Pipeline Overview */}
      <DecisionTraceShell />

      {/* 8. Benchmark Integrity & Credibility Panel */}
      <BenchmarkIntegrityPanel
        testCases={snapshot.testCases}
        adversarialPassed={snapshot.adversarialPassed}
        adversarialTotal={snapshot.adversarialTotal}
        invariantsPassed={snapshot.invariantsPassed}
        invariantsTotal={snapshot.invariantsTotal}
        reproducibilityPct={snapshot.reproducibilityPct}
        falseBlockRate={snapshot.falseBlockRate}
      />
    </div>
  );
};
