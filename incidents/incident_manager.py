import json
import os
from datetime import datetime
from uuid import uuid4

INCIDENT_FILE = os.path.join(os.path.dirname(__file__), "incidents.json")
ALLOWED_SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]


def now():
    return datetime.now().isoformat(timespec="seconds")


def load_incidents():
    if not os.path.exists(INCIDENT_FILE):
        return []
    try:
        with open(INCIDENT_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_incidents(incidents):
    os.makedirs(os.path.dirname(INCIDENT_FILE), exist_ok=True)
    temp_file = INCIDENT_FILE + ".tmp"
    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump(incidents, file, indent=4)
    os.replace(temp_file, INCIDENT_FILE)


def detect_severity(message):
    text = message.lower()

    if any(word in text for word in [
        "critical", "system crash", "data loss", "security breach",
        "production down", "complete outage"
    ]):
        return "CRITICAL"

    if any(word in text for word in [
        "database", "connection refused", "payment failure",
        "server down", "service unavailable", "connection failed"
    ]):
        return "HIGH"

    if any(word in text for word in [
        "warning", "high cpu", "high ram", "memory usage",
        "disk usage", "slow response"
    ]):
        return "MEDIUM"

    return "LOW"


def _normalize_message(message):
    return " ".join(str(message).strip().lower().split())


def create_incident(message, severity=None):
    message = str(message).strip()
    if not message:
        raise ValueError("Incident message cannot be empty")

    incidents = load_incidents()

    if severity is None or not str(severity).strip():
        severity = detect_severity(message)
    else:
        severity = str(severity).strip().upper()

    if severity not in ALLOWED_SEVERITIES:
        raise ValueError(
            "Invalid incident severity. Allowed: CRITICAL, HIGH, MEDIUM, LOW"
        )

    normalized = _normalize_message(message)

    # Deduplicate only against currently OPEN incidents.
    for existing in incidents:
        if (
            existing.get("status") == "OPEN"
            and _normalize_message(existing.get("message", "")) == normalized
        ):
            timestamp = now()
            existing["occurrence_count"] = int(existing.get("occurrence_count", 1)) + 1
            existing["last_seen_at"] = timestamp
            existing["updated_at"] = timestamp
            existing.setdefault("history", []).append({
                "action": "DUPLICATE_DETECTED",
                "timestamp": timestamp,
                "details": "Repeated occurrence attached to this open incident"
            })
            save_incidents(incidents)
            result = dict(existing)
            result["duplicate_detected"] = True
            return result

    timestamp = now()
    incident = {
        "incident_id": str(uuid4()).replace("-", "")[:8].upper(),
        "message": message,
        "severity": severity,
        "status": "OPEN",
        "created_at": timestamp,
        "updated_at": timestamp,
        "last_seen_at": timestamp,
        "resolved_at": None,
        "reopened_at": None,
        "occurrence_count": 1,
        "history": [{
            "action": "CREATED",
            "timestamp": timestamp,
            "details": "Incident created"
        }]
    }

    incidents.append(incident)
    save_incidents(incidents)

    result = dict(incident)
    result["duplicate_detected"] = False
    return result


def get_incidents(search=None, status=None, severity=None):
    incidents = load_incidents()

    if search:
        term = str(search).strip().lower()
        incidents = [
            item for item in incidents
            if term in item.get("incident_id", "").lower()
            or term in item.get("message", "").lower()
        ]

    if status:
        status_value = str(status).strip().upper()
        incidents = [
            item for item in incidents
            if item.get("status", "").upper() == status_value
        ]

    if severity:
        severity_value = str(severity).strip().upper()
        incidents = [
            item for item in incidents
            if item.get("severity", "").upper() == severity_value
        ]

    return sorted(
        incidents,
        key=lambda item: item.get("created_at", ""),
        reverse=True
    )


def get_incident(incident_id):
    for incident in load_incidents():
        if incident.get("incident_id", "").upper() == incident_id.upper():
            return incident
    return None


def resolve_incident(incident_id):
    incidents = load_incidents()

    for incident in incidents:
        if incident.get("incident_id", "").upper() == incident_id.upper():
            if incident.get("status") == "RESOLVED":
                return incident

            timestamp = now()
            incident["status"] = "RESOLVED"
            incident["resolved_at"] = timestamp
            incident["updated_at"] = timestamp
            incident.setdefault("history", []).append({
                "action": "RESOLVED",
                "timestamp": timestamp,
                "details": "Incident marked as resolved"
            })
            save_incidents(incidents)
            return incident

    return None


def reopen_incident(incident_id):
    incidents = load_incidents()

    for incident in incidents:
        if incident.get("incident_id", "").upper() == incident_id.upper():
            if incident.get("status") != "RESOLVED":
                return None

            timestamp = now()
            incident["status"] = "OPEN"
            incident["resolved_at"] = None
            incident["reopened_at"] = timestamp
            incident["updated_at"] = timestamp
            incident.setdefault("history", []).append({
                "action": "REOPENED",
                "timestamp": timestamp,
                "details": "Incident reopened"
            })
            save_incidents(incidents)
            return incident

    return None
