import React, { useState } from "react";
import { Hash, Copy, Check } from "lucide-react";

interface AuditHashMetadataProps {
  decisionId: string;
  decisionHash: string;
  gateVersion?: string;
}

export const AuditHashMetadata: React.FC<AuditHashMetadataProps> = ({
  decisionId,
  decisionHash,
  gateVersion = "trustledger.decision-gate.v1",
}) => {
  const [copied, setCopied] = useState(false);

  const truncatedHash = `${decisionHash.substring(0, 10)}...${decisionHash.substring(decisionHash.length - 8)}`;

  const copyToClipboard = () => {
    navigator.clipboard.writeText(decisionHash);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-wrap items-center gap-3 text-xs font-mono text-text-secondary bg-background-surface/60 border border-border-subtle rounded-lg px-3 py-1.5">
      <div className="flex items-center gap-1 text-text-muted">
        <Hash className="h-3.5 w-3.5 text-accent-infra" />
        <span>ID:</span>
        <span className="text-text-primary font-medium">{decisionId}</span>
      </div>

      <div className="h-3 w-px bg-border-subtle hidden sm:block" />

      <div className="flex items-center gap-1.5 group relative cursor-pointer" onClick={copyToClipboard} title="Click to copy full SHA-256 hash">
        <span className="text-text-muted">SHA-256:</span>
        <span className="text-accent-infra hover:underline font-mono">{truncatedHash}</span>
        <button className="text-text-muted hover:text-text-primary transition-colors">
          {copied ? <Check className="h-3.5 w-3.5 text-verdict-approve" /> : <Copy className="h-3.5 w-3.5" />}
        </button>
        {copied && (
          <span className="absolute -top-7 left-1/2 -translate-x-1/2 bg-background-hover text-verdict-approve text-[10px] px-2 py-0.5 rounded shadow border border-border-subtle">
            Copied!
          </span>
        )}
      </div>

      <div className="h-3 w-px bg-border-subtle hidden sm:block" />

      <div className="text-[11px] text-text-muted">
        <span>Gate: </span>
        <span className="text-text-secondary">{gateVersion}</span>
      </div>
    </div>
  );
};
