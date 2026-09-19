import requests
import time
import subprocess
import os

os.environ["KIDNEY_AI_DATA_ROOT"] = "datasets"

print("Starting server...")
proc = subprocess.Popen([".\\.venv-ai\\Scripts\\python.exe", "-m", "uvicorn", "api.main:app", "--app-dir", ".\\ai-engine", "--host", "127.0.0.1", "--port", "8000"])
time.sleep(10)

try:
    resp = requests.get("http://127.0.0.1:8000/health")
    print("Health response:", resp.json())
except Exception as e:
    print("Health check failed!", e)
finally:
    proc.terminate()
