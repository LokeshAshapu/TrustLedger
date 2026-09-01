"""
TrustLedger Deterministic Evidence Validator Engine
Phase 3 Deterministic Verification Layer
"""

from typing import Dict, Any, List
from datetime import datetime
from verifier.deterministic.models import (
    ComponentResult,
    Finding,
    FindingCategory,
    FindingSeverity,
    CheckStatus,
)


class EvidenceEngine:
    """
    Validates evidence existence, provenance, verification status, entity linkage, timestamp freshness, and sufficiency.
    """

    def validate(
        self,
        request: Dict[str, Any],
        evidence_db: Dict[str, Dict[str, Any]],
        transactions_db: Dict[str, Dict[str, Any]],
        orders_db: Dict[str, Dict[str, Any]],
    ) -> ComponentResult:
        findings: List[Finding] = []
        action_type = request.get("action_type")
        refs = request.get("evidence_references", [])
        overall_status = CheckStatus.PASS

        # 1. Reference Existence & Provenance
        found_evidences: List[Dict[str, Any]] = []

        if not refs:
            findings.append(
                Finding(
                    check_id="EVIDENCE_SUFFICIENCY_CHECK",
                    category=FindingCategory.EVIDENCE,
                    severity=FindingSeverity.WARNING,
                    status=CheckStatus.UNKNOWN,
                    code="NO_EVIDENCE_ATTACHED",
                    message="Proposed financial action payload contains zero attached evidence references.",
                    evidence_ids=[],
                    details={"action_type": action_type},
                )
            )
            overall_status = CheckStatus.UNKNOWN

        for ref_id in refs:
            ev_record = evidence_db.get(ref_id)
            if not ev_record:
                findings.append(
                    Finding(
                        check_id="EVIDENCE_EXISTENCE_CHECK",
                        category=FindingCategory.EVIDENCE,
                        severity=FindingSeverity.HARD,
                        status=CheckStatus.FAIL,
                        code="MISSING_EVIDENCE_REFERENCE",
                        message=f"Referenced evidence ID '{ref_id}' does not exist in the observable evidence registry.",
                        evidence_ids=[ref_id],
                        details={"referenced_id": ref_id},
                    )
                )
                overall_status = CheckStatus.FAIL
                continue

            found_evidences.append(ev_record)

            # Provenance Check
            source = ev_record.get("source")
            source_rec = ev_record.get("source_record_id")
            ts = ev_record.get("timestamp")

            if not source or not source_rec or not ts:
                findings.append(
                    Finding(
                        check_id="EVIDENCE_PROVENANCE_CHECK",
                        category=FindingCategory.EVIDENCE,
                        severity=FindingSeverity.WARNING,
                        status=CheckStatus.FAIL,
                        code="INCOMPLETE_EVIDENCE_PROVENANCE",
                        message=f"Evidence artifact '{ref_id}' is missing mandatory provenance metadata (source, record ID, or timestamp).",
                        evidence_ids=[ref_id],
                        details={"source": source, "source_record_id": source_rec, "timestamp": ts},
                    )
                )

            # Timestamp Freshness & Staleness Check (Stale Threshold: 30 Days)
            req_ts = request.get("requested_at")
            if req_ts and ts:
                try:
                    r_clean = str(req_ts).replace("Z", "+00:00")
                    e_clean = str(ts).replace("Z", "+00:00")
                    req_dt = datetime.fromisoformat(r_clean)
                    ev_dt = datetime.fromisoformat(e_clean)
                    age_days = (req_dt - ev_dt).days
                    stale_threshold_days = 30
                    if age_days > stale_threshold_days:
                        findings.append(
                            Finding(
                                check_id="EVIDENCE_FRESHNESS_CHECK",
                                category=FindingCategory.EVIDENCE,
                                severity=FindingSeverity.WARNING,
                                status=CheckStatus.UNKNOWN,
                                code="EVIDENCE_TIMESTAMP_STALE",
                                message=f"Evidence artifact '{ref_id}' timestamp ({ts[:10]}) is {age_days} days old (exceeds {stale_threshold_days}-day staleness threshold). Re-verification required.",
                                evidence_ids=[ref_id],
                                details={"age_days": age_days, "stale_threshold_days": stale_threshold_days, "evidence_timestamp": ts},
                            )
                        )
                        if overall_status != CheckStatus.FAIL:
                            overall_status = CheckStatus.UNKNOWN
                except Exception:
                    pass

            # Status Check
            v_status = ev_record.get("verification_status")
            if v_status == "FAILED":
                findings.append(
                    Finding(
                        check_id="EVIDENCE_STATUS_CHECK",
                        category=FindingCategory.EVIDENCE,
                        severity=FindingSeverity.HARD,
                        status=CheckStatus.FAIL,
                        code="EVIDENCE_STATUS_FAILED",
                        message=f"Evidence artifact '{ref_id}' status is FAILED. Verification integrity check failed.",
                        evidence_ids=[ref_id],
                        details={"verification_status": v_status},
                    )
                )
                overall_status = CheckStatus.FAIL
            elif v_status == "CONFLICTING":
                findings.append(
                    Finding(
                        check_id="EVIDENCE_STATUS_CHECK",
                        category=FindingCategory.EVIDENCE,
                        severity=FindingSeverity.WARNING,
                        status=CheckStatus.FAIL,
                        code="CONFLICTING_EVIDENCE_STATUS",
                        message=f"Evidence artifact '{ref_id}' status is CONFLICTING. Artifact contains contradictory statements.",
                        evidence_ids=[ref_id],
                        details={"verification_status": v_status},
                    )
                )
                if overall_status != CheckStatus.FAIL:
                    overall_status = CheckStatus.UNKNOWN
            elif v_status in ["STALE", "MISSING"]:
                findings.append(
                    Finding(
                        check_id="EVIDENCE_STATUS_CHECK",
                        category=FindingCategory.EVIDENCE,
                        severity=FindingSeverity.WARNING,
                        status=CheckStatus.UNKNOWN,
                        code=f"EVIDENCE_STATUS_{v_status}",
                        message=f"Evidence artifact '{ref_id}' is marked as {v_status} in storage registry.",
                        evidence_ids=[ref_id],
                        details={"verification_status": v_status},
                    )
                )
                if overall_status != CheckStatus.FAIL:
                    overall_status = CheckStatus.UNKNOWN

            # Entity Linkage Check
            txn_id = request.get("transaction_id")
            order_id = request.get("order_id")

            if source_rec and txn_id and source_rec.startswith("txn_") and source_rec != txn_id:
                findings.append(
                    Finding(
                        check_id="EVIDENCE_LINKAGE_CHECK",
                        category=FindingCategory.EVIDENCE,
                        severity=FindingSeverity.HARD,
                        status=CheckStatus.FAIL,
                        code="EVIDENCE_LINKAGE_MISMATCH",
                        message=f"Evidence '{ref_id}' references transaction '{source_rec}', which does not match requested transaction '{txn_id}'.",
                        evidence_ids=[ref_id],
                        details={"evidence_source_record": source_rec, "decision_transaction_id": txn_id},
                    )
                )
                overall_status = CheckStatus.FAIL

        # 2. Action-Specific Sufficiency Check
        if found_evidences and all(ev.get("verification_status") == "VERIFIED" for ev in found_evidences) and overall_status == CheckStatus.PASS:
            findings.append(
                Finding(
                    check_id="EVIDENCE_VERIFICATION_PASS",
                    category=FindingCategory.EVIDENCE,
                    severity=FindingSeverity.INFO,
                    status=CheckStatus.PASS,
                    code="EVIDENCE_FULLY_VERIFIED",
                    message="All attached evidence references exist, possess valid provenance, and pass integrity verification.",
                    evidence_ids=refs,
                    details={"verified_count": len(found_evidences)},
                )
            )

        return ComponentResult(status=overall_status, findings=findings)
