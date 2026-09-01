import React from "react";
import { Link } from "react-router-dom";
import { ShieldX, ArrowLeft } from "lucide-react";

export const NotFoundPage: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-4">
      <div className="p-4 bg-verdict-block/10 rounded-full border border-verdict-block/30 text-verdict-block">
        <ShieldX className="h-10 w-10 stroke-[1.5]" />
      </div>

      <div className="space-y-1">
        <h2 className="text-xl font-mono font-bold text-text-primary tracking-wider uppercase">
          404 — ROUTE NOT FOUND
        </h2>
        <p className="text-xs text-text-muted max-w-md font-mono">
          The requested control plane route does not exist or has been restricted by TrustLedger policy controls.
        </p>
      </div>

      <Link
        to="/command-center"
        className="inline-flex items-center gap-2 px-4 py-2 text-xs font-mono font-bold text-accent-infra bg-accent-infra/10 border border-accent-infra/30 hover:bg-accent-infra/20 rounded-control transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        <span>Return to Command Center</span>
      </Link>
    </div>
  );
};
