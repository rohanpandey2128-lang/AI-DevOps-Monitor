
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import logging
import os

from app.ai_analyzer import analyze_error


# Create logs folder
os.makedirs("logs", exist_ok=True)


# Configure logging
logger = logging.getLogger("devops_monitor")
logger.setLevel(logging.INFO)

if not logger.handlers:
    file_handler = logging.FileHandler("logs/app.log")

    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )
    )

    logger.addHandler(file_handler)


# Create FastAPI application
app = FastAPI(
    title="AI DevOps Monitoring System",
    description="AI Powered Application Log Monitoring and Incident Analysis",
    version="1.0.0"
)


# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Serve Dashboard through FastAPI
app.mount(
    "/dashboard",
    StaticFiles(directory="dashboard", html=True),
    name="dashboard"
)


# Input model
class LogRequest(BaseModel):
    message: str
    level: str = "INFO"


# Home API
@app.get("/")
def home():
    return {
        "message": "AI DevOps Monitoring System is running!",
        "status": "success"
    }


# Health Check API
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "AI DevOps Monitor"
    }


# Create application logs
@app.post("/logs")
def create_log(data: LogRequest):

    level = data.level.upper()

    if level not in ["INFO", "WARNING", "ERROR"]:
        return {
            "status": "failed",
            "message": "Invalid log level"
        }

    if level == "ERROR":
        logger.error(data.message)

    elif level == "WARNING":
        logger.warning(data.message)

    else:
        logger.info(data.message)

    return {
        "status": "success",
        "message": "Log saved successfully",
        "level": level
    }


# Read application logs
@app.get("/logs")
def get_logs():

    try:
        with open("logs/app.log", "r") as file:
            lines = file.readlines()

        return {
            "total_logs": len(lines),
            "logs": lines[-50:]
        }

    except FileNotFoundError:
        return {
            "total_logs": 0,
            "logs": []
        }


# AI Error Analysis API
@app.post("/analyze")
def analyze_log(data: LogRequest):

    if data.level.upper() != "ERROR":
        return {
            "status": "failed",
            "message": "AI analysis is available only for ERROR logs."
        }

    analysis = analyze_error(data.message)

    if analysis.startswith("AI Analysis failed"):
        return {
            "status": "ai_unavailable",
            "error": data.message,
            "ai_analysis": analysis
        }

    return {
        "status": "success",
        "error": data.message,
        "ai_analysis": analysis
    }
