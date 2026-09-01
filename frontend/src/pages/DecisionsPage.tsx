import React from "react";
import { useNavigate } from "react-router-dom";
import { Filter, ArrowUpRight } from "lucide-react";
import { StatusBadge } from "../components/trustledger/StatusBadge";
import { RiskMeter } from "../components/trustledger/RiskMeter";
import { AISignalBadge } from "../components/trustledger/AISignalBadge";
import { MoneyDisplay } from "../components/trustledger/MoneyDisplay";
import { DataSourceBadge } from "../components/trustledger/DataSourceBadge";
import { MOCK_DECISIONS } from "../data/mock";

export const DecisionsPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="space-y-4">
      {/* Decisions Queue Header & Filter Controls Placeholder */}
      <div className="bg-background-surface/80 border border-border-subtle rounded-card p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-xs font-mono font-bold text-text-primary uppercase tracking-wider">
          <Filter className="h-4 w-4 text-accent-infra" />
          <span>FINANCIAL DECISION EVALUATION QUEUE</span>
        </div>
        <div className="flex items-center gap-3">
          <DataSourceBadge type="HELD_OUT_BENCHMARK" />
          <span className="text-xs font-mono text-text-muted px-2.5 py-1 bg-background-hover rounded border border-border-subtle text-text-primary">
            1,500 Benchmark Cases Loaded
          </span>
        </div>
      </div>

      {/* Decisions Table with Navigation */}
      <div className="bg-background-surface/80 border border-border-subtle rounded-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs font-mono">
            <thead>
              <tr className="bg-background-secondary/80 border-b border-border-subtle text-text-muted uppercase font-semibold">
                <th className="py-3 px-4">Source</th>
                <th className="py-3 px-4">Verdict</th>
                <th className="py-3 px-4">Decision ID & Action</th>
                <th className="py-3 px-4">Merchant / Customer</th>
                <th className="py-3 px-4">AI Signal</th>
                <th className="py-3 px-4">Risk Level</th>
                <th className="py-3 px-4 text-right">Amount</th>
                <th className="py-3 px-4 text-center">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle/50 text-text-primary">
              {MOCK_DECISIONS.map((item) => (
                <tr
                  key={item.decision_id}
                  onClick={() => navigate(`/decisions/${item.decision_id}`)}
                  className="hover:bg-background-hover/60 cursor-pointer transition-colors group"
                >
                  <td className="py-3.5 px-4">
                    <DataSourceBadge type="HELD_OUT_BENCHMARK" labelOverride="BENCHMARK" />
                  </td>
                  <td className="py-3.5 px-4">
                    <StatusBadge verdict={item.verdict} size="sm" />
                  </td>
                  <td className="py-3.5 px-4 font-medium">
                    <div className="flex flex-col">
                      <span className="text-text-primary font-bold group-hover:text-accent-infra transition-colors">{item.action_type}</span>
                      <span className="text-[11px] text-text-muted">{item.decision_id} ({item.decision_rule})</span>
                    </div>
                  </td>
                  <td className="py-3.5 px-4 text-text-secondary">
                    <div className="flex flex-col">
                      <span>{item.merchant_id}</span>
                      <span className="text-[11px] text-text-muted">{item.customer_id || "N/A"}</span>
                    </div>
                  </td>
                  <td className="py-3.5 px-4">
                    <AISignalBadge recommendation={item.ai_recommendation} />
                  </td>
                  <td className="py-3.5 px-4">
                    <RiskMeter level={item.risk_level} score={item.risk_score} />
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <MoneyDisplay amountMinor={item.amount_minor} size="sm" />
                  </td>
                  <td className="py-3.5 px-4 text-center text-text-muted group-hover:text-text-primary">
                    <ArrowUpRight className="h-4 w-4 inline-block" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
