import React, { useMemo } from "react";
import { PlayCircle, Flame } from "lucide-react";
import { TrustLedgerAPI } from "../lib/trustledger-api";
import { BoundedSimulatorPanel } from "../components/simulator/BoundedSimulatorPanel";
import { ErrorState } from "../components/ui/ErrorState";

export const SimulatorPage: React.FC = () => {
  const scenarios = useMemo(() => {
    try {
      return TrustLedgerAPI.getSimulationScenarios();
    } catch (err) {
      console.error("Simulation Scenarios Error:", err);
      return null;
    }
  }, []);

  if (!scenarios) {
    return (
      <ErrorState
        title="SIMULATOR DATA UNRETRIEVABLE"
        description="Could not load bounded simulator scenarios."
        onRetry={() => window.location.reload()}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* 1. Header */}
      <div className="bg-background-surface/80 border border-border-subtle rounded-card p-5 flex items-center justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <PlayCircle className="h-4 w-4 text-accent-infra" />
            <span className="text-xs font-mono font-bold text-accent-infra uppercase tracking-widest">
              BOUNDED SYNTHETIC FINANCIAL EXECUTION SIMULATOR
            </span>
          </div>
          <h2 className="text-xl font-mono font-extrabold text-text-primary tracking-tight">
            NON-BYPASS EXECUTION BOUNDARY DEMO
          </h2>
          <p className="text-xs text-text-muted">
            Demonstrate that AI output alone can never authorize financial execution. Zero real money moved.
          </p>
        </div>

        <div className="hidden sm:flex items-center gap-2 font-mono text-xs text-accent-infra border border-accent-infra/30 px-3 py-1.5 rounded-full bg-accent-infra/10">
          <Flame className="h-4 w-4" />
          <span>SIMULATION ONLY</span>
        </div>
      </div>

      {/* 2. Interactive Bounded Simulator Panel */}
      <BoundedSimulatorPanel scenarios={scenarios} />
    </div>
  );
};
