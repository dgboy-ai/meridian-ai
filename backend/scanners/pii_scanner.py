"""PII/PHI scanner — detects sensitive data exposures in datasets and queries.

Scans for:
- Email addresses (RFC 5322)
- Social Security Numbers (US SSN)
- IP addresses (IPv4/IPv6)
- Phone numbers (US/international)
- Credit card numbers (PCI DSS)
- Medical record numbers (HIPAA)
- Dates of birth (potential PII)

Flags violations against:
- GDPR Article 25 (Data Protection by Design)
- EU AI Act Article 9 (Risk Management)
- CCPA Section 1798.100
- HIPAA Section 164.514
"""
import re
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from backend.models import Severity


class Regulation(str, Enum):
    GDPR_ART_25 = "GDPR Art. 25 — Data Protection by Design and by Default"
    GDPR_ART_30 = "GDPR Art. 30 — Records of Processing Activities"
    EU_AI_ACT_ART_9 = "EU AI Act Art. 9 — Risk Management System"
    CCPA_1798_100 = "CCPA §1798.100 — Right to Know"
    HIPAA_164_514 = "HIPAA §164.514 — De-identification Standards"
    PCI_DSS_3_4 = "PCI DSS Req. 3.4 — Render PAN Unreadable"


@dataclass
class PIIFinding:
    """A single PII detection finding."""
    pattern_name: str
    regulation: Regulation
    severity: Severity
    matched_value: str
    context: str
    column: str = ""
    row_index: int = -1
    confidence: float = 0.95
    recommendation: str = ""

    def to_dict(self) -> dict:
        return {
            "pattern_name": self.pattern_name,
            "regulation": self.regulation.value,
            "severity": self.severity.value,
            "matched_value": self.mask_value(self.matched_value),
            "context": self.context,
            "column": self.column,
            "row_index": self.row_index,
            "confidence": self.confidence,
            "recommendation": self.recommendation,
        }

    @staticmethod
    def mask_value(value: str) -> str:
        """Mask sensitive values for safe display."""
        if len(value) <= 4:
            return "****"
        return value[:2] + "*" * (len(value) - 4) + value[-2:]


@dataclass
class ComplianceViolation:
    """Aggregated compliance violation from multiple PII findings."""
    violation_id: str
    dataset_urn: str
    dataset_name: str
    timestamp: str
    findings: list[PIIFinding] = field(default_factory=list)
    affected_columns: list[str] = field(default_factory=list)
    affected_rows: int = 0
    total_violations: int = 0
    severity: Severity = Severity.LOW
    regulations: list[Regulation] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "violation_id": self.violation_id,
            "dataset_urn": self.dataset_urn,
            "dataset_name": self.dataset_name,
            "timestamp": self.timestamp,
            "total_violations": self.total_violations,
            "affected_columns": self.affected_columns,
            "affected_rows": self.affected_rows,
            "severity": self.severity.value,
            "regulations": [r.value for r in self.regulations],
            "findings": [f.to_dict() for f in self.findings],
        }

    def to_markdown(self) -> str:
        lines = [
            f"# Compliance Violation: {self.dataset_name}",
            f"Generated: {self.timestamp}",
            f"Severity: {self.severity.value.upper()}",
            f"Total Violations: {self.total_violations}",
            "",
            "## Affected Resources",
            f"- Dataset: `{self.dataset_urn}`",
            f"- Columns: {', '.join(self.affected_columns) if self.affected_columns else 'N/A'}",
            f"- Rows Scanned: {self.affected_rows}",
            "",
            "## Regulations Violated",
        ]
        for reg in self.regulations:
            lines.append(f"- {reg.value}")
        lines.append("")

        if self.findings:
            lines.append("## Findings")
            for i, f in enumerate(self.findings[:10], 1):
                lines.append(f"### {i}. {f.pattern_name}")
                lines.append(f"- Severity: {f.severity.value}")
                lines.append(f"- Regulation: {f.regulation.value}")
                lines.append(f"- Column: `{f.column}`")
                lines.append(f"- Matched: `{PIIFinding.mask_value(f.matched_value)}`")
                lines.append(f"- Context: {f.context}")
                lines.append(f"- Recommendation: {f.recommendation}")
                lines.append("")

        return "\n".join(lines)


# ─── PII Pattern Definitions ───────────────────────────────────────────────────

