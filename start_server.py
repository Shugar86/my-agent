import subprocess
import time
import requests
import os
import sys

kimi_key = os.environ.get("KIMI_API_KEY")
openrouter_key = os.environ.get("OPENROUTER_API_KEY")
if not kimi_key and not openrouter_key:
    print("Note: KIMI_API_KEY / OPENROUTER_API_KEY not set — chat will fail, but demo mock flow works.")

print("Starting server...")
proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "web.server:app", "--host", "127.0.0.1", "--port", "8020"],
    cwd=os.path.dirname(os.path.abspath(__file__)),
)

time.sleep(4)

print("Testing server...")
try:
    r = requests.get("http://127.0.0.1:8020/api/health", timeout=10)
    print(f"GET /api/health: {r.status_code}")

    r = requests.post(
        "http://127.0.0.1:8020/api/demo/public/run",
        json={"target": "Notion", "our_company": "Linear", "preset": "competitor"},
        timeout=30,
    )
    print(f"POST /api/demo/public/run: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"Demo mode: {data.get('mode')}, run_id: {data.get('run_id')}")
        print("SUCCESS! Server is working!")
        print("Open canonical demo: http://127.0.0.1:8020/showcase#playground")
    else:
        print(f"Error: {r.text[:200]}")
except requests.RequestException as exc:
    print(f"Error: {exc}")

input("Press Enter to stop server...")
proc.terminate()
proc.wait()
print("Server stopped")
