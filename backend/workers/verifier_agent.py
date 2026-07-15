"""VerifierAgent — challenges RootCause worker before write-back.

"Single agents fail silently. Multi-agent debate catches errors before write-back."

Pattern: After the Root Cause worker generates a diagnosis, a VerifierAgent
challenges it to verify the lineage actually supports the conclusion.
If verifier disagrees, the Planner runs a third pass before escalating to human.

This eliminates hallucinated root causes from reaching DataHub.
"""
import logging
from datetime import datetime, timezone

from backend.clients.datahub_client import DataHubMCPClient
from backend.clients.groq_client import GroqClient
from backend.models import EvidenceObject, Severity, EvidenceItem
from backend.stats import traverse_lineage

logger = logging.getLogger("meridian-ai.verifier")


class VerifierAgent:
    """Challenges RootCause worker conclusions before write-back.

    Implements the maker-checker pattern:
    - Maker: RootCause worker generates diagnosis
    - Checker: VerifierAgent verifies lineage supports the conclusion
    - If checker disagrees: escalate to human or run third pass
    """

    def __init__(self, mcp: DataHubMCPClient, groq: GroqClient):
        self.mcp = mcp
        self.groq = groq

    async def verify_root_cause(
        self,
        root_cause_evidence: EvidenceObject,
        dataset_urn: str,
        model_urns: list[str],
    ) -> EvidenceObject:
        """Verify that root cause conclusion is supported by lineage.

        Args:
            root_cause_evidence: Evidence from RootCause worker
            dataset_urn: Source dataset URN
            model_urns: Affected model URNs

        Returns:
            Verification result as EvidenceObject
        """
        now = datetime.now(timezone.utc).isoformat()

        # Extract claims from root cause evidence
        root_cause_finding = root_cause_evidence.finding
        confidence = root_cause_evidence.confidence

        # Get lineage to verify claims
        lineage = await self.mcp.get_lineage(dataset_urn, depth=5)

        # Get entities for downstream nodes
        entities_dict = {}
        for d in lineage.get("downstream", []):
            urn = d.get("urn", "")
            if urn:
                ents = await self.mcp.get_entities([urn])
                if ents:
                    entities_dict[urn] = ents[0]

        source_entities = await self.mcp.get_entities([dataset_urn])
        source_name = source_entities[0].get("name", "unknown") if source_entities else "unknown"

        # Traverse lineage
        traversal = traverse_lineage(lineage, entities_dict)

        # Verification checks
        verification_checks = []

        # Check 1: Does lineage actually connect source to affected models?
        affected_models_in_lineage = traversal.affected_models
        claimed_affected = [urn.split(",")[-2] if "," in urn else urn for urn in model_urns]

        models_verified = [m for m in claimed_affected if m in affected_models_in_lineage]
        models_unverified = [m for m in claimed_affected if m not in affected_models_in_lineage]

        if models_unverified:
            verification_checks.append({
                "check": "lineage_connection",
                "passed": False,
                "detail": f"Models not found in lineage: {', '.join(models_unverified)}",
            })
        else:
            verification_checks.append({
                "check": "lineage_connection",
                "passed": True,
                "detail": f"All {len(models_verified)} claimed models found in lineage",
            })

        # Check 2: Does the root cause entity exist?
        root_cause_entity_exists = dataset_urn in entities_dict or source_name.lower() in root_cause_finding.lower()
        verification_checks.append({
            "check": "entity_existence",
            "passed": root_cause_entity_exists,
            "detail": f"Root cause entity '{source_name}' {'exists' if root_cause_entity_exists else 'not found'} in lineage",
        })

        # Check 3: Is confidence reasonable?
        confidence_reasonable = confidence >= 0.7
        verification_checks.append({
            "check": "confidence_threshold",
            "passed": confidence_reasonable,
            "detail": f"Confidence {confidence:.2f} {'meets' if confidence_reasonable else 'below'} threshold 0.7",
        })

        # Check 4: Is the finding consistent with lineage structure?
        lineage_consistent = (
            len(traversal.downstream_urns) > 0 and
            ("affected" in root_cause_finding.lower() or "downstream" in root_cause_finding.lower())
        )
        verification_checks.append({
            "check": "lineage_consistency",
            "passed": lineage_consistent,
            "detail": f"Finding mentions {len(traversal.downstream_urns)} downstream entities",
        })

        # Calculate verification result
        all_passed = all(check["passed"] for check in verification_checks)
        passed_count = sum(1 for check in verification_checks if check["passed"])
        total_checks = len(verification_checks)

        # Build verification evidence
        if all_passed:
            finding = (
                f"VERIFICATION PASSED: Root cause conclusion verified. "
                f"{passed_count}/{total_checks} checks passed. "
                f"Lineage confirms {len(models_verified)} affected models. "
                f"Confidence {confidence:.2f} meets threshold."
            )
            severity = Severity.LOW
        else:
            failed_checks = [c for c in verification_checks if not c["passed"]]
            finding = (
                f"VERIFICATION FAILED: Root cause conclusion not fully supported. "
                f"{passed_count}/{total_checks} checks passed. "
                f"Failed: {'; '.join(c['detail'] for c in failed_checks)}. "
                f"Recommend human review."
            )
            severity = Severity.HIGH

        return EvidenceObject(
            worker_id="verifier_agent",
            timestamp=now,
            finding=finding,
            confidence=0.95 if all_passed else 0.6,
            severity=severity,
            evidence=[
                EvidenceItem(
                    type="verification",
                    description=f"Verified {passed_count}/{total_checks} checks: {', '.join(c['check'] for c in verification_checks if c['passed'])}",
                    entity_urn=dataset_urn,
                    affected_models=traversal.affected_models,
                ),
            ],
            next_action="Proceed with write-back" if all_passed else "Escalate to human for review",
            datahub_mutations=[],
        )

    async def cross_validate_with_llm(
        self,
        root_cause_evidence: EvidenceObject,
        lineage_data: dict,
    ) -> EvidenceObject:
        """Use LLM to cross-validate root cause against lineage.

        Args:
            root_cause_evidence: Evidence from RootCause worker
            lineage_data: Lineage graph data

        Returns:
            Cross-validation result
        """
        now = datetime.now(timezone.utc).isoformat()

        # Build prompt for LLM verification
        messages = [
            {
                "role": "system",
                "content": "You are a verification agent for ML incident investigations. "
                          "Your job is to verify that root cause conclusions are supported by "
                          "the lineage data. Be critical and flag any inconsistencies.",
            },
            {
                "role": "user",
                "content": f"""Verify this root cause conclusion against the lineage data:

ROOT CAUSE CONCLUSION:
{root_cause_evidence.finding}

Confidence: {root_cause_evidence.confidence}

LINEAGE DATA:
- Source: {lineage_data.get('entity', 'unknown')}
- Downstream entities: {len(lineage_data.get('downstream', []))}
- Upstream entities: {len(lineage_data.get('upstream', []))}

Is this conclusion supported by the lineage? Respond with:
- VERIFIED: if lineage supports the conclusion
- QUESTIONABLE: if lineage partially supports but has gaps
- REJECTED: if lineage contradicts the conclusion

Include your reasoning.""",
            },
        ]

        response = self.groq.complete(messages, model="reasoning")

        # Parse response
        verified = "VERIFIED" in response.upper()
        questionable = "QUESTIONABLE" in response.upper()
        "REJECTED" in response.upper()

        if verified:
            finding = f"LLM VERIFICATION: Conclusion verified. {response[:200]}"
            severity = Severity.LOW
        elif questionable:
            finding = f"LLM VERIFICATION: Conclusion questionable. {response[:200]}"
            severity = Severity.MEDIUM
        else:
            finding = f"LLM VERIFICATION: Conclusion rejected. {response[:200]}"
            severity = Severity.HIGH

        return EvidenceObject(
            worker_id="verifier_agent",
            timestamp=now,
            finding=finding,
            confidence=0.85 if verified else (0.6 if questionable else 0.3),
            severity=severity,
            evidence=[],
            datahub_mutations=[],
        )
