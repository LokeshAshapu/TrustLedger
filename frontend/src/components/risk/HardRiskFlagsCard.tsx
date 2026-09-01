import React from "react";
import { ShieldAlert, Lock } from "lucide-react";

interface HardFlagItem {
  flag: string;
  description: string;
  count: number;
}

interface HardRiskFlagsCardProps {
  flags: HardFlagItem[];
}

export const HardRiskFlagsCard: React.FC<HardRiskFlagsCardProps> = ({ flags }) => {
  return (
    <div className="bg-background-surface/80 border border-verdict-block/40 rounded-card p-4 space-y-3 shadow-glowBlock">
      <div className="flex items-center justify-between border-b border-border-subtle pb-2">
        <div className="flex items-center gap-2 text-xs font-mono font-bold text-verdict-block uppercase">
          <ShieldAlert className="h-4 w-4" />
          <span>DETERMINISTIC HARD RISK FLAGS</span>
        </div>
        <span className="text-[10px] font-mono text-verdict-block font-bold px-2 py-0.5 rounded bg-verdict-block/10 border border-verdict-block/30">
          NON-OVERRIDABLE
        </span>
      </div>

      <div className="space-y-2">
        {flags.map((item, idx) => (
          <div key={idx} className="p-3 bg-background-primary rounded border border-border-subtle flex items-center justify-between text-xs font-mono">
            <div className="flex flex-col">
              <span className="font-bold text-verdict-block">{item.flag}</span>
              <span className="text-text-muted text-[11px]">{item.description}</span>
            </div>
            <div className="px-2.5 py-1 rounded bg-background-surface border border-border-subtle text-text-primary font-bold">
              {item.count} Cases
            </div>
          </div>
        ))}
      </div>

      <div className="p-2.5 bg-background-primary rounded border border-border-subtle flex items-center justify-between text-xs font-mono text-text-secondary">
        <div className="flex items-center gap-2">
          <Lock className="h-4 w-4 text-accent-infra" />
          <span>Principle: <strong className="text-text-primary">Hard risk flags are deterministic safety signals. AI context cannot override them.</strong></span>
        </div>
        <span className="text-[10px] text-text-muted">Level 2 Safety</span>
      </div>
    </div>
  );
};
