"""Actions Framework listener — receives DataHub metadata change events.

This listener accepts events from DataHub's Actions Framework via HTTP webhook
or Kafka consumer. For hackathon demo, the webhook mode is primary.

In production, the Kafka consumer polls MetadataChangeLog_v1 topic and
dispatches events to the appropriate handler.
"""
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger("meridian-ai.actions.listener")


class ActionEvent:
    """Parsed DataHub metadata change event."""

    def __init__(self, raw: dict):
        self.event_type = raw.get("event_type", raw.get("eventType", "unknown"))
        self.entity_urn = raw.get("entity_urn", raw.get("entityUrn", ""))
        self.aspect = raw.get("aspect", raw.get("aspectName", ""))
        self.old_value = raw.get("old_value", raw.get("oldValue"))
        self.new_value = raw.get("new_value", raw.get("newValue"))
        self.timestamp = raw.get("timestamp", datetime.now(timezone.utc).isoformat())
        self._raw = raw

    @property
    def is_schema_change(self) -> bool:
        return self.aspect in ("schemaMetadata", "editableSchemaMetadata")

    @property
    def is_ownership_change(self) -> bool:
        return self.aspect == "ownership"

    def severity(self) -> str:
        if self.is_schema_change:
            return "HIGH"
        if self.is_ownership_change:
            return "HIGH"
        if self.aspect in ("globalTags", "browsePaths"):
            return "MEDIUM"
        return "LOW"


class ActionsListener:
    """Receives and processes DataHub Actions Framework events."""

    def __init__(self):
        self._event_log: list[dict] = []
        self._handlers: dict[str, list] = {}

    def register_handler(self, event_type: str, handler):
        """Register a handler for a specific event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def process_webhook_event(self, raw_event: dict) -> dict:
        """Process an event received via webhook.

        This is called by the FastAPI endpoint when DataHub sends an event.
        """
        event = ActionEvent(raw_event)
        self._event_log.append({
            "event_type": event.event_type,
            "entity_urn": event.entity_urn,
            "aspect": event.aspect,
            "severity": event.severity(),
            "timestamp": event.timestamp,
        })

        logger.info(
            f"Actions event: {event.event_type} | {event.aspect} | "
            f"{event.entity_urn} | severity={event.severity()}"
        )

        # Determine if investigation is warranted
        should_investigate = event.severity() in ("HIGH", "CRITICAL")

        investigation_id = None
        if should_investigate:
            investigation_id = f"AUTO-{int(datetime.now(timezone.utc).timestamp())}"
            logger.info(f"Auto-investigation {investigation_id} triggered for {event.entity_urn}")

        return {
            "status": "investigation_started" if should_investigate else "event_logged",
            "investigation_id": investigation_id,
            "event": {
                "event_type": event.event_type,
                "entity_urn": event.entity_urn,
                "aspect": event.aspect,
                "severity": event.severity(),
                "timestamp": event.timestamp,
            },
            "should_investigate": should_investigate,
        }

    def get_event_log(self) -> list[dict]:
        return list(self._event_log)

    def get_stats(self) -> dict:
        return {
            "total_events": len(self._event_log),
            "high_severity": sum(1 for e in self._event_log if e.get("severity") == "HIGH"),
            "investigations_triggered": sum(1 for e in self._event_log if e.get("severity") in ("HIGH", "CRITICAL")),
        }


class KafkaEventConsumer:
    """Kafka consumer for DataHub MetadataChangeLog_v1 topic.

    For production use. For hackathon demo, use the webhook listener.
    """

    def __init__(self, bootstrap: str, topic: str = "MetadataChangeLog_v1", group_id: str = "meridian-ai"):
        self.bootstrap = bootstrap
        self.topic = topic
        self.group_id = group_id
        self._running = False

    async def start(self, handler):
        """Start consuming events. Requires confluent-kafka or kafka-python."""
        try:
            from confluent_kafka import Consumer, KafkaError

            consumer = Consumer({
                "bootstrap.servers": self.bootstrap,
                "group.id": self.group_id,
                "auto.offset.reset": "latest",
            })
            consumer.subscribe([self.topic])
            self._running = True

            logger.info(f"Kafka consumer started: {self.topic} @ {self.bootstrap}")

            while self._running:
                msg = consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    logger.error(f"Kafka error: {msg.error()}")
                    continue

                try:
                    event_data = json.loads(msg.value().decode("utf-8"))
                    await handler(event_data)
                except Exception as e:
                    logger.error(f"Failed to process Kafka message: {e}")

        except ImportError:
            logger.warning("confluent-kafka not installed. Kafka consumer unavailable.")
        except Exception as e:
            logger.error(f"Kafka consumer failed: {e}")

    def stop(self):
        self._running = False
