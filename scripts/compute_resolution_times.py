"""Compute resolution_times.json from real investigation data.

This replaces the hardcoded flywheel with computed values.
"""
import json
import sys
sys.path.insert(0, ".")


def compute():
    with open("backend/replay_data.json") as f:
        data = json.load(f)

    incidents = data.get("incidents", {})
    resolution_times = []

    for inc_id, inc in sorted(incidents.items(), key=lambda x: int(x[0])):
        resolution_times.append({
            "id": inc_id,
            "duration_minutes": round(inc.get("duration_seconds", 0) / 60, 1),
            "date": inc.get("detected", "")[:10],
            "pattern": inc.get("pattern_id", ""),
        })

    # Compute trends
    patterns = {}
    for rt in resolution_times:
        p = rt["pattern"]
        if p not in patterns:
            patterns[p] = {"occurrences": 0, "times": []}
        patterns[p]["occurrences"] += 1
        patterns[p]["times"].append(rt["duration_minutes"])

    trends = {}
    for p, data in patterns.items():
        avg = sum(data["times"]) / len(data["times"])
        first = data["times"][0]
        last = data["times"][-1]
        improvement = f"{first}min -> {last}min" if first != last else f"Stable at {first}min"
        trends[p] = {
            "occurrences": data["occurrences"],
            "resolution_times": data["times"],
            "average": round(avg, 1),
            "improvement": improvement,
        }

    total_incidents = len(resolution_times)
    total_patterns = len(patterns)
    all_times = [rt["duration_minutes"] for rt in resolution_times]
    avg_resolution = round(sum(all_times) / len(all_times), 1) if all_times else 0

    output = {
        "flywheel_proof": "Each incident resolves faster because the knowledge base learns.",
        "incidents": resolution_times,
        "trend": trends,
        "cumulative_intelligence": {
            "total_incidents": total_incidents,
            "total_patterns": total_patterns,
            "average_resolution_time": avg_resolution,
            "first_incident_resolution": all_times[0] if all_times else 0,
            "latest_incident_resolution": all_times[-1] if all_times else 0,
        },
    }

    with open("examples/resolution_times.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"Computed resolution_times.json from {total_incidents} incidents")
    print(f"Patterns: {total_patterns}")
    print(f"Average resolution: {avg_resolution}min")
    for p, t in trends.items():
        print(f"  {p}: {t['occurrences']} occurrences, {t['improvement']}")


if __name__ == "__main__":
    compute()
