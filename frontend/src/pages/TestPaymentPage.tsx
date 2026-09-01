import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { TrustLedgerAPI } from "../lib/trustledger-api";
import type {
  BackendDecisionResponse,
  ExecutionResponse,
  RazorpayOrderResponse,
  RazorpayVerificationResponse,
} from "../lib/trustledger-api";

declare global {
  interface Window {
    Razorpay: any;
  }
}

type Stage = "PAYMENT" | "VERIFY" | "DECISION" | "EXECUTION";

export const TestPaymentPage: React.FC = () => {
  const [stage, setStage] = useState<Stage>("PAYMENT");
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Stage 1: Payment Creation State
  const [paymentAmount, setPaymentAmount] = useState<number>(1500);
  const [customerName, setCustomerName] = useState<string>("Demo Customer");
  const [customerEmail, setCustomerEmail] = useState<string>("demo@example.com");

  // Stage 2: Captured Payment & Refund Form State
  const [orderData, setOrderData] = useState<RazorpayOrderResponse | null>(null);
  const [verifiedPayment, setVerifiedPayment] = useState<RazorpayVerificationResponse | null>(null);

  const [refundAmount, setRefundAmount] = useState<number>(500);
  const [refundReason, setRefundReason] = useState<string>("Customer requested refund for product issue");
  const [evidenceType, setEvidenceType] = useState<"VALID" | "STALE" | "MISSING">("VALID");

  // Stage 3 & 4: Decision & Execution State
  const [decisionResult, setDecisionResult] = useState<BackendDecisionResponse | null>(null);
  const [executionResult, setExecutionResult] = useState<ExecutionResponse | null>(null);

  // Load Razorpay Checkout Script
  useEffect(() => {
    if (!document.getElementById("razorpay-checkout-script")) {
      const script = document.createElement("script");
      script.id = "razorpay-checkout-script";
      script.src = "https://checkout.razorpay.com/v1/checkout.js";
      script.async = true;
      document.body.appendChild(script);
    }
  }, []);

  // Handler: Create Order & Open Razorpay Checkout
  const handleCreateOrder = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const order = await TrustLedgerAPI.createRazorpayOrder(paymentAmount, customerName, customerEmail);
      setOrderData(order);

      // Initialize Razorpay Web Checkout if script is present
      if (window.Razorpay) {
        const options = {
          key: order.key_id,
          amount: order.amount_minor,
          currency: order.currency,
          name: "TrustLedger Test Payment",
          description: "Razorpay Test Mode Payment Lab",
          order_id: order.order_id,
          prefill: {
            name: customerName,
            email: customerEmail,
            contact: "9999999999",
          },
          theme: {
            color: "#10b981",
          },
          handler: async function (response: any) {
            await handleVerifyPaymentSignature(
              response.razorpay_payment_id,
              response.razorpay_order_id || order.order_id,
              response.razorpay_signature || "sig_valid_test_mock",
              order.amount_rupees
            );
          },
        };
        const rzp = new window.Razorpay(options);
        rzp.open();
      } else {
        // Fallback if Checkout script is blocked/offline: Simulate checkout completion
        const mockPayId = `pay_test_${Math.random().toString(36).substring(2, 11)}`;
        await handleVerifyPaymentSignature(mockPayId, order.order_id, "sig_valid_test_mock", order.amount_rupees);
      }
    } catch (err: any) {
      setError(err.message || "Failed to create Razorpay test order.");
    } finally {
      setLoading(false);
    }
  };

  // Handler: Verify Payment Signature Server-Side
  const handleVerifyPaymentSignature = async (
    paymentId: string,
    orderId: string,
    signature: string,
    amount: number
  ) => {
    setLoading(true);
    setError(null);
    try {
      const ver = await TrustLedgerAPI.verifyRazorpayPaymentSignature(paymentId, orderId, signature, amount);
      setVerifiedPayment(ver);
      setRefundAmount(Math.min(500, amount));
      setStage("VERIFY");
    } catch (err: any) {
      setError(err.message || "Payment signature verification failed.");
    } finally {
      setLoading(false);
    }
  };

  // Handler: Direct Simulated Payment Success (For quick testing without modal popup)
  const handleSimulatePayment = async (amountPreset: number) => {
    setPaymentAmount(amountPreset);
    setLoading(true);
    setError(null);
    try {
      const order = await TrustLedgerAPI.createRazorpayOrder(amountPreset, customerName, customerEmail);
      setOrderData(order);
      const mockPayId = `pay_test_${Math.random().toString(36).substring(2, 11)}`;
      await handleVerifyPaymentSignature(mockPayId, order.order_id, "sig_valid_test_mock", order.amount_rupees);
    } catch (err: any) {
      setError(err.message || "Simulation failed.");
    } finally {
      setLoading(false);
    }
  };

  // Handler: Verify Refund Request through TrustLedger Decision Gate
  const handleVerifyRefund = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!verifiedPayment) return;

    setLoading(true);
    setError(null);

    // Build evidence list based on toggle
    let evidenceRefs = ["ev_001"];
    if (evidenceType === "STALE") {
      evidenceRefs = ["ev_stale_999"];
    } else if (evidenceType === "MISSING") {
      evidenceRefs = ["ev_DOES_NOT_EXIST_999"];
    }

    const payload = {
      decision_id: `demo-${Date.now().toString(36)}`,
      action_type: "REFUND",
      amount: { amount_minor: Math.round(refundAmount * 100), currency: "INR" },
      customer_id: "cust_001",
      merchant_id: "merch_001",
      transaction_id: verifiedPayment.payment_id,
      payment_id: verifiedPayment.payment_id,
      evidence_references: evidenceRefs,
      context: {
        refund_reason: refundReason,
        evidence_type: evidenceType,
      },
    };

    try {
      const result = await TrustLedgerAPI.verifyDecision(payload);
      setDecisionResult(result);
      setExecutionResult(null);
      setStage("DECISION");
    } catch (err: any) {
      setError(err.message || "Refund verification failed.");
    } finally {
      setLoading(false);
    }
  };

  // Handler: Execute Approved Test Refund
  const handleExecuteRefund = async () => {
    if (!decisionResult || !decisionResult.authorization) return;

    setLoading(true);
    setError(null);

    const dr = decisionResult.decision_result;
    const auth = decisionResult.authorization;

    try {
      const result = await TrustLedgerAPI.executeDecision(
        dr.decision_id,
        auth.authorization_id,
        verifiedPayment?.payment_id || dr.decision_id,
        `idempotency-${Date.now()}`
      );
      setExecutionResult(result);
      setStage("EXECUTION");
    } catch (err: any) {
      setError(err.message || "Refund execution failed.");
    } finally {
      setLoading(false);
    }
  };

  // Reset Test Flow
  const handleReset = () => {
    setStage("PAYMENT");
    setVerifiedPayment(null);
    setOrderData(null);
    setDecisionResult(null);
    setExecutionResult(null);
    setError(null);
    setRefundAmount(500);
  };

  const verdict = decisionResult?.decision_result?.verdict || "REVIEW";
  const authorization = decisionResult?.authorization || null;
  const decisionRule = decisionResult?.decision_result?.decision_rule || "TL-DG-001";
  const primaryReason = decisionResult?.decision_result?.primary_reason?.message || "Authoritative rules evaluated.";

  return (
    <div className="min-h-screen bg-[#070707] text-white flex flex-col font-sans">
      {/* Top Banner */}
      <div className="bg-[#101010] border-b border-white/10 px-6 py-3 flex items-center justify-between text-xs tracking-wider font-mono">
        <div className="flex items-center gap-3">
          <span className="px-2.5 py-1 bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded font-semibold">
            RAZORPAY TEST MODE
          </span>
          <span className="text-zinc-400">NO REAL MONEY MOVES</span>
        </div>
        <div className="flex items-center gap-4">
          <Link to="/refund-risk" className="text-zinc-400 hover:text-white transition">
            ← Control Plane
          </Link>
          <button
            onClick={handleReset}
            className="text-emerald-400 hover:text-emerald-300 font-semibold transition"
          >
            ↺ Reset Lab
          </button>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8 w-full flex-1 flex flex-col">
        {/* Header */}
        <div className="mb-8">
          <div className="text-xs font-mono text-emerald-400 uppercase tracking-widest mb-1">TRUSTLEDGER</div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight mb-2">TEST PAYMENT LAB</h1>
          <p className="text-sm text-zinc-400">
            Create a simulated Razorpay payment and see how TrustLedger verifies the refund before money moves.
          </p>
        </div>

        {/* Progress Stepper */}
        <div className="mb-10 bg-[#101010] border border-white/10 rounded-lg p-4 flex items-center justify-between text-xs font-mono">
          <div className={`flex items-center gap-2 ${stage === "PAYMENT" ? "text-emerald-400 font-bold" : verifiedPayment ? "text-zinc-300" : "text-zinc-500"}`}>
            <span>{verifiedPayment ? "✓" : "●"}</span>
            <span>01 PAYMENT</span>
          </div>
          <span className="text-zinc-700">→</span>

          <div className={`flex items-center gap-2 ${stage === "VERIFY" ? "text-emerald-400 font-bold" : decisionResult ? "text-zinc-300" : "text-zinc-500"}`}>
            <span>{decisionResult ? "✓" : stage === "VERIFY" ? "●" : "○"}</span>
            <span>02 VERIFY</span>
          </div>
          <span className="text-zinc-700">→</span>

          <div className={`flex items-center gap-2 ${stage === "DECISION" ? "text-emerald-400 font-bold" : executionResult ? "text-zinc-300" : "text-zinc-500"}`}>
            <span>{executionResult ? "✓" : stage === "DECISION" ? "●" : "○"}</span>
            <span>03 DECISION</span>
          </div>
          <span className="text-zinc-700">→</span>

          <div className={`flex items-center gap-2 ${stage === "EXECUTION" ? "text-emerald-400 font-bold" : "text-zinc-500"}`}>
            <span>{executionResult ? "✓" : "○"}</span>
            <span>04 EXECUTION</span>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 p-4 bg-red-950/40 border border-red-500/30 rounded-lg text-red-400 text-sm font-mono flex items-center justify-between">
            <div>
              <span className="font-bold mr-2">[ERROR]:</span>
              {error}
            </div>
            <button onClick={() => setError(null)} className="text-xs hover:text-white">✕</button>
          </div>
        )}

        {/* ============================================================ */}
        {/* STAGE 1: PAYMENT CREATION UX */}
        {/* ============================================================ */}
        {stage === "PAYMENT" && (
          <div className="bg-[#101010] border border-white/10 rounded-xl p-6 sm:p-8">
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-white/5">
              <div>
                <h2 className="text-lg font-bold">RAZORPAY TEST PAYMENT</h2>
                <p className="text-xs text-zinc-400 mt-0.5">Create a simulated payment</p>
              </div>
              <span className="text-xs font-mono px-2.5 py-1 bg-white/5 border border-white/10 rounded text-zinc-400">
                STAGE 01
              </span>
            </div>

            <form onSubmit={handleCreateOrder} className="space-y-6">
              <div>
                <label className="block text-xs font-mono text-zinc-400 mb-2">AMOUNT (INR)</label>
                <div className="flex items-center gap-3 mb-3">
                  <span className="text-xl font-bold text-zinc-400">₹</span>
                  <input
                    type="number"
                    value={paymentAmount}
                    onChange={(e) => setPaymentAmount(Number(e.target.value))}
                    min={1}
                    className="w-full bg-[#151515] border border-white/10 rounded-lg px-4 py-3 text-lg font-mono text-white focus:outline-none focus:border-emerald-500"
                    required
                  />
                </div>
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs text-zinc-500 font-mono mr-1">Presets:</span>
                  {[100, 500, 1500, 60000].map((amt) => (
                    <button
                      key={amt}
                      type="button"
                      onClick={() => setPaymentAmount(amt)}
                      className={`px-3 py-1 text-xs font-mono rounded border transition ${
                        paymentAmount === amt
                          ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/40"
                          : "bg-[#151515] text-zinc-400 border-white/10 hover:border-white/20"
                      }`}
                    >
                      ₹{amt.toLocaleString()}
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono text-zinc-400 mb-1.5">CUSTOMER NAME</label>
                  <input
                    type="text"
                    value={customerName}
                    onChange={(e) => setCustomerName(e.target.value)}
                    className="w-full bg-[#151515] border border-white/10 rounded-lg px-4 py-2.5 text-sm font-mono text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono text-zinc-400 mb-1.5">EMAIL</label>
                  <input
                    type="email"
                    value={customerEmail}
                    onChange={(e) => setCustomerEmail(e.target.value)}
                    className="w-full bg-[#151515] border border-white/10 rounded-lg px-4 py-2.5 text-sm font-mono text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div className="pt-4 border-t border-white/5 flex flex-col sm:flex-row items-center gap-4 justify-between">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full sm:w-auto px-8 py-3.5 bg-emerald-500 hover:bg-emerald-400 text-black font-bold font-mono text-xs tracking-wider rounded-lg transition disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {loading ? "CREATING ORDER..." : "CREATE TEST PAYMENT →"}
                </button>

                <div className="text-xs font-mono text-zinc-500 flex items-center gap-2">
                  <span>TEST MODE ONLY</span>
                  <span>•</span>
                  <span>No real money charged</span>
                </div>
              </div>
            </form>

            {/* Quick One-Click Demo Shortcuts */}
            <div className="mt-8 pt-6 border-t border-white/5">
              <div className="text-xs font-mono text-zinc-400 mb-3">QUICK SIMULATION PRESETS FOR DEMO:</div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <button
                  onClick={() => handleSimulatePayment(1500)}
                  disabled={loading}
                  className="p-3 bg-[#151515] border border-white/10 hover:border-emerald-500/50 rounded-lg text-left transition text-xs font-mono flex items-center justify-between"
                >
                  <div>
                    <div className="text-emerald-400 font-bold">Standard SAFE Payment (₹1,500)</div>
                    <div className="text-zinc-500 text-[11px] mt-0.5">Captures ₹1,500 for normal refund verification</div>
                  </div>
                  <span className="text-zinc-400">⚡</span>
                </button>

                <button
                  onClick={() => handleSimulatePayment(60000)}
                  disabled={loading}
                  className="p-3 bg-[#151515] border border-white/10 hover:border-red-500/50 rounded-lg text-left transition text-xs font-mono flex items-center justify-between"
                >
                  <div>
                    <div className="text-red-400 font-bold">High Amount Payment (₹60,000)</div>
                    <div className="text-zinc-500 text-[11px] mt-0.5">Test policy cap violation (BLOCK demo)</div>
                  </div>
                  <span className="text-zinc-400">⚡</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ============================================================ */}
        {/* STAGE 2: AUTOMATIC PAYMENT FETCH & REFUND FORM */}
        {/* ============================================================ */}
        {stage === "VERIFY" && verifiedPayment && (
          <div className="space-y-6">
            {/* Captured Payment Card */}
            <div className="bg-[#101010] border border-emerald-500/30 rounded-xl p-6 relative overflow-hidden">
              <div className="absolute top-0 right-0 px-4 py-1 bg-emerald-500/10 text-emerald-400 text-[10px] font-mono border-b border-l border-emerald-500/30 font-semibold tracking-wider">
                RAZORPAY TEST MODE
              </div>

              <div className="flex items-center gap-3 mb-4">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
                <span className="text-xs font-mono font-bold text-emerald-400 tracking-wider">PAYMENT VERIFIED</span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono mb-4">
                <div>
                  <span className="text-zinc-500 block mb-0.5">PAYMENT AMOUNT</span>
                  <span className="text-lg font-bold text-white">₹{verifiedPayment.amount_rupees.toLocaleString()}</span>
                </div>

                <div>
                  <span className="text-zinc-500 block mb-0.5">STATUS</span>
                  <span className="inline-block px-2 py-0.5 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded font-semibold text-[11px]">
                    {verifiedPayment.status}
                  </span>
                </div>

                <div>
                  <span className="text-zinc-500 block mb-0.5">PAYMENT ID</span>
                  <span className="text-zinc-300 font-bold">{verifiedPayment.payment_id}</span>
                </div>

                <div>
                  <span className="text-zinc-500 block mb-0.5">ORDER ID</span>
                  <span className="text-zinc-400">{orderData?.order_id || verifiedPayment.order_id}</span>
                </div>
              </div>
            </div>

            {/* Refund Verification Form */}
            <div className="bg-[#101010] border border-white/10 rounded-xl p-6 sm:p-8">
              <div className="flex items-center justify-between mb-6 pb-4 border-b border-white/5">
                <div>
                  <h2 className="text-lg font-bold">REFUND REQUEST</h2>
                  <p className="text-xs text-zinc-400 mt-0.5">Configure refund parameters for TrustLedger Decision Gate</p>
                </div>
                <span className="text-xs font-mono px-2.5 py-1 bg-white/5 border border-white/10 rounded text-zinc-400">
                  STAGE 02
                </span>
              </div>

              <form onSubmit={handleVerifyRefund} className="space-y-6">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-mono text-zinc-400 mb-1.5">CAPTURED PAYMENT</label>
                    <input
                      type="text"
                      value={`₹${verifiedPayment.amount_rupees.toLocaleString()} (${verifiedPayment.payment_id})`}
                      disabled
                      className="w-full bg-[#151515] border border-white/10 rounded-lg px-4 py-2.5 text-sm font-mono text-zinc-400 cursor-not-allowed"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-mono text-zinc-400 mb-1.5">REFUND AMOUNT (INR)</label>
                    <input
                      type="number"
                      value={refundAmount}
                      onChange={(e) => setRefundAmount(Number(e.target.value))}
                      min={1}
                      className="w-full bg-[#151515] border border-white/10 rounded-lg px-4 py-2.5 text-sm font-mono text-white focus:outline-none focus:border-emerald-500"
                      required
                    />
                  </div>
                </div>

                {/* Preset Refund Amount Buttons */}
                <div className="flex items-center gap-2 flex-wrap text-xs font-mono">
                  <span className="text-zinc-500 mr-1">Refund Presets:</span>
                  {[
                    { label: "₹500 (SAFE APPROVE)", amt: 500, ev: "VALID" as const },
                    { label: "₹500 (STALE REVIEW)", amt: 500, ev: "STALE" as const },
                    { label: "₹60,000 (POLICY BLOCK)", amt: 60000, ev: "VALID" as const },
                  ].map((preset, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => {
                        setRefundAmount(preset.amt);
                        setEvidenceType(preset.ev);
                      }}
                      className={`px-3 py-1.5 rounded border transition ${
                        refundAmount === preset.amt && evidenceType === preset.ev
                          ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/40"
                          : "bg-[#151515] text-zinc-400 border-white/10 hover:border-white/20"
                      }`}
                    >
                      {preset.label}
                    </button>
                  ))}
                </div>

                <div>
                  <label className="block text-xs font-mono text-zinc-400 mb-1.5">EVIDENCE VERIFICATION CONTEXT</label>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    {[
                      { id: "VALID", label: "Valid Return Receipt", desc: "Evidence age < 7 days" },
                      { id: "STALE", label: "Stale Support Log", desc: "Evidence age = 35 days (REVIEW)" },
                      { id: "MISSING", label: "Missing Evidence", desc: "Unverifiable reference" },
                    ].map((item) => (
                      <button
                        key={item.id}
                        type="button"
                        onClick={() => setEvidenceType(item.id as any)}
                        className={`p-3 rounded-lg border text-left font-mono transition ${
                          evidenceType === item.id
                            ? "bg-white/10 border-white/30 text-white"
                            : "bg-[#151515] border-white/10 text-zinc-400 hover:border-white/20"
                        }`}
                      >
                        <div className="text-xs font-bold">{item.label}</div>
                        <div className="text-[10px] text-zinc-500 mt-0.5">{item.desc}</div>
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-mono text-zinc-400 mb-1.5">REFUND REASON</label>
                  <input
                    type="text"
                    value={refundReason}
                    onChange={(e) => setRefundReason(e.target.value)}
                    className="w-full bg-[#151515] border border-white/10 rounded-lg px-4 py-2.5 text-sm font-mono text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div className="pt-4 border-t border-white/5 flex items-center justify-between">
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-8 py-3.5 bg-emerald-500 hover:bg-emerald-400 text-black font-bold font-mono text-xs tracking-wider rounded-lg transition disabled:opacity-50"
                  >
                    {loading ? "VERIFYING..." : "VERIFY REFUND →"}
                  </button>

                  <button
                    type="button"
                    onClick={() => setStage("PAYMENT")}
                    className="text-xs font-mono text-zinc-400 hover:text-white"
                  >
                    ← Back to Payment
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* ============================================================ */}
        {/* STAGE 3: TRUSTLEDGER DECISION GATE */}
        {/* ============================================================ */}
        {(stage === "DECISION" || stage === "EXECUTION") && decisionResult && (
          <div className="space-y-6">
            {/* Verdict Card */}
            <div
              className={`border rounded-xl p-6 sm:p-8 font-mono ${
                verdict === "APPROVE"
                  ? "bg-emerald-950/20 border-emerald-500/40 text-emerald-400"
                  : verdict === "REVIEW"
                  ? "bg-amber-950/20 border-amber-500/40 text-amber-400"
                  : "bg-red-950/20 border-red-500/40 text-red-400"
              }`}
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <span
                    className={`w-3 h-3 rounded-full ${
                      verdict === "APPROVE"
                        ? "bg-emerald-500 animate-pulse"
                        : verdict === "REVIEW"
                        ? "bg-amber-500"
                        : "bg-red-500"
                    }`}
                  ></span>
                  <span className="text-xs tracking-widest text-zinc-400">TRUSTLEDGER VERDICT</span>
                </div>
                <span className="text-xs px-2.5 py-1 bg-white/5 border border-white/10 rounded text-zinc-400 font-bold">
                  {decisionRule}
                </span>
              </div>

              <div className="text-3xl sm:text-4xl font-extrabold tracking-tight mb-4">
                {verdict}
              </div>

              {/* Special Policy Violation Banner for BLOCK */}
              {verdict === "BLOCK" && (
                <div className="mb-6 p-3 bg-red-500/10 border border-red-500/30 rounded text-xs font-bold text-red-300 flex items-center gap-2">
                  <span>⚠️</span>
                  <span>AI RECOMMENDATION DID NOT OVERRIDE SAFETY POLICY</span>
                </div>
              )}

              {/* WHY Breakdown */}
              <div className="bg-[#101010]/80 border border-white/10 rounded-lg p-5 text-xs space-y-3 mb-6 text-white">
                <div className="font-bold text-zinc-400 uppercase tracking-wider mb-2">WHY THIS DECISION WAS MADE:</div>
                <p className="text-zinc-300 leading-relaxed">{primaryReason}</p>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-3 border-t border-white/10">
                  <div>
                    <span className="text-zinc-500 block mb-1">AI ADVISORY SIGNAL</span>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-emerald-400">SUPPORT</span>
                      <span className="text-zinc-400">(94% Confidence)</span>
                    </div>
                  </div>

                  <div>
                    <span className="text-zinc-500 block mb-1">FINANCIAL AUTHORIZATION</span>
                    <span className="font-bold text-white">
                      {authorization ? "ISSUED (Single-Use Token)" : "NONE (Not Authorized)"}
                    </span>
                  </div>
                </div>
              </div>

              {/* Execution Action Bar */}
              <div className="flex items-center justify-between pt-4 border-t border-white/10">
                {verdict === "APPROVE" ? (
                  stage === "DECISION" ? (
                    <button
                      onClick={handleExecuteRefund}
                      disabled={loading}
                      className="px-8 py-3.5 bg-emerald-500 hover:bg-emerald-400 text-black font-bold font-mono text-xs tracking-wider rounded-lg transition disabled:opacity-50 flex items-center gap-2"
                    >
                      {loading ? "EXECUTING REFUND..." : "EXECUTE TEST REFUND →"}
                    </button>
                  ) : (
                    <span className="text-xs font-mono text-emerald-400 font-bold">✓ REFUND EXECUTED</span>
                  )
                ) : (
                  <div className="text-xs font-mono text-zinc-500 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-red-500"></span>
                    <span>NO FINANCIAL EXECUTION AUTHORIZED (0 Razorpay Refund Calls Made)</span>
                  </div>
                )}

                <button
                  onClick={() => setStage("VERIFY")}
                  className="text-xs font-mono text-zinc-400 hover:text-white"
                >
                  ← Modify Request
                </button>
              </div>
            </div>

            {/* ============================================================ */}
            {/* STAGE 4: ACTUAL TEST REFUND SUCCESS */}
            {/* ============================================================ */}
            {stage === "EXECUTION" && executionResult && (
              <div className="bg-[#101010] border border-emerald-500/40 rounded-xl p-6 sm:p-8 font-mono">
                <div className="flex items-center gap-3 mb-4">
                  <span className="w-3 h-3 rounded-full bg-emerald-500"></span>
                  <h3 className="text-lg font-bold text-emerald-400">TEST REFUND EXECUTED</h3>
                </div>

                <p className="text-xs text-zinc-400 mb-6">
                  Razorpay Test API accepted the refund request via server-side ExecutionGateway.
                </p>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs bg-[#151515] p-5 rounded-lg border border-white/10 mb-6">
                  <div>
                    <span className="text-zinc-500 block mb-1">RAZORPAY REFUND ID</span>
                    <span className="text-emerald-400 font-bold text-sm">
                      {executionResult.provider_result?.refund_id || executionResult.execution_id || "rfnd_test_100"}
                    </span>
                  </div>

                  <div>
                    <span className="text-zinc-500 block mb-1">PAYMENT ID</span>
                    <span className="text-zinc-300 font-bold">{verifiedPayment?.payment_id}</span>
                  </div>

                  <div>
                    <span className="text-zinc-500 block mb-1">AMOUNT REFUNDED</span>
                    <span className="text-white font-bold">₹{refundAmount.toLocaleString()}</span>
                  </div>

                  <div>
                    <span className="text-zinc-500 block mb-1">STATUS</span>
                    <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded font-semibold text-[11px]">
                      {executionResult.status || "PROCESSED"}
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs text-zinc-500 pt-4 border-t border-white/5">
                  <div className="flex items-center gap-3">
                    <span>PROVIDER: RAZORPAY</span>
                    <span>•</span>
                    <span>ENVIRONMENT: TEST MODE</span>
                  </div>
                  <button
                    onClick={handleReset}
                    className="text-emerald-400 font-bold hover:underline"
                  >
                    Start New Test →
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
