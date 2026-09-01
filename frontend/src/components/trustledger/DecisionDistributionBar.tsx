import React from "react";
import { PieChart } from "lucide-react";

interface VerdictDistribution {
  APPROVE: number;
  REVIEW: number;
  BLOCK: number;
  total: number;
}

interface DecisionDistributionBarProps {
  distribution: VerdictDistribution;
}

export const DecisionDistributionBar: React.FC<DecisionDistributionBarProps> = ({
  distribution,
}) => {
  const { APPROVE, REVIEW, BLOCK, total } = distribution;

  const appPct = total > 0 ? (APPROVE / total) * 100 : 0;
  const revPct = total > 0 ? (REVIEW / total) * 100 : 0;
  const blkPct = total > 0 ? (BLOCK / total) * 100 : 0;

  return (
    <div className="bg-background-surface/80 border border-border-subtle rounded-card p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <PieChart className="h-4 w-4 text-accent-infra" />
          <h3 className="text-xs font-mono font-bold text-text-primary uppercase tracking-wider">
            DECISION VERDICT DISTRIBUTION
          </h3>
        </div>
        <span className="text-xs font-mono text-text-muted">
          {total.toLocaleString()} Total Held-Out Decisions
        </span>
      </div>

      {/* Segmented Horizontal Distribution Bar */}
      <div className="h-3 w-full bg-background-primary rounded-full overflow-hidden flex p-0.5 border border-border-subtle">
        <div
          className="h-full bg-verdict-approve rounded-l-full transition-all duration-300"
          style={{ width: `${appPct}%` }}
          title={`APPROVE: ${APPROVE} (${appPct.toFixed(1)}%)`}
        />
        <div
          className="h-full bg-verdict-review transition-all duration-300"
          style={{ width: `${revPct}%` }}
          title={`REVIEW: ${REVIEW} (${revPct.toFixed(1)}%)`}
        />
        <div
          className="h-full bg-verdict-block rounded-r-full transition-all duration-300"
          style={{ width: `${blkPct}%` }}
          title={`BLOCK: ${BLOCK} (${blkPct.toFixed(1)}%)`}
        />
      </div>

      {/* Breakdown Legend Cards */}
      <div className="grid grid-cols-3 gap-2 pt-1 font-mono text-xs">
        <div className="p-2 rounded bg-background-primary border border-verdict-approve/20 flex flex-col">
          <div className="flex items-center justify-between text-verdict-approve font-bold">
            <span>● APPROVE</span>
            <span>{appPct.toFixed(1)}%</span>
          </div>
          <span className="text-[11px] text-text-muted mt-0.5">{APPROVE} Decisions</span>
        </div>

        <div className="p-2 rounded bg-background-primary border border-verdict-review/20 flex flex-col">
          <div className="flex items-center justify-between text-verdict-review font-bold">
            <span>● REVIEW</span>
            <span>{revPct.toFixed(1)}%</span>
          </div>
          <span className="text-[11px] text-text-muted mt-0.5">{REVIEW} Decisions</span>
        </div>

        <div className="p-2 rounded bg-background-primary border border-verdict-block/20 flex flex-col">
          <div className="flex items-center justify-between text-verdict-block font-bold">
            <span>● BLOCK</span>
            <span>{blkPct.toFixed(1)}%</span>
          </div>
          <span className="text-[11px] text-text-muted mt-0.5">{BLOCK} Decisions</span>
        </div>
      </div>
    </div>
  );
};
