import React from "react";

interface PrimaryMetricCardProps {
  number: string;
  title: string;
  value: React.ReactNode;
  subtitle: string;
  badgeText?: string;
  variant?: "approve" | "review" | "block" | "infra" | "default";
}

export const PrimaryMetricCard: React.FC<PrimaryMetricCardProps> = ({
  number,
  title,
  value,
  subtitle,
  badgeText,
  variant = "default",
}) => {
  const variantStyles = {
    approve: "border-verdict-approve/30 bg-verdict-approve/5 hover:border-verdict-approve/50 shadow-glowApprove",
    review: "border-verdict-review/30 bg-verdict-review/5 hover:border-verdict-review/50 shadow-glowReview",
    block: "border-verdict-block/30 bg-verdict-block/5 hover:border-verdict-block/50 shadow-glowBlock",
    infra: "border-accent-infra/30 bg-accent-infra/5 hover:border-accent-infra/50 shadow-glowAI",
    default: "border-border-subtle bg-background-surface/80 hover:border-border-active",
  };

  const numberColors = {
    approve: "text-verdict-approve",
    review: "text-verdict-review",
    block: "text-verdict-block",
    infra: "text-accent-infra",
    default: "text-text-muted",
  };

  return (
    <div
      className={`flex flex-col justify-between p-5 rounded-card border transition-all duration-200 ${variantStyles[variant]}`}
    >
      <div className="flex items-center justify-between">
        <span className={`font-mono text-xs font-bold tracking-widest ${numberColors[variant]}`}>
          {number}
        </span>
        {badgeText && (
          <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-background-primary border border-border-subtle text-text-secondary">
            {badgeText}
          </span>
        )}
      </div>

      <div className="my-3 space-y-1">
        <h3 className="text-xs font-mono font-semibold text-text-muted uppercase tracking-wider">
          {title}
        </h3>
        <div className="text-2xl font-mono font-extrabold text-text-primary tracking-tight">
          {value}
        </div>
      </div>

      <div className="text-[11px] font-mono text-text-secondary border-t border-border-subtle/50 pt-2 flex items-center justify-between">
        <span>{subtitle}</span>
        <span className="text-[10px] text-text-muted">Phase 8.1 Data</span>
      </div>
    </div>
  );
};
