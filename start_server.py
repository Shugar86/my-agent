import subprocess, time, requests, os, sys

api_key = os.environ.get("OPENROUTER_API_KEY")
if not api_key:
    print("ERROR: OPENROUTER_API_KEY not set. Set it in .env or environment.")
    sys.exit(1)

print("Starting server...")
proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "web.server:app", "--host", "127.0.0.1", "--port", "8000"],
    cwd=os.path.dirname(os.path.abspath(__file__)),
)

time.sleep(4)

print("Testing server...")
try:
    r = requests.get("http://127.0.0.1:8000/api/agents")
    print(f"GET /api/agents: {r.status_code}")

    r = requests.post("http://127.0.0.1:8000/api/chat",
                      json={"message": "test", "agent_id": "researcher"})
    print(f"POST /api/chat: {r.status_code}")
    if r.status_code == 200:
        print(f"Response: {r.json().get('response', '')[:100]}")
        print("SUCCESS! Server is working!")
        print("Open: http://127.0.0.1:8000/chat")
    else:
        print(f"Error: {r.text[:200]}")
except Exception as e:
    print(f"Error: {e}")

input("Press Enter to stop server...")
proc.terminate()
proc.wait()
print("Server stopped")
