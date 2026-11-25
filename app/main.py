import logging
from pathlib import Path

import psutil
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.ai_analyzer import analyze_error
from incidents.incident_manager import (
    create_incident,
    get_incidents,
    get_incident,
    resolve_incident,
    reopen_incident,
)

app = FastAPI(
    title="AI DevOps Monitoring System",
    description="AI-powered DevOps monitoring and incident management",
    version="2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    force=True,
)
logger = logging.getLogger(__name__)

DASHBOARD_DIR = BASE_DIR / "dashboard"
if DASHBOARD_DIR.exists():
    app.mount(
        "/dashboard",
        StaticFiles(directory=str(DASHBOARD_DIR), html=True),
        name="dashboard",
    )


class LogRequest(BaseModel):
    level: str
    message: str


class IncidentRequest(BaseModel):
    message: str
    severity: str | None = None


last_system_status = {"cpu": False, "memory": False}


@app.get("/")
def home():
    return {
        "message": "AI DevOps Monitoring System is running",
        "status": "success",
        "version": "2.0",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "API is running successfully"}


@app.post("/logs")
def create_log(log: LogRequest):
    level = log.level.strip().upper()
    message = log.message.strip()

    if level not in ["INFO", "WARNING", "ERROR"]:
        raise HTTPException(status_code=400, detail="Invalid log level")
    if not message:
        raise HTTPException(status_code=400, detail="Log message cannot be empty")

    if level == "ERROR":
        logger.error(message)
        incident = create_incident(message)
        logger.info(
            "Automatic incident handling: %s (%s)",
            incident["incident_id"],
            "duplicate occurrence" if incident.get("duplicate_detected") else "created",
        )
    elif level == "WARNING":
        logger.warning(message)
        incident = None
    else:
        logger.info(message)
        incident = None

    return {
        "status": "success",
        "message": "Log saved successfully",
        "incident_created": bool(incident and not incident.get("duplicate_detected")),
        "duplicate_detected": bool(incident and incident.get("duplicate_detected")),
        "incident": incident,
    }


@app.get("/logs")
def get_logs():
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as file:
            logs = file.readlines()
        return {"total_logs": len(logs), "logs": logs[-100:]}
    except FileNotFoundError:
        return {"total_logs": 0, "logs": []}


@app.post("/analyze")
def analyze_log(log: LogRequest):
    if log.level.strip().upper() != "ERROR":
        raise HTTPException(
            status_code=400,
            detail="Only ERROR logs can be analyzed",
        )
    try:
        analysis = analyze_error(log.message)
        return {
            "status": "success",
            "error": log.message,
            "ai_analysis": analysis,
        }
    except Exception as exc:
        logger.exception("AI analysis failed")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/system/metrics")
def system_metrics():
    global last_system_status

    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    memory_percent = memory.percent

    total_memory_gb = round(memory.total / (1024 ** 3), 2)
    available_memory_gb = round(memory.available / (1024 ** 3), 2)

    alerts = []

    if cpu_percent > 90:
        alerts.append("CPU usage is above 90 percent")
        if not last_system_status["cpu"]:
            logger.warning("CPU usage is above 90 percent")
        last_system_status["cpu"] = True
    else:
        if last_system_status["cpu"]:
            logger.info("CPU usage returned to normal")
        last_system_status["cpu"] = False

    if memory_percent > 90:
        alerts.append("RAM usage is above 90 percent")
        if not last_system_status["memory"]:
            logger.warning("RAM usage is above 90 percent")
        last_system_status["memory"] = True
    else:
        if last_system_status["memory"]:
            logger.info("RAM usage returned to normal")
        last_system_status["memory"] = False

    # Both naming styles are returned for compatibility with existing clients.
    return {
        "cpu_percent": cpu_percent,
        "memory_percent": memory_percent,
        "total_memory_gb": total_memory_gb,
        "available_memory_gb": available_memory_gb,
        "cpu_usage": cpu_percent,
        "ram_usage": memory_percent,
        "total_ram_gb": total_memory_gb,
        "available_ram_gb": available_memory_gb,
        "alerts": alerts,
    }


@app.post("/incidents")
def create_new_incident(request: IncidentRequest):
    try:
        incident = create_incident(request.message, request.severity)
        if incident.get("duplicate_detected"):
            message = "Matching OPEN incident found; occurrence count updated"
        else:
            message = "Incident created successfully"

        logger.info(
            "Incident request handled: %s",
            incident["incident_id"],
        )
        return {
            "status": "success",
            "message": message,
            "duplicate_detected": incident.get("duplicate_detected", False),
            "incident": incident,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/incidents")
def list_incidents(
    q: str | None = Query(default=None, description="Search by incident ID or message"),
    status: str | None = Query(default=None),
    severity: str | None = Query(default=None),
):
    allowed_statuses = {"OPEN", "RESOLVED"}
    allowed_severities = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}

    if status and status.upper() not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Status must be OPEN or RESOLVED")
    if severity and severity.upper() not in allowed_severities:
        raise HTTPException(
            status_code=400,
            detail="Severity must be CRITICAL, HIGH, MEDIUM, or LOW",
        )

    incidents = get_incidents(search=q, status=status, severity=severity)
    all_incidents = get_incidents()

    return {
        "total_incidents": len(incidents),
        "open_incidents": sum(i.get("status") == "OPEN" for i in all_incidents),
        "resolved_incidents": sum(i.get("status") == "RESOLVED" for i in all_incidents),
        "critical_incidents": sum(i.get("severity") == "CRITICAL" for i in all_incidents),
        "high_incidents": sum(i.get("severity") == "HIGH" for i in all_incidents),
        "medium_incidents": sum(i.get("severity") == "MEDIUM" for i in all_incidents),
        "low_incidents": sum(i.get("severity") == "LOW" for i in all_incidents),
        "filters": {"q": q, "status": status, "severity": severity},
        "incidents": incidents,
    }


@app.get("/incidents/{incident_id}")
def incident_details(incident_id: str):
    incident = get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return {"status": "success", "incident": incident}


@app.patch("/incidents/{incident_id}/resolve")
def resolve_existing_incident(incident_id: str):
    incident = resolve_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    logger.info("Incident resolved: %s", incident_id)
    return {
        "status": "success",
        "message": "Incident resolved successfully",
        "incident": incident,
    }


@app.patch("/incidents/{incident_id}/reopen")
def reopen_existing_incident(incident_id: str):
    existing = get_incident(incident_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Incident not found")
    if existing.get("status") != "RESOLVED":
        raise HTTPException(status_code=409, detail="Only RESOLVED incidents can be reopened")

    incident = reopen_incident(incident_id)
    logger.info("Incident reopened: %s", incident_id)
    return {
        "status": "success",
        "message": "Incident reopened successfully",
        "incident": incident,
    }
