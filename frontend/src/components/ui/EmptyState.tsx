import React from "react";
import { Inbox } from "lucide-react";

interface EmptyStateProps {
  title?: string;
  description?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = "NO ACTIVE INVESTIGATIONS",
  description = "All currently loaded financial action requests have completed deterministic verification.",
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center bg-background-surface/40 border border-border-subtle rounded-card space-y-3">
      <div className="p-3 bg-background-hover rounded-full border border-border-subtle">
        <Inbox className="h-6 w-6 text-text-muted stroke-[1.5]" />
      </div>
      <div className="space-y-1">
        <h4 className="text-xs font-mono font-bold text-text-primary tracking-wider uppercase">{title}</h4>
        <p className="text-xs text-text-muted max-w-sm">{description}</p>
      </div>
    </div>
  );
};
