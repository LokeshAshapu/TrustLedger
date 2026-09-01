import React from "react";
import { CheckCircle2, AlertTriangle, ShieldX } from "lucide-react";

export type FinalVerdict = "APPROVE" | "REVIEW" | "BLOCK";

interface StatusBadgeProps {
  verdict: FinalVerdict;
  size?: "sm" | "md" | "lg";
  showIcon?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  verdict,
  size = "md",
  showIcon = true,
}) => {
  const sizeClasses = {
    sm: "px-2 py-0.5 text-xs font-semibold gap-1",
    md: "px-2.5 py-1 text-xs font-bold gap-1.5",
    lg: "px-3.5 py-1.5 text-sm font-bold gap-2",
  };

  const styleMap = {
    APPROVE: {
      bg: "bg-verdict-approve/10 border-verdict-approve/30 text-verdict-approve shadow-glowApprove",
      icon: CheckCircle2,
      dot: "bg-verdict-approve",
    },
    REVIEW: {
      bg: "bg-verdict-review/10 border-verdict-review/30 text-verdict-review shadow-glowReview",
      icon: AlertTriangle,
      dot: "bg-verdict-review",
    },
    BLOCK: {
      bg: "bg-verdict-block/10 border-verdict-block/30 text-verdict-block shadow-glowBlock",
      icon: ShieldX,
      dot: "bg-verdict-block",
    },
  };

  const current = styleMap[verdict] || styleMap.REVIEW;
  const IconComponent = current.icon;

  return (
    <span
      className={`inline-flex items-center rounded-full border transition-colors ${sizeClasses[size]} ${current.bg}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${current.dot} animate-pulse`} />
      {showIcon && <IconComponent className="h-3.5 w-3.5 stroke-[2.5]" />}
      <span className="tracking-wide uppercase">{verdict}</span>
    </span>
  );
};
