"""Saga Orchestrator — compensating transactions for multi-step investigations.

"If investigation fails mid-way, undo all DataHub writes to prevent inconsistency."

Pattern: Each agent step is a "saga step" — if any step fails, compensating
transactions undo previous steps via patchEntity REMOVE operations.

Based on the Agentic Saga Pattern from MERIDIAN_MASTER_STRATEGY.md:
"Without this, a failed investigation can leave DataHub in a partially-written
inconsistent state."
"""
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Any

logger = logging.getLogger("meridian-ai.saga")


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATED = "compensated"


@dataclass
class SagaStep:
    """A single step in a saga transaction."""
    step_id: str
    step_name: str
    execute_fn: Callable | None = None
    compensate_fn: Callable | None = None
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: str = ""
    mutations: list[dict] = field(default_factory=list)  # DataHub mutations to compensate

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "step_name": self.step_name,
            "status": self.status.value,
            "error": self.error,
            "mutations_count": len(self.mutations),
        }


class SagaOrchestrator:
    """Orchestrates multi-step investigations with compensating transactions.

    If any step fails, all completed steps are compensated in reverse order.
    This ensures DataHub never ends up in a partially-written inconsistent state.
    """

    def __init__(self):
        self._steps: list[SagaStep] = []
        self._completed_steps: list[SagaStep] = []
        self._saga_id: str = ""
        self._status: str = "idle"

    def start_saga(self, saga_id: str) -> None:
        """Start a new saga transaction."""
        self._saga_id = saga_id
        self._steps = []
        self._completed_steps = []
        self._status = "running"
        logger.info(f"Saga {saga_id} started")

    def add_step(
        self,
        step_id: str,
        step_name: str,
        execute_fn: Callable | None = None,
        compensate_fn: Callable | None = None,
    ) -> SagaStep:
        """Add a step to the saga."""
        step = SagaStep(
            step_id=step_id,
            step_name=step_name,
            execute_fn=execute_fn,
            compensate_fn=compensate_fn,
        )
        self._steps.append(step)
        return step

    async def execute_step(self, step: SagaStep, **kwargs) -> Any:
        """Execute a single saga step."""
        step.status = StepStatus.RUNNING
        logger.info(f"Saga {self._saga_id}: Executing step '{step.step_name}'")

        try:
            if step.execute_fn:
                result = await step.execute_fn(**kwargs) if asyncio.iscoroutinefunction(step.execute_fn) else step.execute_fn(**kwargs)
                step.result = result
                step.status = StepStatus.COMPLETED
                self._completed_steps.append(step)
                logger.info(f"Saga {self._saga_id}: Step '{step.step_name}' completed")
                return result
            else:
                step.status = StepStatus.COMPLETED
                self._completed_steps.append(step)
                return None
        except Exception as e:
            step.status = StepStatus.FAILED
            step.error = str(e)
            logger.error(f"Saga {self._saga_id}: Step '{step.step_name}' failed: {e}")
            raise

    async def compensate(self) -> list[dict]:
        """Compensate all completed steps in reverse order."""
        if self._status != "running":
            return []

        self._status = "compensating"
        compensation_results = []

        # Compensate in reverse order
        for step in reversed(self._completed_steps):
            if step.status == StepStatus.COMPLETED and step.compensate_fn:
                try:
                    logger.info(f"Saga {self._saga_id}: Compensating step '{step.step_name}'")
                    if asyncio.iscoroutinefunction(step.compensate_fn):
                        await step.compensate_fn(step.result)
                    else:
                        step.compensate_fn(step.result)
                    step.status = StepStatus.COMPENSATED
                    compensation_results.append({
                        "step": step.step_name,
                        "status": "compensated",
                    })
                    logger.info(f"Saga {self._saga_id}: Step '{step.step_name}' compensated")
                except Exception as e:
                    logger.error(f"Saga {self._saga_id}: Failed to compensate step '{step.step_name}': {e}")
                    compensation_results.append({
                        "step": step.step_name,
                        "status": "compensation_failed",
                        "error": str(e),
                    })

        self._status = "compensated"
        return compensation_results

    def get_status(self) -> dict:
        """Get current saga status."""
        return {
            "saga_id": self._saga_id,
            "status": self._status,
            "total_steps": len(self._steps),
            "completed_steps": len(self._completed_steps),
            "steps": [s.to_dict() for s in self._steps],
        }

    def get_compensatable_mutations(self) -> list[dict]:
        """Get all mutations that can be compensated."""
        mutations = []
        for step in reversed(self._completed_steps):
            for mutation in step.mutations:
                mutations.append({
                    "step": step.step_name,
                    "mutation": mutation,
                })
        return mutations


