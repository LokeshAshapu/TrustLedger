import React, { useEffect, useState } from "react";
import { Server } from "lucide-react";
import { TrustLedgerAPI, type BackendHealthResponse } from "../../lib/trustledger-api";

export const SystemStatus: React.FC = () => {
  const [health, setHealth] = useState<BackendHealthResponse | null>(null);
  const [isOffline, setIsOffline] = useState<boolean>(false);

  useEffect(() => {
    let isMounted = true;
    const checkBackendHealth = async () => {
      try {
        const data = await TrustLedgerAPI.getHealth();
        if (isMounted) {
          setHealth(data);
          setIsOffline(false);
        }
      } catch (err) {
        if (isMounted) {
          setIsOffline(true);
        }
      }
    };

    checkBackendHealth();
    const interval = setInterval(checkBackendHealth, 15000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const providerName = health?.components?.ai_verifier?.configured_provider?.toUpperCase() || "MOCK";
  const label = isOffline ? "BACKEND OFFLINE" : `LIVE BACKEND • ${providerName}`;
  const dotColor = isOffline ? "bg-verdict-block" : "bg-verdict-approve";
  const textColor = isOffline ? "text-verdict-block" : "text-verdict-approve";

  return (
    <div className="flex items-center justify-between px-3 py-2 bg-background-surface/80 border border-border-subtle rounded-control text-xs font-mono">
      <div className="flex items-center gap-2">
        <span className={`h-2 w-2 rounded-full ${dotColor} animate-pulse`} />
        <span className={`font-extrabold tracking-wider ${textColor}`}>{label}</span>
      </div>
      <div className="flex items-center gap-1.5 text-[11px] text-text-muted">
        <Server className="h-3.5 w-3.5 text-accent-infra" />
        <span>trustledger.decision-gate.v1</span>
      </div>
    </div>
  );
};
