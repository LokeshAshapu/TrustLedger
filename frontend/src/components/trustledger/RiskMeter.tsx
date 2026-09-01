import React from "react";
import { ShieldAlert } from "lucide-react";

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

interface RiskMeterProps {
  level: RiskLevel;
  score?: number;
  showScore?: boolean;
}

export const RiskMeter: React.FC<RiskMeterProps> = ({
  level,
  score,
  showScore = true,
}) => {
  const levelMap = {
    LOW: { color: "text-verdict-approve", bg: "bg-verdict-approve", border: "border-verdict-approve/20" },
    MEDIUM: { color: "text-verdict-review", bg: "bg-verdict-review", border: "border-verdict-review/20" },
    HIGH: { color: "text-amber-500", bg: "bg-amber-500", border: "border-amber-500/20" },
    CRITICAL: { color: "text-verdict-block", bg: "bg-verdict-block", border: "border-verdict-block/20" },
  };

  const style = levelMap[level] || levelMap.LOW;
  const normalizedScore = score !== undefined ? Math.min(Math.max(score, 0), 1) : 0;
  const pct = Math.round(normalizedScore * 100);

  return (
    <div className={`inline-flex items-center gap-2 rounded-lg bg-background-surface/80 px-2.5 py-1 border ${style.border}`}>
      <ShieldAlert className={`h-3.5 w-3.5 ${style.color}`} />
      <div className="flex flex-col">
        <div className="flex items-center gap-1.5 text-xs font-semibold">
          <span className={`${style.color} uppercase tracking-wider font-mono`}>{level} RISK</span>
          {showScore && score !== undefined && (
            <span className="text-text-muted font-mono text-[11px]">({pct}%)</span>
          )}
        </div>
        <div className="mt-0.5 h-1 w-20 rounded-full bg-background-hover overflow-hidden">
          <div
            className={`h-full rounded-full ${style.bg} transition-all duration-300`}
            style={{ width: `${Math.max(pct, 8)}%` }}
          />
        </div>
      </div>
    </div>
  );
};
