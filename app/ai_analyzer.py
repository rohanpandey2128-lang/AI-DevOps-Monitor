
import os
from google import genai


def local_analysis(error_message):
    """Fallback analysis when Gemini is unavailable."""

    error = error_message.lower()

    if "database" in error or "sql" in error:
        return """
LOCAL INCIDENT ANALYSIS

Issue: Database Connection Failure

Possible Causes:
1. Database server may be down.
2. Incorrect database credentials.
3. Database host or port may be incorrect.
4. Network connectivity problem.

Recommended Actions:
1. Check database server status.
2. Verify username and password.
3. Check database host and port.
4. Test database connectivity.
5. Review database server logs.

Priority: HIGH
Suggested Action: Investigate database connectivity.
"""

    elif "cpu" in error:
        return """
LOCAL INCIDENT ANALYSIS

Issue: High CPU Usage

Possible Causes:
1. Heavy application workload.
2. Infinite loop or inefficient process.
3. Too many running processes.

Recommended Actions:
1. Check CPU usage using Task Manager.
2. Identify high CPU processes.
3. Stop unnecessary processes.
4. Review application performance.

Priority: HIGH
Suggested Action: Investigate CPU-intensive processes.
"""

    elif "memory" in error or "ram" in error:
        return """
LOCAL INCIDENT ANALYSIS

Issue: High Memory Usage

Possible Causes:
1. Memory leak.
2. Too many running applications.
3. Insufficient available RAM.

Recommended Actions:
1. Check memory usage.
2. Identify memory-intensive processes.
3. Restart affected services if appropriate.
4. Investigate possible memory leaks.

Priority: MEDIUM
Suggested Action: Monitor memory consumption.
"""

    elif "timeout" in error:
        return """
LOCAL INCIDENT ANALYSIS

Issue: Request Timeout

Possible Causes:
1. Slow server response.
2. Network latency.
3. Backend service overload.

Recommended Actions:
1. Check network connectivity.
2. Review application response time.
3. Inspect backend service logs.
4. Check server resource usage.

Priority: HIGH
Suggested Action: Investigate service response delays.
"""

    elif "connection refused" in error:
        return """
LOCAL INCIDENT ANALYSIS

Issue: Connection Refused

Possible Causes:
1. Target service is not running.
2. Incorrect port configuration.
3. Firewall blocking the connection.

Recommended Actions:
1. Verify target service status.
2. Check configured port.
3. Review firewall rules.
4. Test network connectivity.

Priority: HIGH
Suggested Action: Verify service availability.
"""

    else:
        return f"""
LOCAL INCIDENT ANALYSIS

Issue: {error_message}

Possible Causes:
1. Application configuration issue.
2. Service dependency failure.
3. Unexpected application behaviour.

Recommended Actions:
1. Check application logs.
2. Verify service configuration.
3. Inspect related dependencies.
4. Investigate the error timestamp.

Priority: MEDIUM
Suggested Action: Perform manual investigation.
"""


def analyze_error(error_message):

    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key:
        return (
            "Gemini API key unavailable. "
            "Using local fallback analysis.\n"
            + local_analysis(error_message)
        )

    try:
        client = genai.Client(api_key=api_key)

        prompt = f"""
You are an experienced DevOps incident analyst.

Analyze this application error:

{error_message}

Provide:
1. Error explanation.
2. Possible root causes.
3. Troubleshooting steps.
4. Recommended solution.
5. Incident priority.

Use simple and practical language.
"""

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt
        )

        if response.text:
            return response.text

        raise ValueError("Empty AI response")

    except Exception as error:

        print("Gemini API unavailable:", str(error))

        return (
            "GEMINI AI TEMPORARILY UNAVAILABLE\n"
            "Using local troubleshooting analysis instead.\n"
            + local_analysis(error_message)
        )
