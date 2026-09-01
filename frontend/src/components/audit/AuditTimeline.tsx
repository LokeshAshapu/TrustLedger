import React from "react";
import { CheckCircle2, AlertTriangle, ShieldX, Info, Clock } from "lucide-react";
import type { AuditTimelineEvent } from "../../data/mock/explorer-data";

interface AuditTimelineProps {
  events: AuditTimelineEvent[];
}

export const AuditTimeline: React.FC<AuditTimelineProps> = ({ events }) => {
  const statusIcons = {
    PASS: { icon: CheckCircle2, color: "text-verdict-approve", bg: "bg-verdict-approve/10" },
    WARNING: { icon: AlertTriangle, color: "text-verdict-review", bg: "bg-verdict-review/10" },
    FAIL: { icon: ShieldX, color: "text-verdict-block", bg: "bg-verdict-block/10" },
    INFO: { icon: Info, color: "text-accent-ai", bg: "bg-accent-ai/10" },
  };

  return (
    <div className="bg-background-surface/80 border border-border-subtle rounded-card p-4 space-y-3">
      <div className="flex items-center justify-between border-b border-border-subtle pb-2">
        <div className="flex items-center gap-2 text-xs font-mono font-bold text-text-primary uppercase">
          <Clock className="h-4 w-4 text-accent-infra" />
          <span>CANONICAL DECISION RECONSTRUCTION TIMELINE</span>
        </div>
        <span className="text-[10px] font-mono text-text-muted">High-Precision Microsecond Log</span>
      </div>

      <div className="relative pl-6 space-y-3 border-l border-border-subtle text-xs font-mono">
        {events.map((evt, idx) => {
          const st = statusIcons[evt.status];
          const Icon = st.icon;
          return (
            <div key={idx} className="relative group">
              <div className={`absolute -left-[31px] top-0.5 p-1 rounded-full border border-border-subtle bg-background-primary ${st.color}`}>
                <Icon className="h-3.5 w-3.5" />
              </div>
              <div className="p-2.5 rounded bg-background-primary border border-border-subtle flex flex-col space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-text-primary">{evt.stage}</span>
                  <span className="text-[10px] text-text-muted">{evt.time}</span>
                </div>
                <p className="text-[11px] text-text-secondary">{evt.detail}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
