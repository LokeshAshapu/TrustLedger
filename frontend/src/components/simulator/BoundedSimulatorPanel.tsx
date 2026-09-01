import React, { useState } from "react";
import { PlayCircle, Flame, ShieldAlert, CheckCircle2, AlertOctagon, RotateCw, Lock } from "lucide-react";
import { MoneyDisplay } from "../trustledger/MoneyDisplay";
import { StatusBadge } from "../trustledger/StatusBadge";
import { AISignalBadge } from "../trustledger/AISignalBadge";
import type { SimulationScenarioItem } from "../../data/mock/explorer-data";

interface SimulationEvent {
  time: string;
  scenarioId: string;
  action: string;
  status: "AUTHORIZED" | "EXECUTED_SIMULATION" | "BLOCKED" | "FAILED_SIMULATION";
  detail: string;
}

interface BoundedSimulatorPanelProps {
  scenarios: SimulationScenarioItem[];
}

export const BoundedSimulatorPanel: React.FC<BoundedSimulatorPanelProps> = ({
  scenarios,
}) => {
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>("sim_scen_override_01");
  const [executionStates, setExecutionStates] = useState<Record<string, "IDLE" | "EXECUTING" | "EXECUTED_SIMULATION" | "FAILED_SIMULATION" | "BLOCKED">>({
    sim_scen_override_01: "BLOCKED",
    sim_scen_stale_03: "BLOCKED",
  });
  const [eventLogs, setEventLogs] = useState<SimulationEvent[]>([
    {
      time: new Date().toLocaleTimeString(),
      scenarioId: "sim_scen_override_01",
      action: "EXECUTION_ATTEMPT",
      status: "BLOCKED",
      detail: "DENIED: Hard policy rule TL-DG-002 limit exceeded. No valid ExecutionAuthorization token.",
    },
  ]);

  const activeScenario = scenarios.find((s) => s.id === selectedScenarioId) || scenarios[0];
  const activeState = executionStates[activeScenario.id] || (activeScenario.can_simulate ? "IDLE" : "BLOCKED");

  const handleSimulateExecution = (scen: SimulationScenarioItem) => {
    if (!scen.can_simulate || scen.verdict !== "APPROVE") return;

    setExecutionStates((prev) => ({ ...prev, [scen.id]: "EXECUTING" }));

    setTimeout(() => {
      if (scen.simulated_failure && executionStates[scen.id] !== "EXECUTED_SIMULATION") {
        setExecutionStates((prev) => ({ ...prev, [scen.id]: "FAILED_SIMULATION" }));
        setEventLogs((prev) => [
          {
            time: new Date().toLocaleTimeString(),
            scenarioId: scen.id,
            action: "SIMULATED_EXECUTION",
            status: "FAILED_SIMULATION",
            detail: "SIMULATED_GATEWAY_TIMEOUT: Synthetic payment gateway simulation timed out.",
          },
          ...prev,
        ]);
      } else {
        setExecutionStates((prev) => ({ ...prev, [scen.id]: "EXECUTED_SIMULATION" }));
        setEventLogs((prev) => [
          {
            time: new Date().toLocaleTimeString(),
            scenarioId: scen.id,
            action: "SIMULATED_EXECUTION",
            status: "EXECUTED_SIMULATION",
            detail: `EXECUTED_SIMULATION: Synthetic balance updated. Reference: sim_tx_${Math.floor(100000 + Math.random() * 900000)}`,
          },
          ...prev,
        ]);
      }
    }, 400);
  };

  return (
    <div className="space-y-4">
      {/* Simulation Banner Notice */}
      <div className="bg-accent-infra/10 border border-accent-infra/40 rounded-card p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-glowAI">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-accent-infra/20 rounded-lg text-accent-infra">
            <Flame className="h-6 w-6" />
          </div>
          <div className="flex flex-col">
            <span className="text-xs font-mono font-bold text-accent-infra uppercase tracking-wider">
              BOUNDED SYNTHETIC FINANCIAL EXECUTION SIMULATOR
            </span>
            <span className="text-xs text-text-muted">
              Strict Non-Bypass Architecture: Only APPROVE decisions with valid ExecutionAuthorization tokens may execute on synthetic local ledger. Zero real money moved.
            </span>
          </div>
        </div>
        <span className="text-xs font-mono font-extrabold text-accent-infra border border-accent-infra/30 px-3 py-1 rounded-full bg-accent-infra/5 shrink-0">
          SIMULATION ONLY • NO REAL MONEY
        </span>
      </div>

      {/* Scenario Selector Tabs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2">
        {scenarios.map((scen) => {
          const isSelected = selectedScenarioId === scen.id;
          return (
            <button
              key={scen.id}
              onClick={() => setSelectedScenarioId(scen.id)}
              className={`p-3 rounded-card border text-left flex flex-col justify-between space-y-2 transition-all ${
                isSelected
                  ? "bg-background-surface border-accent-infra ring-2 ring-accent-infra/30 shadow-glowAI"
                  : "bg-background-surface/60 border-border-subtle hover:border-border-active"
              }`}
            >
              <div className="flex items-center justify-between">
                <StatusBadge verdict={scen.verdict} size="sm" />
                <span className="text-[10px] font-mono text-text-muted">{scen.action_type}</span>
              </div>
              <span className="text-xs font-mono font-bold text-text-primary line-clamp-2">{scen.title}</span>
              <MoneyDisplay amountMinor={scen.amount_minor} size="sm" />
            </button>
          );
        })}
      </div>

      {/* Active Scenario Execution Details */}
      <div className="bg-background-surface/90 border border-border-subtle rounded-card p-5 space-y-4 shadow-panel">
        <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-border-subtle pb-3 gap-2">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-xs font-mono text-text-muted">
              <span>SCENARIO DETAIL:</span>
              <span className="text-text-primary font-bold">{activeScenario.id}</span>
            </div>
            <h3 className="text-sm font-mono font-extrabold text-text-primary tracking-tight">
              {activeScenario.title}
            </h3>
          </div>

          <div className="flex items-center gap-3 font-mono text-xs">
            <AISignalBadge recommendation={activeScenario.ai_recommendation} confidence={activeScenario.ai_confidence} />
            <StatusBadge verdict={activeScenario.verdict} size="md" />
          </div>
        </div>

        <p className="text-xs font-mono text-text-secondary leading-relaxed bg-background-primary p-3 rounded border border-border-subtle">
          {activeScenario.description}
        </p>

        {/* Execution Boundary State & Controls */}
        <div className="p-4 bg-background-primary rounded-card border border-border-subtle flex flex-col md:flex-row items-center justify-between gap-4 font-mono">
          <div className="space-y-1 text-xs">
            <span className="text-text-muted uppercase text-[10px]">Authorization Boundary State:</span>
            <div className="flex items-center gap-2">
              <Lock className="h-4 w-4 text-accent-infra" />
              <span className={`font-bold uppercase text-sm ${activeScenario.verdict === "APPROVE" ? "text-verdict-approve" : "text-verdict-block"}`}>
                {activeScenario.authorization_state}
              </span>
            </div>
          </div>

          {/* Action Triggers */}
          <div className="flex items-center gap-3">
            {activeScenario.verdict !== "APPROVE" ? (
              <div className="px-4 py-2 rounded bg-verdict-block/10 border border-verdict-block/30 text-verdict-block font-bold text-xs flex items-center gap-2">
                <AlertOctagon className="h-4 w-4" />
                <span>DENIED: NO VALID EXECUTION AUTHORIZATION</span>
              </div>
            ) : activeState === "EXECUTED_SIMULATION" ? (
              <div className="px-4 py-2 rounded bg-verdict-approve/10 border border-verdict-approve/30 text-verdict-approve font-bold text-xs flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4" />
                <span>EXECUTED_SIMULATION SUCCESS</span>
              </div>
            ) : activeState === "FAILED_SIMULATION" ? (
              <button
                onClick={() => handleSimulateExecution(activeScenario)}
                className="px-4 py-2 rounded bg-verdict-review/20 border border-verdict-review/50 text-verdict-review font-bold text-xs hover:bg-verdict-review/30 flex items-center gap-2 transition-colors"
              >
                <RotateCw className="h-4 w-4" />
                <span>RETRY SIMULATION</span>
              </button>
            ) : (
              <button
                onClick={() => handleSimulateExecution(activeScenario)}
                disabled={activeState === "EXECUTING"}
                className="px-5 py-2.5 rounded-control bg-accent-infra/20 border border-accent-infra/50 text-accent-infra font-extrabold text-xs hover:bg-accent-infra/30 transition-all flex items-center gap-2 shadow-glowAI"
              >
                <PlayCircle className="h-4 w-4" />
                <span>{activeState === "EXECUTING" ? "Simulating..." : "SIMULATE EXECUTION"}</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Simulation Event Audit Log */}
      <div className="bg-background-surface/80 border border-border-subtle rounded-card p-4 space-y-3">
        <div className="flex items-center justify-between border-b border-border-subtle pb-2">
          <h4 className="text-xs font-mono font-bold text-text-primary uppercase tracking-wider flex items-center gap-2">
            <ShieldAlert className="h-4 w-4 text-accent-infra" />
            <span>SIMULATION EVENT LOG (IN-MEMORY DEMO AUDIT)</span>
          </h4>
          <span className="text-[10px] font-mono text-text-muted">{eventLogs.length} Event(s)</span>
        </div>

        <div className="space-y-1.5 font-mono text-xs max-h-48 overflow-y-auto">
          {eventLogs.map((log, idx) => (
            <div key={idx} className="p-2 rounded bg-background-primary border border-border-subtle flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-text-muted">{log.time}</span>
                <span className={`px-1.5 py-0.5 text-[10px] font-bold rounded ${log.status === "EXECUTED_SIMULATION" ? "bg-verdict-approve/10 text-verdict-approve" : "bg-verdict-block/10 text-verdict-block"}`}>
                  {log.status}
                </span>
                <span className="text-text-primary">{log.detail}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
