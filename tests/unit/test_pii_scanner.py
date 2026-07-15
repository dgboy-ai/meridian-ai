"""Tests for PII/PHI scanner."""
import pytest
from backend.scanners.pii_scanner import (
    PIIScanner,
    PIIFinding,
    ComplianceViolation,
    Regulation,
    Severity,
    PII_PATTERNS,
)


class TestPIIScanner:
    def test_init_default_patterns(self):
        scanner = PIIScanner()
        assert len(scanner.patterns) == len(PII_PATTERNS)

    def test_init_custom_patterns(self):
        custom = [{"name": "test", "regex": r"\bTEST\d+\b", "regulation": Regulation.GDPR_ART_25, "severity": Severity.LOW, "recommendation": "test"}]
        scanner = PIIScanner(patterns=custom)
        assert len(scanner.patterns) == 1


class TestEmailDetection:
    def test_detect_email(self):
        scanner = PIIScanner()
        findings = scanner.scan_value("Contact john.doe@example.com for details")
        assert len(findings) == 1
        assert findings[0].pattern_name == "email_address"
        assert findings[0].regulation == Regulation.GDPR_ART_25
        assert findings[0].severity == Severity.HIGH

    def test_detect_multiple_emails(self):
        scanner = PIIScanner()
        findings = scanner.scan_value("Emails: alice@test.com and bob@demo.org")
        assert len(findings) == 2

    def test_no_email_in_clean_text(self):
        scanner = PIIScanner()
        findings = scanner.scan_value("No PII here, just regular text")
        assert len(findings) == 0


class TestSSNDetection:
    def test_detect_ssn(self):
        scanner = PIIScanner()
        findings = scanner.scan_value("SSN: 123-45-6789")
        assert len(findings) == 1
        assert findings[0].pattern_name == "ssn"
        assert findings[0].severity == Severity.CRITICAL

    def test_no_ssn_in_numbers(self):
        scanner = PIIScanner()
        findings = scanner.scan_value("Order number: 123-456-7890")
        assert not any(f.pattern_name == "ssn" for f in findings)


class TestIPDetection:
    def test_detect_ipv4(self):
        scanner = PIIScanner()
        findings = scanner.scan_value("Request from 192.168.1.100")
        assert len(findings) == 1
        assert findings[0].pattern_name == "ipv4_address"
        assert findings[0].severity == Severity.MEDIUM

    def test_detect_multiple_ips(self):
        scanner = PIIScanner()
        findings = scanner.scan_value("IPs: 10.0.0.1 and 172.16.0.1")
        assert len(findings) == 2


class TestPhoneDetection:
    def test_detect_phone_us(self):
        scanner = PIIScanner()
        findings = scanner.scan_value("Call +1-555-123-4567")
        assert len(findings) == 1
        assert findings[0].pattern_name == "phone_number"

    def test_detect_phone_parentheses(self):
        scanner = PIIScanner()
        findings = scanner.scan_value("Phone: (555) 123-4567")
        assert len(findings) == 1


class TestCreditCardDetection:
    def test_detect_visa(self):
        scanner = PIIScanner()
        findings = scanner.scan_value("Card: 4111111111111111")
        assert len(findings) == 1
        assert findings[0].pattern_name == "credit_card"
        assert findings[0].severity == Severity.CRITICAL

    def test_detect_amex(self):
        scanner = PIIScanner()
        findings = scanner.scan_value("Card: 378282246310005")
        assert len(findings) == 1
        assert findings[0].pattern_name == "credit_card"


class TestMedicalRecordDetection:
    def test_detect_mrn(self):
        scanner = PIIScanner()
        findings = scanner.scan_value("Patient MRN: 12345678")
        assert len(findings) == 1
        assert findings[0].pattern_name == "medical_record_number"
        assert findings[0].severity == Severity.CRITICAL
        assert findings[0].regulation == Regulation.HIPAA_164_514


class TestDateOfBirthDetection:
    def test_detect_dob(self):
        scanner = PIIScanner()
        findings = scanner.scan_value("DOB: 1990-05-15")
        assert len(findings) == 1
        assert findings[0].pattern_name == "date_of_birth"
        assert findings[0].severity == Severity.MEDIUM

    def test_detect_dob_slash(self):
        scanner = PIIScanner()
        findings = scanner.scan_value("Born: 01/15/1985")
        assert len(findings) == 1


class TestValueMasking:
    def test_mask_long_value(self):
        masked = PIIFinding.mask_value("john@example.com")
        assert masked == "jo************om"

    def test_mask_short_value(self):
        masked = PIIFinding.mask_value("ab")
        assert masked == "****"


class TestScanDict:
    def test_scan_dict(self):
        scanner = PIIScanner()
        record = {"name": "John", "email": "john@test.com", "ip": "192.168.1.1"}
        findings = scanner.scan_dict(record)
        assert len(findings) == 2
        assert any(f.pattern_name == "email_address" for f in findings)
        assert any(f.pattern_name == "ipv4_address" for f in findings)

    def test_scan_dict_with_column(self):
        scanner = PIIScanner()
        record = {"user_email": "test@example.com"}
        findings = scanner.scan_dict(record, row_index=0)
        assert findings[0].column == "user_email"
        assert findings[0].row_index == 0


class TestScanRecords:
    def test_scan_records(self):
        scanner = PIIScanner()
        records = [
            {"email": "a@test.com", "ip": "1.2.3.4"},
            {"email": "b@test.com", "ssn": "123-45-6789"},
        ]
        violation = scanner.scan_records(records)
        assert violation.total_violations > 0
        assert violation.severity == Severity.CRITICAL
        assert len(violation.affected_columns) > 0

    def test_scan_records_no_violations(self):
        scanner = PIIScanner()
        records = [{"name": "John", "age": "30"}]
        violation = scanner.scan_records(records)
        assert violation.total_violations == 0


class TestComplianceViolation:
    def test_to_dict(self):
        violation = ComplianceViolation(
            violation_id="TEST-001",
            dataset_urn="urn:li:dataset:test",
            dataset_name="test_dataset",
            timestamp="2026-01-01 00:00:00 UTC",
            total_violations=5,
            severity=Severity.HIGH,
            regulations=[Regulation.GDPR_ART_25],
        )
        d = violation.to_dict()
        assert d["violation_id"] == "TEST-001"
        assert d["total_violations"] == 5
        assert d["severity"] == "high"

    def test_to_markdown(self):
        violation = ComplianceViolation(
            violation_id="TEST-002",
            dataset_urn="urn:li:dataset:test",
            dataset_name="test_dataset",
            timestamp="2026-01-01 00:00:00 UTC",
            findings=[
                PIIFinding(
                    pattern_name="email",
                    regulation=Regulation.GDPR_ART_25,
                    severity=Severity.HIGH,
                    matched_value="test@example.com",
                    context="user email field",
                    column="email",
                ),
            ],
            total_violations=1,
            severity=Severity.HIGH,
            regulations=[Regulation.GDPR_ART_25],
        )
        md = violation.to_markdown()
        assert "test_dataset" in md
        assert "GDPR Art. 25" in md
        assert "email" in md


class TestHasViolations:
    def test_has_violations_true(self):
        scanner = PIIScanner()
        assert scanner.has_violations([{"email": "test@example.com"}]) is True

    def test_has_violations_false(self):
        scanner = PIIScanner()
        assert scanner.has_violations([{"name": "John", "age": "30"}]) is False
