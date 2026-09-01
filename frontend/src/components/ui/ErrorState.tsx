import React from "react";
import { AlertOctagon, RotateCw } from "lucide-react";

interface ErrorStateProps {
  title?: string;
  description?: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = "TRUSTLEDGER SERVICE UNAVAILABLE",
  description = "The control plane cannot retrieve the current decision state.",
  onRetry,
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center bg-verdict-block/5 border border-verdict-block/30 rounded-card space-y-3">
      <div className="p-3 bg-verdict-block/10 rounded-full border border-verdict-block/30">
        <AlertOctagon className="h-6 w-6 text-verdict-block stroke-[1.5]" />
      </div>
      <div className="space-y-1">
        <h4 className="text-xs font-mono font-bold text-verdict-block tracking-wider uppercase">{title}</h4>
        <p className="text-xs text-text-muted max-w-sm">{description}</p>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono font-semibold text-text-primary bg-background-surface hover:bg-background-hover border border-border-subtle rounded-control transition-colors"
        >
          <RotateCw className="h-3.5 w-3.5" />
          <span>Retry Connection</span>
        </button>
      )}
    </div>
  );
};
