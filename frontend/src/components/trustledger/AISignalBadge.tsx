import React from "react";
import { Sparkles, HelpCircle, AlertOctagon, PowerOff } from "lucide-react";

export type AIRecommendation = "SUPPORT" | "UNCERTAIN" | "CONTRADICT" | "AI_UNAVAILABLE";

interface AISignalBadgeProps {
  recommendation: AIRecommendation;
  confidence?: number;
}

export const AISignalBadge: React.FC<AISignalBadgeProps> = ({
  recommendation,
  confidence,
}) => {
  const signalMap = {
    SUPPORT: {
      label: "AI SIGNAL: SUPPORT",
      bg: "bg-accent-ai/10 border-accent-ai/30 text-accent-ai shadow-glowAI",
      icon: Sparkles,
    },
    UNCERTAIN: {
      label: "AI SIGNAL: UNCERTAIN",
      bg: "bg-verdict-review/10 border-verdict-review/30 text-verdict-review",
      icon: HelpCircle,
    },
    CONTRADICT: {
      label: "AI SIGNAL: CONTRADICT",
      bg: "bg-verdict-block/10 border-verdict-block/30 text-verdict-block",
      icon: AlertOctagon,
    },
    AI_UNAVAILABLE: {
      label: "AI SIGNAL: UNAVAILABLE",
      bg: "bg-text-muted/10 border-text-muted/30 text-text-muted",
      icon: PowerOff,
    },
  };

  const current = signalMap[recommendation] || signalMap.AI_UNAVAILABLE;
  const IconComponent = current.icon;
  const confPct = confidence !== undefined ? Math.round(confidence * 100) : null;

  return (
    <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-xs font-mono font-medium ${current.bg}`}>
      <IconComponent className="h-3.5 w-3.5" />
      <span>{current.label}</span>
      {confPct !== null && (
        <span className="opacity-75 font-sans">({confPct}%)</span>
      )}
    </div>
  );
};
