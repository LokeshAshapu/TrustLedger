import React from "react";
import { HelpCircle, AlertTriangle, FileQuestion } from "lucide-react";
import type { ReviewContextDetails } from "../../data/mock/investigations";

interface ReviewContextCardProps {
  reviewContext: ReviewContextDetails;
}

export const ReviewContextCard: React.FC<ReviewContextCardProps> = ({
  reviewContext,
}) => {
  return (
    <div className="bg-background-surface/90 border border-verdict-review/40 rounded-card p-5 space-y-4 shadow-glowReview">
      <div className="flex items-center justify-between border-b border-border-subtle pb-3">
        <div className="flex items-center gap-2 text-xs font-mono font-bold text-verdict-review uppercase tracking-wider">
          <HelpCircle className="h-5 w-5" />
          <span>HUMAN REVIEW CONTEXT & REVIEWER QUESTIONS</span>
        </div>
        <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-verdict-review/10 text-verdict-review border border-verdict-review/30">
          ACTION REQUIRED
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
        {/* Left: Reviewer Questions */}
        <div className="space-y-2">
          <span className="text-text-primary font-bold flex items-center gap-1.5">
            <FileQuestion className="h-4 w-4 text-verdict-review" />
            <span>Deterministic Reviewer Questions:</span>
          </span>
          <ul className="space-y-1.5 text-text-secondary list-disc list-inside bg-background-primary p-3 rounded border border-border-subtle">
            {reviewContext.reviewer_questions.map((q, idx) => (
              <li key={idx} className="leading-relaxed">{q}</li>
            ))}
          </ul>
        </div>

        {/* Right: Missing Information & Conflicting Signals */}
        <div className="space-y-3">
          <div className="space-y-1">
            <span className="text-text-muted font-semibold">Missing Information:</span>
            <div className="p-2.5 bg-background-primary rounded border border-border-subtle text-text-secondary">
              {reviewContext.missing_information.join(", ") || "None"}
            </div>
          </div>

          <div className="space-y-1">
            <span className="text-verdict-review font-semibold flex items-center gap-1">
              <AlertTriangle className="h-3.5 w-3.5" />
              <span>Conflicting Signals:</span>
            </span>
            <div className="p-2.5 bg-background-primary rounded border border-border-subtle text-verdict-review">
              {reviewContext.conflicting_signals.join(", ") || "None"}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
