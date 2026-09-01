import React from "react";
import { Link } from "react-router-dom";
import { LiveVerificationRunner } from "../components/trustledger/LiveVerificationRunner";
import { RefundLossPreventionCard } from "../components/trustledger/RefundLossPreventionCard";
import { RefundEvaluationPanel } from "../components/trustledger/RefundEvaluationPanel";

export const RefundRiskPage: React.FC = () => {
  const refundTaxonomyItems = [
    { code: "POLICY_CAP_VIOLATION", name: "Merchant Policy Cap Breach", severity: "HARD", verdict: "BLOCK", desc: "Refund requested ₹60,000 > Merchant Limit ₹25,000" },
    { code: "DUPLICATE_REFUND", name: "Duplicate Refund Attempt", severity: "HARD", verdict: "BLOCK", desc: "Refund already processed for transaction" },
    { code: "REFUND_AMOUNT_MISMATCH", name: "Refund Amount Mismatch", severity: "HARD", verdict: "BLOCK", desc: "Requested refund exceeds original order amount" },
    { code: "ENTITY_MISMATCH", name: "Customer / Order Entity Mismatch", severity: "HARD", verdict: "BLOCK", desc: "Customer ID does not match transaction owner" },
    { code: "NONEXISTENT_TRANSACTION", name: "Nonexistent Transaction ID", severity: "HARD", verdict: "BLOCK", desc: "Transaction ID not found in authoritative repo" },
    { code: "MISSING_EVIDENCE", name: "Missing Evidence Attachment", severity: "WARNING", verdict: "REVIEW", desc: "Required courier or support ticket missing" },
    { code: "CONFLICTING_EVIDENCE", name: "Conflicting Evidence Signals", severity: "WARNING", verdict: "REVIEW", desc: "Courier API indicates delivered vs Support claim" },
    { code: "STALE_EVIDENCE", name: "Stale Evidence (>30 Days)", severity: "WARNING", verdict: "REVIEW", desc: "Evidence attachment date exceeds 30-day limit" },
    { code: "REFUND_VELOCITY_RISK", name: "High Refund Velocity", severity: "WARNING", verdict: "REVIEW", desc: "Customer exceeded 3 refunds in 7 days" },
  ];

  return (
    <div className="space-y-16 font-sans">
      {/* 1. Hero Introduction */}
      <section className="flex flex-col items-center text-center space-y-4 pt-4 sm:pt-6 max-w-3xl mx-auto">
        <span className="text-[11px] font-mono font-semibold text-[#68717D] uppercase tracking-[0.08em] block">
          AI FINANCIAL CONTROL
        </span>

        <h1 className="text-4xl sm:text-6xl md:text-7xl lg:text-[80px] font-extrabold text-[#F5F7FA] tracking-[-0.045em] leading-[0.95]">
          AI REFUND <br />
          RISK MANAGER
        </h1>

        <p className="text-sm sm:text-base text-[#A3ACB8] max-w-[600px] leading-relaxed">
          Verify every AI-proposed refund before it reaches financial execution.
        </p>

        <div className="flex items-center gap-3 text-xs font-mono text-[#68717D] pt-1">
          <span className="text-[#36D98A] font-semibold uppercase">AI CAN RECOMMEND.</span>
          <span>•</span>
          <span className="text-[#4F8CFF] font-semibold uppercase">TRUSTLEDGER DECIDES.</span>
        </div>
      </section>

      {/* 2. Test Payment Lab Banner */}
      <section className="max-w-[1200px] mx-auto">
        <div className="bg-gradient-to-r from-emerald-950/40 via-black to-blue-950/40 border border-emerald-500/30 rounded-xl p-6 flex flex-col sm:flex-row items-center justify-between gap-4 font-mono">
          <div>
            <div className="flex items-center gap-2 text-emerald-400 font-bold text-xs mb-1">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              BUILDATHON REAL E2E TEST LAB
            </div>
            <h2 className="text-lg font-bold text-white">Razorpay Test Mode Payment & Refund Gating</h2>
            <p className="text-xs text-zinc-400 mt-1">
              Create a simulated Razorpay payment and experience automatic payment capture & refund execution.
            </p>
          </div>
          <Link
            to="/test-payment"
            className="px-6 py-3 bg-emerald-500 hover:bg-emerald-400 text-black font-bold text-xs rounded-lg transition whitespace-nowrap"
          >
            TRY REAL TEST PAYMENT →
          </Link>
        </div>
      </section>

      {/* 3. Main Verification Workspace */}
      <section>
        <LiveVerificationRunner />
      </section>

      {/* 3. Refund Loss Prevention Card */}
      <section>
        <RefundLossPreventionCard />
      </section>

      {/* 4. Risk Taxonomy Matrix */}
      <section>
        <div className="fintech-surface p-7 space-y-6">
          <div className="flex items-center justify-between border-b border-white/[0.08] pb-4">
            <h3 className="text-sm font-bold text-[#F5F7FA] uppercase tracking-wider font-mono">
              AI REFUND RISK TAXONOMY & VERDICT MAPPING
            </h3>
            <span className="text-xs font-mono text-[#68717D]">9 Risk Taxonomy Rules</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 text-xs font-mono">
            {refundTaxonomyItems.map((item) => (
              <div key={item.code} className="p-4 bg-[#07090C] rounded-md border border-white/[0.08] space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-[#F5F7FA] text-xs">{item.name}</span>
                  <span
                    className={`px-2 py-0.5 text-[10px] font-bold rounded ${
                      item.verdict === "BLOCK"
                        ? "bg-[#FF5864]/15 text-[#FF5864]"
                        : "bg-[#E5B85C]/15 text-[#E5B85C]"
                    }`}
                  >
                    {item.verdict}
                  </span>
                </div>
                <p className="text-[11px] text-[#A3ACB8] leading-relaxed">{item.desc}</p>
                <div className="flex items-center justify-between pt-1 text-[10px] text-[#68717D]">
                  <code>{item.code}</code>
                  <span className="font-bold text-[#A3ACB8]">{item.severity}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 5. Refund Evaluation Panel */}
      <section>
        <RefundEvaluationPanel />
      </section>
    </div>
  );
};
