import React, { useState } from "react";
import {
  CheckCircle2,
  AlertOctagon,
  RotateCw,
  ArrowRight,
  ChevronDown,
  ChevronUp,
  Search,
  ShieldAlert,
  ShieldCheck,
  CreditCard,
  Lock,
} from "lucide-react";
import {
  TrustLedgerAPI,
  type BackendDecisionResponse,
  type RazorpayPaymentMetadata,
} from "../../lib/trustledger-api";

export const LiveVerificationRunner: React.FC = () => {
  // Form State Inputs
  const [amountRupees, setAmountRupees] = useState<number | string>(1500);
  const [customerId, setCustomerId] = useState<string>("cust_001");
  const [transactionId, setTransactionId] = useState<string>("txn_100");
  const [paymentId, setPaymentId] = useState<string>("pay_100");
  const [reason, setReason] = useState<string>("Customer requested refund for verified item issue.");
  const [evidenceText, setEvidenceText] = useState<string>("Fresh courier delivery return artifact (ev_001).");
  const [evidenceRef, setEvidenceRef] = useState<string>("ev_001");
  const [idempotencyKey] = useState<string>(`idem_req_${Math.floor(1000 + Math.random() * 9000)}`);
  const [activePreset, setActivePreset] = useState<"SAFE" | "REVIEW" | "BLOCK" | "CUSTOM">("SAFE");

  // Razorpay Payment Discovery State
  const [fetchingPayment, setFetchingPayment] = useState<boolean>(false);
  const [fetchPaymentError, setFetchPaymentError] = useState<string | null>(null);
  const [paymentMetadata, setPaymentMetadata] = useState<RazorpayPaymentMetadata | null>(null);

  // Execution & Backend Response State
  const [loading, setLoading] = useState<boolean>(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);
  const [executingRefund, setExecutingRefund] = useState<boolean>(false);
  const [execResult, setExecResult] = useState<any | null>(null);
  const [lastResult, setLastResult] = useState<{
    res: BackendDecisionResponse;
    reqPayload: any;
  } | null>(null);

  // Decision Trace Collapse State
  const [expandedTraceIdx, setExpandedTraceIdx] = useState<number | null>(null);

  // Preset Scenario Handlers
  const handleApplyPreset = (preset: "SAFE" | "REVIEW" | "BLOCK") => {
    setActivePreset(preset);
    setValidationError(null);
    setApiError(null);
    setExecResult(null);
    setFetchPaymentError(null);

    if (preset === "SAFE") {
      setAmountRupees(1500);
      setCustomerId("cust_001");
      setTransactionId("txn_100");
      setPaymentId("pay_100");
      setReason("Customer requested refund for verified item issue.");
      setEvidenceText("Fresh courier delivery return artifact (ev_001).");
      setEvidenceRef("ev_001");
    } else if (preset === "REVIEW") {
      setAmountRupees(500);
      setCustomerId("cust_001");
      setTransactionId("txn_100");
      setPaymentId("pay_100");
      setReason("Stale support ticket refund request.");
      setEvidenceText("Support ticket attachment date exceeds 30-day freshness limit (ev_stale_999).");
      setEvidenceRef("ev_stale_999");
    } else if (preset === "BLOCK") {
      setAmountRupees(60000);
      setCustomerId("cust_001");
      setTransactionId("txn_100");
      setPaymentId("pay_100");
      setReason("Customer requested refund exceeding policy cap.");
      setEvidenceText("Courier API confirms delivery return. Support evidence reports customer dispute.");
      setEvidenceRef("ev_001");
    }
  };

  // Razorpay Test Payment Discovery Handler
  const handleFetchPayment = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!paymentId.trim()) {
      setFetchPaymentError("PAYMENT ID REQUIRED: Enter a Razorpay Test Mode Payment ID (e.g. pay_100).");
      return;
    }

    setFetchingPayment(true);
    setFetchPaymentError(null);

    try {
      const metadata = await TrustLedgerAPI.fetchRazorpayPayment(paymentId.trim());
      setPaymentMetadata(metadata);
      setTransactionId(metadata.payment_id);
      if (metadata.amount_rupees > 0 && activePreset !== "BLOCK") {
        setAmountRupees(metadata.amount_rupees);
      }
    } catch (err: any) {
      console.error("Razorpay Fetch Payment Error:", err);
      setFetchPaymentError(err.message || "Payment ID not found on Razorpay Test API or local benchmark repository.");
    } finally {
      setFetchingPayment(false);
    }
  };

  // Real Backend Verification Handler
  const handleVerifyRefund = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();

    setValidationError(null);
    setApiError(null);
    setExecResult(null);

    const numericAmount = Number(amountRupees);
    if (isNaN(numericAmount) || numericAmount <= 0) {
      setValidationError("INVALID AMOUNT: Refund amount must be a positive number greater than ₹0.");
      return;
    }

    if (!customerId.trim() || !transactionId.trim() || !paymentId.trim()) {
      setValidationError("MISSING REQUIRED FIELDS: Customer ID, Transaction ID, and Payment ID are required.");
      return;
    }

    setLoading(true);

    const amountMinor = Math.round(numericAmount * 100);
    const reqPayload = {
      contract_version: "trustledger.contract.v1",
      decision_id: `dec_custom_${Date.now()}_${Math.floor(1000 + Math.random() * 9000)}`,
      action_type: "REFUND",
      agent_id: "agent_custom_verifier_01",
      merchant_id: "merch_001",
      customer_id: customerId.trim(),
      transaction_id: transactionId.trim(),
      payment_id: paymentId.trim(),
      order_id: "ord_100",
      amount: { amount_minor: amountMinor, currency: "INR" },
      reason: { category: "CUSTOMER_REQUEST", explanation: reason.trim() },
      evidence_references: [evidenceRef || "ev_001"],
      evidence_context: evidenceText.trim(),
      idempotency_key: idempotencyKey.trim() || `idem_${Date.now()}`,
      requested_at: new Date().toISOString(),
    };

    try {
      const response = await TrustLedgerAPI.verifyDecision(reqPayload);
      setLastResult({ res: response, reqPayload });
    } catch (err: any) {
      console.error("Custom Refund Verification API Error:", err);
      setApiError(err.message || "TrustLedger REST API backend unreachable (http://localhost:8000).");
    } finally {
      setLoading(false);
    }
  };

  // Execution Handler for Authorized APPROVE Decisions ONLY
  const handleExecuteRefund = async () => {
    if (!lastResult || !lastResult.res.authorization) return;

    setExecutingRefund(true);
    try {
      const baseUrl = TrustLedgerAPI.getApiBaseUrl();
      const res = await fetch(
        `${baseUrl}/api/v1/decisions/${lastResult.res.decision_result.decision_id}/execute`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            authorization_id: lastResult.res.authorization.authorization_id,
            payment_id: paymentId.trim() || "pay_100",
            idempotency_key: idempotencyKey.trim(),
          }),
        }
      );

      const json = await res.json();
      setExecResult(json);
    } catch (err: any) {
      setExecResult({ status: "FAILED", detail: err.message || "Execution call failed." });
    } finally {
      setExecutingRefund(false);
    }
  };

  const dr = lastResult?.res.decision_result;
  const auth = lastResult?.res.authorization;
  const isPolicyOverride =
    dr?.verdict === "BLOCK" && (dr?.primary_reason?.code === "REFUND_LIMIT_EXCEEDED" || dr?.decision_rule === "TL-DG-002");

  const requestedAmountMinor = lastResult ? lastResult.reqPayload.amount.amount_minor : Number(amountRupees || 0) * 100;
  const requestedAmountRupees = Math.round(requestedAmountMinor / 100);
  const policyCapRupees = 25000;
  const excessRupees = requestedAmountRupees > policyCapRupees ? requestedAmountRupees - policyCapRupees : 0;

  return (
    <div className="w-full space-y-8 max-w-[1280px] mx-auto">
      {/* TEST MODE BANNER */}
      <div className="p-3 bg-[#4F8CFF]/10 border border-[#4F8CFF]/30 rounded-md flex flex-col sm:flex-row items-center justify-between gap-2 text-xs font-mono">
        <div className="flex items-center gap-2 text-[#4F8CFF]">
          <Lock className="h-4 w-4 shrink-0" />
          <span className="font-extrabold uppercase tracking-wider">RAZORPAY TEST MODE</span>
          <span className="text-[#68717D]">|</span>
          <span className="text-[#A3ACB8]">SANDBOX FINANCIAL SAFETY ENGINE</span>
        </div>
        <span className="px-2.5 py-0.5 bg-[#4F8CFF]/20 text-[#4F8CFF] font-bold rounded text-[10px] uppercase tracking-wider">
          NO REAL MONEY MOVES
        </span>
      </div>

      {/* UNIFIED CONTROL WORKSPACE CONTAINER */}
      <div className="fintech-surface overflow-hidden shadow-2xl">
        <div className="grid grid-cols-1 lg:grid-cols-12 divide-y lg:divide-y-0 lg:divide-x divide-white/[0.08]">
          {/* LEFT COLUMN (58%): 01 / REQUEST & PAYMENT DISCOVERY */}
          <div className="lg:col-span-7 p-6 sm:p-9 space-y-6">
            <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
              <span className="text-[11px] font-mono font-semibold text-[#68717D] uppercase tracking-[0.08em]">
                01 / PAYMENT & REFUND REQUEST
              </span>

              {/* Compact Quick Scenario Pills */}
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-mono text-[#68717D] mr-1 hidden sm:inline">PRESETS:</span>
                <button
                  type="button"
                  onClick={() => handleApplyPreset("SAFE")}
                  className={`px-2.5 py-1 rounded-full text-xs font-mono transition-all cursor-pointer ${
                    activePreset === "SAFE"
                      ? "bg-[#36D98A]/15 border border-[#36D98A]/40 text-[#36D98A] font-semibold"
                      : "bg-[#07090C] border border-white/[0.08] text-[#A3ACB8] hover:text-[#F5F7FA]"
                  }`}
                >
                  Safe
                </button>
                <button
                  type="button"
                  onClick={() => handleApplyPreset("REVIEW")}
                  className={`px-2.5 py-1 rounded-full text-xs font-mono transition-all cursor-pointer ${
                    activePreset === "REVIEW"
                      ? "bg-[#E5B85C]/15 border border-[#E5B85C]/40 text-[#E5B85C] font-semibold"
                      : "bg-[#07090C] border border-white/[0.08] text-[#A3ACB8] hover:text-[#F5F7FA]"
                  }`}
                >
                  Stale evidence
                </button>
                <button
                  type="button"
                  onClick={() => handleApplyPreset("BLOCK")}
                  className={`px-2.5 py-1 rounded-full text-xs font-mono transition-all cursor-pointer ${
                    activePreset === "BLOCK"
                      ? "bg-[#FF5864]/15 border border-[#FF5864]/40 text-[#FF5864] font-semibold"
                      : "bg-[#07090C] border border-white/[0.08] text-[#A3ACB8] hover:text-[#F5F7FA]"
                  }`}
                >
                  Policy violation
                </button>
              </div>
            </div>

            {/* SECTION 1: RAZORPAY TEST PAYMENT DISCOVERY PANEL */}
            <div className="p-4 bg-[#07090C] border border-white/[0.08] rounded-md space-y-3 font-mono text-xs">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-[#68717D] uppercase font-bold tracking-wider flex items-center gap-1.5">
                  <CreditCard className="h-3.5 w-3.5 text-[#4F8CFF]" />
                  RAZORPAY TEST PAYMENT INSPECTION
                </span>
                {paymentMetadata && (
                  <span className="px-2 py-0.5 bg-[#4F8CFF]/15 text-[#4F8CFF] font-bold text-[10px] rounded border border-[#4F8CFF]/30">
                    {paymentMetadata.source}
                  </span>
                )}
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={paymentId}
                  onChange={(e) => {
                    setPaymentId(e.target.value);
                    setTransactionId(e.target.value);
                  }}
                  placeholder="pay_L123456789"
                  className="flex-1 field-input px-3 py-2 text-xs font-mono"
                />
                <button
                  type="button"
                  onClick={handleFetchPayment}
                  disabled={fetchingPayment}
                  className="px-4 py-2 bg-[#4F8CFF]/20 border border-[#4F8CFF]/40 text-[#4F8CFF] font-bold rounded-md hover:bg-[#4F8CFF]/30 transition-all flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                >
                  {fetchingPayment ? (
                    <RotateCw className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Search className="h-3.5 w-3.5" />
                  )}
                  <span>FETCH PAYMENT</span>
                </button>
              </div>

              {fetchPaymentError && (
                <div className="p-2.5 bg-[#FF5864]/10 border border-[#FF5864]/30 rounded text-[11px] text-[#FF5864]">
                  {fetchPaymentError}
                </div>
              )}

              {paymentMetadata && (
                <div className="p-3 bg-[#090C10] border border-white/[0.08] rounded-md grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 text-[11px]">
                  <div>
                    <span className="text-[10px] text-[#68717D] uppercase block">CAPTURED AMOUNT</span>
                    <span className="text-[#36D98A] font-bold text-sm">₹{paymentMetadata.amount_rupees.toLocaleString()}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-[#68717D] uppercase block">PAYMENT STATUS</span>
                    <span className={`font-bold text-xs ${paymentMetadata.captured ? "text-[#36D98A]" : "text-[#E5B85C]"}`}>
                      {paymentMetadata.status}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-[#68717D] uppercase block">METHOD</span>
                    <span className="text-[#F5F7FA] font-bold text-xs">{paymentMetadata.method}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-[#68717D] uppercase block">CURRENCY</span>
                    <span className="text-[#F5F7FA] font-bold text-xs">{paymentMetadata.currency}</span>
                  </div>
                </div>
              )}
            </div>

            {/* SECTION 2: REFUND FORM */}
            <form onSubmit={handleVerifyRefund} className="space-y-6 pt-1">
              {/* Visually Dominant Amount Field */}
              <div className="space-y-1.5">
                <span className="text-[11px] font-mono font-semibold text-[#68717D] uppercase tracking-wider block">
                  REQUESTED REFUND AMOUNT
                </span>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-mono text-[#A3ACB8]">₹</span>
                  <input
                    type="number"
                    min="1"
                    step="1"
                    value={amountRupees}
                    onChange={(e) => {
                      setAmountRupees(e.target.value);
                      setActivePreset("CUSTOM");
                    }}
                    className="w-full bg-transparent border-b-2 border-white/[0.13] focus:border-[#4F8CFF] focus:outline-none text-4xl sm:text-5xl font-mono font-extrabold text-[#F5F7FA] py-1 transition-all"
                    placeholder="1500"
                  />
                </div>
                <span className="text-[11px] font-mono text-[#68717D] block pt-1">
                  = {Math.round(Number(amountRupees || 0) * 100).toLocaleString()} paise
                </span>
              </div>

              {/* Two-Column Metadata */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
                <div className="space-y-1">
                  <span className="text-[#68717D] text-[11px] uppercase block">CUSTOMER ID</span>
                  <input
                    type="text"
                    value={customerId}
                    onChange={(e) => {
                      setCustomerId(e.target.value);
                      setActivePreset("CUSTOM");
                    }}
                    className="w-full field-input px-3 py-2 text-xs"
                    placeholder="cust_100"
                  />
                </div>

                <div className="space-y-1">
                  <span className="text-[#68717D] text-[11px] uppercase block">TRANSACTION ID</span>
                  <input
                    type="text"
                    value={transactionId}
                    onChange={(e) => {
                      setTransactionId(e.target.value);
                      setActivePreset("CUSTOM");
                    }}
                    className="w-full field-input px-3 py-2 text-xs"
                    placeholder="txn_100"
                  />
                </div>
              </div>

              {/* Reason & Evidence Fields */}
              <div className="space-y-3">
                <div className="space-y-1">
                  <span className="text-[11px] font-mono font-semibold text-[#68717D] uppercase block">
                    REFUND REASON
                  </span>
                  <input
                    type="text"
                    value={reason}
                    onChange={(e) => {
                      setReason(e.target.value);
                      setActivePreset("CUSTOM");
                    }}
                    className="w-full field-input px-3 py-2 text-xs font-sans"
                    placeholder="Customer returned item..."
                  />
                </div>

                <div className="space-y-1">
                  <span className="text-[11px] font-mono font-semibold text-[#68717D] uppercase block">
                    EVIDENCE CONTEXT
                  </span>
                  <textarea
                    rows={2}
                    value={evidenceText}
                    onChange={(e) => {
                      setEvidenceText(e.target.value);
                      setActivePreset("CUSTOM");
                    }}
                    className="w-full bg-[#07090C] border border-white/[0.08] rounded-md p-2.5 text-[#F5F7FA] text-xs font-sans focus:border-[#4F8CFF] focus:outline-none transition-all"
                    placeholder="Courier API artifact details..."
                  />
                </div>
              </div>

              {/* Validation Alert */}
              {validationError && (
                <div className="p-3 bg-[#FF5864]/10 border border-[#FF5864]/30 rounded-md text-xs font-mono text-[#FF5864] font-semibold flex items-center gap-2">
                  <AlertOctagon className="h-4 w-4 shrink-0" />
                  <span>{validationError}</span>
                </div>
              )}

              {/* Primary CTA */}
              <button
                type="submit"
                disabled={loading}
                className="brand-cta w-full flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 py-3.5"
              >
                {loading ? (
                  <>
                    <RotateCw className="h-4 w-4 animate-spin text-white" />
                    <span>RUNNING TRUSTLEDGER VERIFICATION...</span>
                  </>
                ) : (
                  <>
                    <span>VERIFY REFUND</span>
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>
            </form>
          </div>

          {/* RIGHT COLUMN (42%): 02 / DECISION & EXPLANATION */}
          <div className="lg:col-span-5 p-6 sm:p-9 space-y-6 bg-[#090C10]">
            <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
              <span className="text-[11px] font-mono font-semibold text-[#68717D] uppercase tracking-[0.08em]">
                02 / DECISION & SAFETY GATE
              </span>
              <span className="text-xs font-mono text-[#68717D]">
                {dr ? `RULE ${dr.decision_rule}` : "WAITING FOR INPUT"}
              </span>
            </div>

            {/* Waiting Initial State */}
            {!lastResult && !loading && !apiError && (
              <div className="space-y-4 py-8 text-center sm:text-left font-mono">
                <span className="text-xs font-mono text-[#68717D] uppercase block">AUTHORITATIVE VERDICT</span>
                <h3 className="text-3xl font-extrabold font-mono text-[#A3ACB8]">WAITING FOR VERIFICATION</h3>
                <p className="text-xs text-[#A3ACB8] leading-relaxed font-sans">
                  Fetch a payment or click <strong>VERIFY REFUND</strong> to execute TrustLedger deterministic safety gate and AI context checks.
                </p>
              </div>
            )}

            {/* Loading State */}
            {loading && (
              <div className="space-y-4 py-8 font-mono text-xs text-[#4F8CFF] animate-pulse">
                <div className="flex items-center gap-3">
                  <RotateCw className="h-5 w-5 animate-spin text-[#4F8CFF]" />
                  <span className="font-bold text-base text-[#F5F7FA] uppercase tracking-wider">
                    EVALUATING RISK PIPELINE
                  </span>
                </div>
                <p className="text-[#A3ACB8]">Evaluating merchant policy limits, evidence freshness, entity consistency, and AI signal...</p>
              </div>
            )}

            {/* API Error State */}
            {apiError && (
              <div className="p-5 bg-[#FF5864]/10 border border-[#FF5864]/30 rounded-md space-y-2 text-xs font-mono">
                <div className="flex items-center gap-2 text-[#FF5864] font-bold">
                  <AlertOctagon className="h-4 w-4" />
                  <span>BACKEND OFFLINE</span>
                </div>
                <p className="text-[#F5F7FA]">Unable to reach backend at port 8000. Ensure server is running.</p>
                <span className="text-[11px] text-[#68717D] block pt-1">
                  No financial execution authorized.
                </span>
              </div>
            )}

            {/* Evaluated Verdict Display */}
            {lastResult && !loading && (
              <div className="space-y-5 font-mono">
                {/* Verdict + Status */}
                <div className="space-y-1">
                  <span className="text-[11px] text-[#68717D] uppercase block">TRUSTLEDGER VERDICT</span>
                  <span
                    className={`text-5xl sm:text-6xl font-extrabold tracking-tight block ${
                      dr?.verdict === "APPROVE"
                        ? "text-[#36D98A]"
                        : dr?.verdict === "REVIEW"
                        ? "text-[#E5B85C]"
                        : "text-[#FF5864]"
                    }`}
                  >
                    {dr?.verdict}
                  </span>
                  <span className="text-xs font-bold uppercase tracking-wider text-[#A3ACB8] block pt-1">
                    {dr?.verdict === "APPROVE"
                      ? "EXECUTION AUTHORIZED"
                      : dr?.verdict === "REVIEW"
                      ? "HUMAN REVIEW REQUIRED"
                      : "EXECUTION BLOCKED"}
                  </span>
                </div>

                {/* PRIMARY REASON PANEL */}
                <div className={`p-3.5 rounded-md border text-xs ${
                  dr?.verdict === "APPROVE"
                    ? "bg-[#36D98A]/10 border-[#36D98A]/30"
                    : dr?.verdict === "REVIEW"
                    ? "bg-[#E5B85C]/10 border-[#E5B85C]/30"
                    : "bg-[#FF5864]/10 border-[#FF5864]/30"
                }`}>
                  <span className="text-[10px] text-[#68717D] uppercase block mb-1">
                    {dr?.verdict === "APPROVE" ? "WHY APPROVED" : dr?.verdict === "REVIEW" ? "WHY REVIEW" : "WHY BLOCKED"}
                  </span>
                  <span className={`font-semibold leading-relaxed block ${
                    dr?.verdict === "APPROVE" ? "text-[#36D98A]" : dr?.verdict === "REVIEW" ? "text-[#E5B85C]" : "text-[#FF5864]"
                  }`}>
                    [{dr?.primary_reason?.code}]
                  </span>
                  <span className="text-[#F5F7FA] leading-relaxed block mt-0.5">
                    {dr?.primary_reason?.message}
                  </span>
                </div>

                {/* AI SIGNAL + EVIDENCE STATE */}
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="p-2.5 bg-[#07090C] border border-white/[0.08] rounded-md space-y-0.5">
                    <span className="text-[10px] text-[#68717D] uppercase block">AI CONTEXT SIGNAL</span>
                    <span className={`font-bold text-sm block ${
                      dr?.ai_recommendation === "SUPPORT" ? "text-[#36D98A]"
                      : dr?.ai_recommendation === "CONTRADICT" ? "text-[#FF5864]"
                      : "text-[#E5B85C]"
                    }`}>
                      {dr?.ai_recommendation || "—"}
                    </span>
                    <span className="text-[10px] text-[#68717D]">Rule: {dr?.decision_rule}</span>
                  </div>

                  <div className="p-2.5 bg-[#07090C] border border-white/[0.08] rounded-md space-y-0.5">
                    <span className="text-[10px] text-[#68717D] uppercase block">EVIDENCE STATE</span>
                    <span className={`font-bold text-sm block ${
                      dr?.evidence_state === "SUFFICIENT" ? "text-[#36D98A]"
                      : dr?.evidence_state === "CONFLICTING" ? "text-[#FF5864]"
                      : "text-[#E5B85C]"
                    }`}>
                      {dr?.evidence_state || "—"}
                    </span>
                    <span className="text-[10px] text-[#68717D]">
                      Risk: {dr?.risk_level} ({((dr?.risk_score ?? 0) * 100).toFixed(0)}%)
                    </span>
                  </div>
                </div>

                {/* OVERRIDE BANNER IF AI WAS SUPPORT BUT DETERMINISTIC ENGINE BLOCKED */}
                {isPolicyOverride && (
                  <div className="p-3 bg-[#FF5864]/10 border border-[#FF5864]/30 rounded-md text-xs font-bold text-[#FF5864] flex items-center gap-2">
                    <ShieldAlert className="h-4 w-4 shrink-0" />
                    <span>AI RECOMMENDATION DID NOT OVERRIDE SAFETY POLICY</span>
                  </div>
                )}

                {/* REVIEW CONTEXT — missing items */}
                {dr?.verdict === "REVIEW" && (
                  <div className="p-3 bg-[#E5B85C]/10 border border-[#E5B85C]/30 rounded-md text-xs space-y-1">
                    <div className="flex items-center gap-1.5 text-[#E5B85C] font-bold">
                      <ShieldCheck className="h-4 w-4" />
                      <span>NO FINANCIAL EXECUTION AUTHORIZED</span>
                    </div>
                    <p className="text-[#F5F7FA] text-[11px]">
                      Razorpay API calls: <strong>0</strong>. Human review is required before refund can proceed.
                    </p>
                  </div>
                )}

                {/* BLOCK CONTEXT */}
                {dr?.verdict === "BLOCK" && (
                  <div className="p-3 bg-[#FF5864]/10 border border-[#FF5864]/30 rounded-md text-xs space-y-1">
                    <div className="flex items-center gap-1.5 text-[#FF5864] font-bold">
                      <ShieldAlert className="h-4 w-4" />
                      <span>NO FINANCIAL EXECUTION AUTHORIZED</span>
                    </div>
                    <p className="text-[#F5F7FA] text-[11px]">
                      Razorpay API calls: <strong>0</strong>. Execution blocked by TrustLedger Decision Gate.
                    </p>
                  </div>
                )}

                {/* Financial Comparison */}
                <div className="p-3 bg-[#07090C] border border-white/[0.08] rounded-md grid grid-cols-3 gap-2 text-xs">
                  <div>
                    <span className="text-[10px] text-[#68717D] uppercase block">REQUESTED</span>
                    <span className="text-[#F5F7FA] font-bold text-sm">₹{requestedAmountRupees.toLocaleString()}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-[#68717D] uppercase block">POLICY LIMIT</span>
                    <span className="text-[#FF5864] font-bold text-sm">₹{policyCapRupees.toLocaleString()}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-[#68717D] uppercase block">EXCESS</span>
                    <span className="text-[#FF5864] font-bold text-sm">
                      {excessRupees > 0 ? `+₹${excessRupees.toLocaleString()}` : "₹0"}
                    </span>
                  </div>
                </div>

                {/* APPROVE Execution CTA */}
                {auth && dr?.verdict === "APPROVE" && (
                  <div className="space-y-2 pt-2">
                    <span className="text-[11px] text-[#36D98A] block">
                      Server Auth Token: <code>{auth.authorization_id.substring(0, 16)}...</code>
                    </span>
                    <button
                      type="button"
                      onClick={handleExecuteRefund}
                      disabled={executingRefund || (execResult && (execResult.status === "EXECUTED" || execResult.status === "SUCCESS"))}
                      className="w-full py-3.5 bg-[#36D98A] text-[#07090C] font-extrabold text-xs uppercase tracking-wider rounded-md hover:bg-[#36D98A]/90 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                    >
                      {executingRefund ? (
                        <>
                          <RotateCw className="h-4 w-4 animate-spin text-[#07090C]" />
                          <span>CALLING RAZORPAY TEST API...</span>
                        </>
                      ) : (execResult?.status === "EXECUTED" || execResult?.status === "SUCCESS") ? (
                        <>
                          <CheckCircle2 className="h-4 w-4 text-[#07090C]" />
                          <span>REFUND EXECUTED</span>
                        </>
                      ) : (
                        <>
                          <ArrowRight className="h-4 w-4 text-[#07090C]" />
                          <span>EXECUTE TEST REFUND</span>
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* RAZORPAY REFUND EXECUTION RESULT DISPLAY */}
      {execResult && (
        <div className="fintech-surface p-6 sm:p-7 space-y-4 font-mono text-xs">
          <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
            <span className="font-bold text-[#36D98A] uppercase tracking-wider flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4" />
              RAZORPAY TEST-MODE REFUND RESULT
            </span>
            <span className="px-2 py-0.5 bg-[#36D98A]/15 text-[#36D98A] font-bold text-[10px] rounded">
              ENVIRONMENT: {execResult.provider_environment || "TEST MODE"}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
            <div className="p-3 bg-[#07090C] border border-white/[0.08] rounded space-y-1">
              <span className="text-[10px] text-[#68717D] uppercase block">RAZORPAY REFUND ID</span>
              <code className="text-[#36D98A] font-bold block text-sm">
                {execResult.refund_id || execResult.external_reference || "rfnd_test_001"}
              </code>
            </div>

            <div className="p-3 bg-[#07090C] border border-white/[0.08] rounded space-y-1">
              <span className="text-[10px] text-[#68717D] uppercase block">PAYMENT ID</span>
              <code className="text-[#F5F7FA] font-bold block text-sm">{execResult.payment_id || paymentId}</code>
            </div>

            <div className="p-3 bg-[#07090C] border border-white/[0.08] rounded space-y-1">
              <span className="text-[10px] text-[#68717D] uppercase block">REFUNDED AMOUNT</span>
              <span className="text-[#F5F7FA] font-bold block text-sm">
                ₹{((execResult.amount?.amount_minor || 0) / 100).toLocaleString()} {execResult.amount?.currency || "INR"}
              </span>
            </div>

            <div className="p-3 bg-[#07090C] border border-white/[0.08] rounded space-y-1">
              <span className="text-[10px] text-[#68717D] uppercase block">PROVIDER / STATUS</span>
              <span className="text-[#36D98A] font-bold block text-sm">
                {execResult.provider || "RAZORPAY"} ({execResult.status})
              </span>
            </div>
          </div>

          <div className="text-[11px] text-[#A3ACB8] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 pt-1 border-t border-white/[0.06]">
            <span>Execution ID: <code>{execResult.execution_id}</code></span>
            <span>Auth ID: <code>{execResult.authorization_id}</code></span>
          </div>
        </div>
      )}

      {/* SIGNATURE TRUSTLEDGER VISUAL: HORIZONTAL DECISION FLOW */}
      {lastResult && !loading && (
        <div className="fintech-surface p-6 sm:p-7 space-y-6 font-mono">
          <span className="text-[11px] font-semibold text-[#68717D] uppercase tracking-[0.08em] block">
            DECISION FLOW RELATIONSHIP
          </span>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 items-center text-xs text-center">
            {/* 1. AI Context */}
            <div className="p-4 bg-[#07090C] border border-white/[0.08] rounded-md space-y-1">
              <span className="text-[10px] text-[#68717D] uppercase block">AI CONTEXT SIGNAL</span>
              <span className={`text-sm font-bold block ${
                dr?.ai_recommendation === "SUPPORT" ? "text-[#36D98A]"
                : dr?.ai_recommendation === "CONTRADICT" ? "text-[#FF5864]"
                : "text-[#E5B85C]"
              }`}>
                {dr?.ai_recommendation || "UNCERTAIN"}
              </span>
              <span className="text-[11px] text-[#A3ACB8]">{((dr?.risk_score ?? 0) * 100).toFixed(0)}% RISK SCORE</span>
            </div>

            <div className="hidden md:flex justify-center text-[#4F8CFF] font-bold text-lg">→</div>

            {/* 2. TrustLedger Safety Gate */}
            <div className="p-4 bg-[#07090C] border border-white/[0.08] rounded-md space-y-1">
              <span className="text-[10px] text-[#68717D] uppercase block">SAFETY GATE</span>
              <span className={`text-sm font-bold block ${
                dr?.verdict === "APPROVE" ? "text-[#36D98A]"
                : dr?.verdict === "REVIEW" ? "text-[#E5B85C]"
                : "text-[#FF5864]"
              }`}>
                {dr?.primary_reason?.code || "EVALUATING"}
              </span>
              <span className="text-[11px] text-[#A3ACB8]">RULE {dr?.decision_rule}</span>
            </div>

            <div className="hidden md:flex justify-center text-[#FF5864] font-bold text-lg">→</div>

            {/* 3. Authoritative Verdict */}
            <div className={`p-4 rounded-md border space-y-1 ${
              dr?.verdict === "APPROVE" ? "bg-[#36D98A]/10 border-[#36D98A]/30"
              : dr?.verdict === "REVIEW" ? "bg-[#E5B85C]/10 border-[#E5B85C]/30"
              : "bg-[#FF5864]/10 border-[#FF5864]/30"
            }`}>
              <span className="text-[10px] text-[#FF5864] font-bold uppercase block">AUTHORITATIVE VERDICT</span>
              <span className="text-base font-extrabold text-[#FF5864] block">{dr?.verdict || "BLOCK"}</span>
              <span className="text-[11px] text-[#F5F7FA]">AUTHORITY: TRUSTLEDGER</span>
            </div>
          </div>
        </div>
      )}

      {/* HORIZONTAL DESKTOP DECISION TRACE TIMELINE */}
      {dr?.decision_trace && dr.decision_trace.length > 0 && (
        <div className="fintech-surface p-6 sm:p-7 space-y-4 font-mono text-xs">
          <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
            <span className="font-semibold text-[#68717D] uppercase tracking-wider">
              DECISION TRACE TIMELINE
            </span>
            <span className="text-[11px] text-[#68717D]">Click stage to expand information</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
            {dr.decision_trace.map((trace: any, idx: number) => {
              const isExpanded = expandedTraceIdx === idx;
              const isBlockStage = trace.status === "FAIL" || trace.status === "BLOCK";
              return (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setExpandedTraceIdx(isExpanded ? null : idx)}
                  className={`p-3 rounded-md border text-left flex flex-col justify-between transition-all cursor-pointer ${
                    isBlockStage
                      ? "bg-[#FF5864]/15 border-[#FF5864]/40 text-[#FF5864]"
                      : trace.status === "PASS" || trace.status === "APPROVE"
                      ? "bg-[#36D98A]/10 border-[#36D98A]/30 text-[#36D98A]"
                      : "bg-[#07090C] border-white/[0.08] text-[#A3ACB8]"
                  }`}
                >
                  <div>
                    <span className="text-[10px] text-[#68717D] font-bold block">0{idx + 1}</span>
                    <span className="font-bold text-[11px] block">{trace.stage_name}</span>
                  </div>
                  <div className="flex items-center justify-between pt-2">
                    <span className="text-[10px] font-bold uppercase">{trace.status}</span>
                    {isExpanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                  </div>
                </button>
              );
            })}
          </div>

          {expandedTraceIdx !== null && dr.decision_trace[expandedTraceIdx] && (
            <div className="p-4 bg-[#07090C] border border-white/[0.08] rounded-md text-xs space-y-1.5 font-mono">
              <div className="flex items-center justify-between font-bold text-[#F5F7FA]">
                <span>STAGE 0{expandedTraceIdx + 1}: {dr.decision_trace[expandedTraceIdx].stage_name}</span>
                <span className="text-[#4F8CFF]">{dr.decision_trace[expandedTraceIdx].status}</span>
              </div>
              <p className="text-[#A3ACB8]"><strong className="text-[#68717D]">Input:</strong> {dr.decision_trace[expandedTraceIdx].input_summary}</p>
              <p className="text-[#A3ACB8]"><strong className="text-[#68717D]">Output:</strong> {dr.decision_trace[expandedTraceIdx].output_summary}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