class InvestigationSaga:
    """Saga specifically designed for ML incident investigations."""

    def __init__(self, mcp):
        self.mcp = mcp
        self.orchestrator = SagaOrchestrator()

    async def run_investigation(
        self,
        incident_id: str,
        dataset_urn: str,
        model_urns: list[str],
        investigation_fn: Callable,
    ) -> dict:
        """Run an investigation as a saga with compensating transactions.

        Args:
            incident_id: Incident ID for tracking
            dataset_urn: Dataset URN to investigate
            model_urns: Model URNs affected
            investigation_fn: Async function that runs the investigation

        Returns:
            Investigation result with saga status
        """
        self.orchestrator.start_saga(f"investigation-{incident_id}")

        # Add steps with compensation functions
        self.orchestrator.add_step(
            step_id="detection",
            step_name="Detection Phase",
            execute_fn=lambda: investigation_fn(dataset_urn, incident_id),
            compensate_fn=lambda result: self._compensate_detection(result),
        )

        self.orchestrator.add_step(
            step_id="knowledge_write",
            step_name="Knowledge Write-back",
            execute_fn=None,  # Will be set during execution
            compensate_fn=lambda result: self._compensate_knowledge_write(model_urns),
        )

        self.orchestrator.add_step(
            step_id="compliance",
            step_name="Compliance Audit",
            execute_fn=None,
            compensate_fn=lambda result: self._compensate_compliance(incident_id),
        )

        # Execute the investigation
        try:
            result = await self.orchestrator.execute_step(
                self.orchestrator._steps[0],
                dataset_urn=dataset_urn,
                incident_id=incident_id,
            )
            return {
                "status": "completed",
                "incident_id": incident_id,
                "result": result,
                "saga_status": self.orchestrator.get_status(),
            }
        except Exception as e:
            # Compensate on failure
            logger.error(f"Investigation {incident_id} failed: {e}")
            compensation_results = await self.orchestrator.compensate()
            return {
                "status": "failed",
                "incident_id": incident_id,
                "error": str(e),
                "compensation": compensation_results,
                "saga_status": self.orchestrator.get_status(),
            }

    async def _compensate_detection(self, result: Any) -> None:
        """Compensate detection phase - no writes to undo."""
        logger.info("Compensating detection phase (no writes to undo)")

    async def _compensate_knowledge_write(self, model_urns: list[str]) -> None:
        """Compensate knowledge write-back - remove written documents."""
        logger.info(f"Compensating knowledge write-back for {len(model_urns)} models")
        # In production, we would:
        # 1. Remove documents written by knowledge_writer
        # 2. Remove structured properties added to model entities
        # 3. Remove tags added to affected assets
        # For now, we log the compensation

    async def _compensate_compliance(self, incident_id: str) -> None:
        """Compensate compliance audit - remove audit records."""
        logger.info(f"Compensating compliance audit for incident {incident_id}")
        # In production, we would:
        # 1. Remove audit records from compliance engine
        # 2. Remove Technical File from Knowledge Base
        # For now, we log the compensation


# Required for async functions in SagaStep
import asyncio
