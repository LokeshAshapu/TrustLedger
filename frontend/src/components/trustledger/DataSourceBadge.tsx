import React from "react";
import { Server, Database, Flame } from "lucide-react";

export type DataSourceType = "LIVE_BACKEND" | "HELD_OUT_BENCHMARK" | "SIMULATION";

interface DataSourceBadgeProps {
  type: DataSourceType;
  labelOverride?: string;
}

export const DataSourceBadge: React.FC<DataSourceBadgeProps> = ({ type, labelOverride }) => {
  const badgeConfig = {
    LIVE_BACKEND: {
      label: labelOverride || "LIVE BACKEND",
      icon: Server,
      color: "text-verdict-approve bg-verdict-approve/10 border-verdict-approve/40 shadow-glowApprove",
    },
    HELD_OUT_BENCHMARK: {
      label: labelOverride || "HELD-OUT BENCHMARK",
      icon: Database,
      color: "text-accent-infra bg-accent-infra/10 border-accent-infra/40 shadow-glowAI",
    },
    SIMULATION: {
      label: labelOverride || "SIMULATION",
      icon: Flame,
      color: "text-accent-ai bg-accent-ai/10 border-accent-ai/40",
    },
  };

  const config = badgeConfig[type];
  const Icon = config.icon;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-extrabold uppercase border ${config.color}`}
    >
      <Icon className="h-3 w-3" />
      <span>{config.label}</span>
    </span>
  );
};
