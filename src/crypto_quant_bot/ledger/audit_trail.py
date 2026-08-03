from __future__ import annotations

import json
from dataclasses import replace
from hashlib import sha256
from typing import Any

from crypto_quant_bot.ledger.models import (
    DEFAULT_LEDGER_BLOCK_REASONS,
    DecisionLedgerCheck,
    DecisionLedgerEntry,
    DecisionLedgerPolicy,
    DecisionLedgerResult,
)


def _normalize_checksum_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    normalized.pop("entry_checksum", None)
    normalized.pop("created_at", None)
    return normalized


def build_entry_checksum(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        _normalize_checksum_payload(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


class DecisionLedgerAuditTrail:
    def __init__(
        self,
        policy_version: str = "lot15_decision_ledger_v0",
        ledger_version: str = "lot15_decision_ledger_v0",
    ) -> None:
        self.policy_version = policy_version
        self.ledger_version = ledger_version

    def default_policy(self, *, timeframe: str = "multi", timestamp: str = "") -> DecisionLedgerPolicy:
        return DecisionLedgerPolicy(
            timeframe=timeframe,
            timestamp=timestamp,
            policy_version=self.policy_version,
            ledger_version=self.ledger_version,
        )

    def build_checks(self, *, decision_firewall_state: str) -> list[DecisionLedgerCheck]:
        return [
            DecisionLedgerCheck(
                check_name="audit_only_record",
                expected_value=False,
                observed_value=False,
                block_reason="DECISION_RECORDED_FOR_AUDIT_ONLY",
                message="Ledger record remains audit-only.",
            ),
            DecisionLedgerCheck(
                check_name="final_decision",
                expected_value="WAIT",
                observed_value="WAIT",
                block_reason="FINAL_DECISION_WAIT",
                message="Final decision remains WAIT.",
            ),
            DecisionLedgerCheck(
                check_name="system_decision",
                expected_value="BLOCK_TRADING",
                observed_value="BLOCK_TRADING",
                block_reason="SYSTEM_DECISION_BLOCK_TRADING",
                message="System decision remains BLOCK_TRADING.",
            ),
            DecisionLedgerCheck(
                check_name="execution_allowed",
                expected_value=False,
                observed_value=False,
                block_reason="EXECUTION_NOT_ALLOWED",
                message="Execution remains disabled.",
            ),
            DecisionLedgerCheck(
                check_name="decision_firewall_state",
                expected_value="ACTIVE",
                observed_value=decision_firewall_state,
                block_reason="DECISION_RECORDED_FOR_AUDIT_ONLY",
                message="Decision Firewall remains active.",
            ),
            DecisionLedgerCheck(
                check_name="routing_allowed",
                expected_value=False,
                observed_value=False,
                block_reason="ORDER_ROUTING_NOT_ALLOWED",
                message="Routing remains disabled.",
            ),
            DecisionLedgerCheck(
                check_name="external_connectivity_allowed",
                expected_value=False,
                observed_value=False,
                block_reason="EXTERNAL_CONNECTIVITY_DISABLED",
                message="External connectivity remains disabled.",
            ),
            DecisionLedgerCheck(
                check_name="risk_allowed",
                expected_value=False,
                observed_value=False,
                block_reason="RISK_ENGINE_BLOCKS_BY_DEFAULT",
                message="Risk Engine remains blocking by default.",
            ),
            DecisionLedgerCheck(
                check_name="exposure_allowed",
                expected_value=False,
                observed_value=False,
                block_reason="EXPOSURE_GUARD_BLOCKS_BY_DEFAULT",
                message="Exposure Guard remains blocking by default.",
            ),
            DecisionLedgerCheck(
                check_name="portfolio_state",
                expected_value="FROZEN",
                observed_value="FROZEN",
                block_reason="PORTFOLIO_FROZEN",
                message="Portfolio remains frozen.",
            ),
            DecisionLedgerCheck(
                check_name="operating_mode",
                expected_value="educational_only",
                observed_value="educational_only",
                block_reason="EDUCATIONAL_MODE_ONLY",
                message="Project remains educational only.",
            ),
            DecisionLedgerCheck(
                check_name="human_review_required",
                expected_value=True,
                observed_value=True,
                block_reason="HUMAN_REVIEW_REQUIRED",
                message="Human review remains required.",
            ),
        ]

    def entry_from_source(
        self,
        *,
        timeframe: str,
        ledger_sequence: int,
        source_row: dict[str, Any],
        previous_entry_checksum: str,
        source_artifacts: list[str],
        source_checksums: dict[str, str],
    ) -> DecisionLedgerEntry:
        timestamp = str(source_row.get("timestamp", ""))
        policy = self.default_policy(timeframe=timeframe, timestamp=timestamp)
        entry = DecisionLedgerEntry(
            timeframe=timeframe,
            timestamp=timestamp,
            policy_version=policy.policy_version,
            ledger_version=policy.ledger_version,
            ledger_entry_id=f"decision_ledger_lot15_{timeframe}_{ledger_sequence:03d}",
            ledger_sequence=ledger_sequence,
            source_decision_id=str(source_row.get("id", "")),
            source_timeframe=str(source_row.get("timeframe", timeframe)),
            source_timestamp=str(source_row.get("timestamp", "")),
            trading_decision=str(source_row.get("trading_decision", policy.trading_decision)),
            system_decision=str(source_row.get("system_decision", policy.system_decision)),
            final_decision=str(source_row.get("final_decision", policy.final_decision)),
            final_system_decision=str(source_row.get("final_system_decision", policy.final_system_decision)),
            decision_firewall_state=str(source_row.get("decision_firewall_state", policy.decision_firewall_state)),
            execution_allowed=bool(source_row.get("execution_allowed", policy.execution_allowed)),
            trade_allowed=bool(source_row.get("trade_allowed", policy.trade_allowed)),
            used_for_decision=bool(source_row.get("used_for_decision", policy.used_for_decision)),
            risk_allowed=bool(source_row.get("risk_allowed", policy.risk_allowed)),
            exposure_allowed=bool(source_row.get("exposure_allowed", policy.exposure_allowed)),
            portfolio_change_allowed=bool(
                source_row.get("portfolio_change_allowed", policy.portfolio_change_allowed)
            ),
            allocation_change_allowed=bool(
                source_row.get("allocation_change_allowed", policy.allocation_change_allowed)
            ),
            rebalance_allowed=bool(source_row.get("rebalance_allowed", policy.rebalance_allowed)),
            order_routing_allowed=bool(source_row.get("order_routing_allowed", policy.order_routing_allowed)),
            external_connectivity_allowed=bool(
                source_row.get("external_connectivity_allowed", policy.external_connectivity_allowed)
            ),
            human_review_required=bool(
                source_row.get("human_review_required", policy.human_review_required)
            ),
            ledger_state=policy.ledger_state,
            audit_trail_state=policy.audit_trail_state,
            immutability_mode=policy.immutability_mode,
            ledger_block_reasons=list(DEFAULT_LEDGER_BLOCK_REASONS),
            ledger_checks=self.build_checks(
                decision_firewall_state=str(source_row.get("decision_firewall_state", policy.decision_firewall_state))
            ),
            source_artifacts=list(source_artifacts),
            source_checksums=dict(source_checksums),
            previous_entry_checksum=previous_entry_checksum,
        )
        checksum = build_entry_checksum(entry.to_dict())
        return replace(entry, entry_checksum=checksum)

    def build_entries(
        self,
        timeframe: str,
        *,
        firewall_rows: list[dict[str, Any]],
        source_artifacts: list[str],
        source_checksums: dict[str, str],
    ) -> list[DecisionLedgerEntry]:
        entries: list[DecisionLedgerEntry] = []
        previous_checksum = ""
        for index, row in enumerate(firewall_rows, start=1):
            if str(row.get("timeframe", timeframe)) != timeframe:
                raise ValueError(f"unexpected source timeframe for {timeframe}")
            entry = self.entry_from_source(
                timeframe=timeframe,
                ledger_sequence=index,
                source_row=row,
                previous_entry_checksum=previous_checksum,
                source_artifacts=source_artifacts,
                source_checksums=source_checksums,
            )
            entries.append(entry)
            previous_checksum = entry.entry_checksum
        return entries

    def build_result(
        self,
        *,
        counts_by_timeframe: dict[str, int],
        source_artifacts: list[str],
        output_paths: list[str],
    ) -> DecisionLedgerResult:
        return DecisionLedgerResult(
            policy_version=self.policy_version,
            ledger_version=self.ledger_version,
            counts_by_timeframe=dict(counts_by_timeframe),
            total_entries=sum(counts_by_timeframe.values()),
            source_artifacts=list(source_artifacts),
            output_paths=list(output_paths),
        )
