"""Verify all example files are consistent and accurate."""
import json
from pathlib import Path

checks = []

# 1. Summary
s = json.load(open("examples/incident_42_summary.json"))
checks.append(("validation_passed", s["validation_passed"], True))
checks.append(("health_score", s["health_score"], 89))
checks.append(("datahub_mutations", s["datahub_mutations"], 17))
checks.append(("workers_count", len(s["workers_fired"]), 17))
checks.append(("articles", s["compliance"]["articles_covered"], ["12", "13", "14"]))

# 2. AI Knowledge
ak = json.load(open("examples/ai-knowledge/churn_model_v3.json"))["ai_knowledge_panel"]
checks.append(("resolved_incidents", ak["resolved_incidents"], 15))
checks.append(("health_score_ak", ak["ai_health_score"], 89))
checks.append(("confidence", ak["ai_confidence"], 0.94))

# 3. Resolution times
rt = json.load(open("examples/resolution_times.json"))
checks.append(("flywheel_incidents", len(rt["incidents"]), 3))
checks.append(("improvement_pct", rt["cumulative_intelligence"]["improvement_percentage"], 83))
checks.append(("latest_time", rt["incidents"][-1]["duration_minutes"], 3.0))

# 4. Timeline
tl = json.load(open("examples/incident_42_timeline.json"))
checks.append(("timeline_events", len(tl), 36))

# 5. Incident record
ir = json.load(open("examples/incidents/incident_042_full.json"))
checks.append(("incident_severity", ir["severity"], "HIGH"))
checks.append(("affected_models", len(ir["affected_models"]), 3))

# Print results
all_pass = True
for name, actual, expected in checks:
    status = "PASS" if actual == expected else "FAIL"
    if status == "FAIL":
        all_pass = False
    print(f"  {status}: {name} = {actual} (expected {expected})")

print(f"\n{'ALL CHECKS PASSED' if all_pass else 'SOME CHECKS FAILED'}")