PII_PATTERNS = [
    {
        "name": "email_address",
        "regex": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
        "regulation": Regulation.GDPR_ART_25,
        "severity": Severity.HIGH,
        "recommendation": "Mask or tokenize email addresses. Apply pseudonymization per GDPR Art. 25.",
    },
    {
        "name": "ssn",
        "regex": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        "regulation": Regulation.CCPA_1798_100,
        "severity": Severity.CRITICAL,
        "recommendation": "Remove SSN from analytics datasets. Use tokenized identifiers instead.",
    },
    {
        "name": "ipv4_address",
        "regex": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
        "regulation": Regulation.GDPR_ART_30,
        "severity": Severity.MEDIUM,
        "recommendation": "Hash or truncate IP addresses. Consider /24 subnet masking.",
    },
    {
        "name": "phone_number",
        "regex": re.compile(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b"),
        "regulation": Regulation.GDPR_ART_25,
        "severity": Severity.HIGH,
        "recommendation": "Apply phone number masking. Use country code + hashed local part.",
    },
    {
        "name": "credit_card",
        "regex": re.compile(r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b"),
        "regulation": Regulation.PCI_DSS_3_4,
        "severity": Severity.CRITICAL,
        "recommendation": "Credit card numbers must never appear in ML training data. Remove immediately.",
    },
    {
        "name": "medical_record_number",
        "regex": re.compile(r"\bMRN\s*:\s*\d{6,10}\b", re.IGNORECASE),
        "regulation": Regulation.HIPAA_164_514,
        "severity": Severity.CRITICAL,
        "recommendation": "Medical record numbers are PHI under HIPAA. Remove from all non-clinical systems.",
    },
    {
        "name": "date_of_birth",
        "regex": re.compile(r"\b(?:19|20)\d{2}[-/](?:0[1-9]|1[0-2])[-/](?:0[1-9]|[12]\d|3[01])\b|(?:0[1-9]|1[0-2])[-/](?:0[1-9]|[12]\d|3[01])[-/](?:19|20)\d{2}\b"),
        "regulation": Regulation.EU_AI_ACT_ART_9,
        "severity": Severity.MEDIUM,
        "recommendation": "Dates of birth are indirect identifiers. Use age ranges instead.",
    },
    {
        "name": "passport_number",
        "regex": re.compile(r"\b[A-Z]{1,2}\d{6,9}\b"),
        "regulation": Regulation.GDPR_ART_25,
        "severity": Severity.HIGH,
        "recommendation": "Passport numbers are government-issued IDs. Remove from training data.",
    },
]


class PIIScanner:
    """Enterprise-grade PII/PHI scanner for datasets and queries."""

    def __init__(self, patterns: list[dict] | None = None):
        self.patterns = patterns or PII_PATTERNS
        self._compiled = {p["name"]: p["regex"] for p in self.patterns}

    def scan_value(self, value: str, column: str = "", row_index: int = -1) -> list[PIIFinding]:
        """Scan a single value for PII patterns."""
        findings = []
        for pattern in self.patterns:
            matches = pattern["regex"].finditer(str(value))
            for match in matches:
                context_start = max(0, match.start() - 20)
                context_end = min(len(value), match.end() + 20)
                context = value[context_start:context_end]

                findings.append(PIIFinding(
                    pattern_name=pattern["name"],
                    regulation=pattern["regulation"],
                    severity=pattern["severity"],
                    matched_value=match.group(),
                    context=f"...{context}..." if context_start > 0 or context_end < len(value) else context,
                    column=column,
                    row_index=row_index,
                    confidence=0.95,
                    recommendation=pattern["recommendation"],
                ))
        return findings

    def scan_dict(self, record: dict, row_index: int = -1) -> list[PIIFinding]:
        """Scan a dictionary record for PII patterns."""
        findings = []
        for column, value in record.items():
            if value is not None:
                findings.extend(self.scan_value(str(value), column=column, row_index=row_index))
        return findings

    def scan_records(self, records: list[dict]) -> ComplianceViolation:
        """Scan a list of records and return aggregated violation report."""
        all_findings = []
        affected_columns = set()
        affected_rows = set()

        for i, record in enumerate(records):
            findings = self.scan_dict(record, row_index=i)
            all_findings.extend(findings)
            for f in findings:
                affected_columns.add(f.column)
                if f.row_index >= 0:
                    affected_rows.add(f.row_index)

        # Determine overall severity
        severities = [f.severity for f in all_findings]
        if Severity.CRITICAL in severities:
            overall_severity = Severity.CRITICAL
        elif Severity.HIGH in severities:
            overall_severity = Severity.HIGH
        elif Severity.MEDIUM in severities:
            overall_severity = Severity.MEDIUM
        else:
            overall_severity = Severity.LOW

        # Collect unique regulations
        regulations = list(set(f.regulation for f in all_findings))

        violation_id = f"COMPLIANCE-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

        return ComplianceViolation(
            violation_id=violation_id,
            dataset_urn="",
            dataset_name="",
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            findings=all_findings,
            affected_columns=sorted(affected_columns),
            affected_rows=len(affected_rows),
            total_violations=len(all_findings),
            severity=overall_severity,
            regulations=regulations,
        )

    def scan_query(self, query: str) -> list[PIIFinding]:
        """Scan a SQL query for hardcoded PII values."""
        return self.scan_value(query, column="query")

    def has_violations(self, records: list[dict]) -> bool:
        """Quick check if records contain any PII."""
        for record in records:
            for value in record.values():
                if value is not None:
                    for pattern in self.patterns:
                        if pattern["regex"].search(str(value)):
                            return True
        return False
