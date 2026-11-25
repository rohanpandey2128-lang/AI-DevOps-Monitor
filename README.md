# AI-Powered DevOps Monitoring & Incident Management System

An AI-assisted DevOps monitoring and incident management project built using Python and FastAPI. It collects application logs, monitors errors and warnings, and provides troubleshooting analysis with a local fallback.

## Features

- FastAPI-based REST API
- Application log generation
- View and retrieve recent logs
- Error, warning and info log categorization
- AI-assisted incident analysis using Gemini
- Local troubleshooting fallback when Gemini is unavailable
- Web-based monitoring dashboard
- Automatic dashboard refresh

## Technologies Used

- Python
- FastAPI
- Uvicorn
- Google Gemini API
- HTML, CSS and JavaScript
- Git and GitHub

## Project Structure

```text
AI-DevOps-Monitor/
│
├── app/
│   ├── main.py
│   └── ai_analyzer.py
│
├── dashboard/
│   └── index.html
│
├── logs/
├── .gitignore
└── README.md
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/rohanpandey2128-lang/AI-DevOps-Monitor.git
cd AI-DevOps-Monitor
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the environment (Windows PowerShell)

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install fastapi uvicorn google-genai
```

### 5. Configure Gemini API

Set your Gemini API key as an environment variable in PowerShell:

```powershell
$env:GEMINI_API_KEY = "YOUR_API_KEY"
```

Never upload your API key to GitHub.

### 6. Run the application

```bash
python -m uvicorn app.main:app --reload
```

## Access the Application

- Dashboard: http://127.0.0.1:8000/dashboard/
- API Home: http://127.0.0.1:8000/
- Health Check: http://127.0.0.1:8000/health
- API Documentation: http://127.0.0.1:8000/docs

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | API home |
| GET | `/health` | Health check |
| POST | `/logs` | Generate application logs |
| GET | `/logs` | Retrieve recent logs |
| POST | `/analyze` | Analyze application errors |

## AI Analysis

The project uses Google Gemini for AI-assisted incident analysis. If the Gemini service is unavailable, a local troubleshooting mechanism provides possible causes, recommended actions and priority levels.

## Future Improvements

- Docker containerization
- Prometheus and Grafana integration
- Kubernetes deployment
- Automated alert notifications
- CI/CD pipeline integration
- Advanced incident classification

## Author

**Rohan Pandey**

GitHub: https://github.com/rohanpandey2128-lang

---

*This project is developed as a practical learning project in DevOps, cloud engineering and AI-assisted incident management.*