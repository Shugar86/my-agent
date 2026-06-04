# Troubleshooting Guide

> My Agent — Common Issues & Solutions  
> Version: **3.5.2** · Default port: **8020** (Docker / VDS)

---

## 1. Server Errors

### 1.1 "Internal Server Error" in Chat

**Symptoms:**
- Browser shows "Ошибка сервера: Internal Server Error"
- Console shows 500 status code

**Causes & Solutions:**

#### API Key Not Set
```bash
# Check if key is set
echo $OPENROUTER_API_KEY

# Set it
export OPENROUTER_API_KEY="sk-or-v1-..."

# Or add to config/agent.json
```

#### Server Not Restarted After Changes
```bash
# Kill old process
pkill -f uvicorn

# Start fresh
python -m uvicorn web.server:app --host 0.0.0.0 --port 8020
```

#### Port Already in Use
```bash
# Find process
netstat -ano | grep :8020

# Kill it
taskkill /F /PID <PID>

# Or use different port
python -m uvicorn web.server:app --port 8001
```

#### Postgres sessions schema mismatch or uninitialized pool (Docker / production)

**Symptoms:**
```
AttributeError: 'NoneType' object has no attribute 'acquire'
UndefinedColumnError: column "source" of relation "sessions" does not exist
```
Every chat request returns "Internal server error".

**Root cause (as of 3.5.2):**
- `DATABASE_URL` present → `MemoryManager` selects the PostgreSQL backend.
- `PGStateManager._pool` was never initialized (no startup hook called `connect()` for per-request `AgentBuilder` instances).
- The live database contained the ancient schema (`sessions.agent_id`, `sessions.messages` as blob) instead of the columns the current `PGStateManager` expects.

**Fix (already in the codebase):**
- Lazy `ensure_connected()` on every DB method.
- Automatic migration: on first connection the code detects the legacy schema, drops the old tables, and creates the modern structure.

Just pull latest code and restart:
```bash
docker compose up -d --force-recreate --no-build agent
```

If you are on an older image and need to force-clean the schema manually:
```bash
docker exec my-agent-db psql -U agent -d agent_db \
  -c "DROP TABLE IF EXISTS messages CASCADE; DROP TABLE IF EXISTS sessions CASCADE;"
docker compose restart agent
```

---

### 1.2 "ModuleNotFoundError"

**Symptoms:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
```bash
# Install dependencies
pip install -r requirements.txt

# Or specific package
pip install fastapi uvicorn
```

---

### 1.3 "UnicodeEncodeError"

**Symptoms:**
```
UnicodeEncodeError: 'charmap' codec can't encode character
```

**Solution (Windows):**
```bash
# Set encoding
set PYTHONIOENCODING=utf-8

# Or in Python
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
```

---

## 2. LLM Errors

### 2.1 "RateLimitError"

**Symptoms:**
```
RateLimitError: deepseek-v4-flash:free is temporarily rate-limited
```

**Solution:**
- Fallback to `deepseek-chat` is automatic
- Wait a few seconds and retry
- Consider adding paid OpenRouter key for higher limits

---

### 2.2 "AuthenticationError"

**Symptoms:**
```
AuthenticationError: Invalid API key
```

**Solution:**
```bash
# Verify key format (should start with sk-or-v1-)
echo $OPENROUTER_API_KEY

# Check in config
cat config/agent.json

# Regenerate at https://openrouter.ai/settings/keys
```

---

### 2.3 "Model Not Found"

**Symptoms:**
```
Model not found: openrouter/deepseek/...
```

**Solution:**
```bash
# Check available models
curl https://openrouter.ai/api/v1/models

# Update model ID in config
# Format: openrouter/<provider>/<model>
```

---

## 3. Frontend Issues

### 3.1 Blank Page

**Symptoms:** White screen, no content

**Solution:**
1. Check server is running
2. Open DevTools (F12) → Console
3. Look for JavaScript errors
4. Check network tab for 404 errors

---

### 3.2 "Unexpected token 'I', 'Internal S'... is not valid JSON"

**Symptoms:** Error in chat when sending message

**Cause:** Server returns HTML error page instead of JSON

**Solution:**
```bash
# Server is returning 500 error
# Check server logs for traceback
# Fix underlying error (usually API key or import error)
```

---

### 3.3 Styles Not Loading

**Symptoms:** Page looks unstyled

**Solution:**
```bash
# Check static files are served
ls web/static/

# Verify app.mount in server.py
```

---

## 4. Performance Issues

### 4.1 Slow Responses

**Causes:**
- LLM API latency (normal: 2–5s)
- Rate limiting on free OpenRouter models

**Solutions:**
- Use a paid OpenRouter key for higher limits
- Switch to a faster model in `config/agent.json`

---

### 4.2 High Memory Usage

**Cause:** Session files accumulate over time

**Solution:**
```bash
# Clear old sessions
rm memory/sessions/*.json

# Or implement TTL in MemoryManager
```

---

### 4.3 Server Hangs

**Cause:** Long-running LLM call or stuck workflow run.

**Solution:**
```bash
pkill -f uvicorn
python -m uvicorn web.server:app --host 0.0.0.0 --port 8020
```
---

## 5. Data Issues

### 5.1 Agents Not Showing

**Symptoms:** Dashboard shows 0 agents

**Solution:**
```bash
# Check registry file exists
cat agents/registry.json

# Verify JSON is valid
python -m json.tool agents/registry.json

# Check permissions
ls -la agents/
```

---

### 5.2 Skills Not Loading

**Symptoms:** "Warning: skill 'xxx' not found"

**Solution:**
```bash
# Check skill directory exists
ls skills/

# Verify skill.py and SKILL.md exist
ls skills/deep_research/

# Check for syntax errors in skill.py
python -m py_compile skills/*/skill.py
```

---

### 5.3 Output Files Not Created

**Symptoms:** No files in output/ directory

**Solution:**
```bash
# Create directory
mkdir -p output

# Check permissions
chmod 755 output

# Verify tool has write access
```

---

## 6. Docker Issues

### 6.1 "Cannot connect to Docker daemon"

**Solution:**
```bash
# Start Docker service
sudo systemctl start docker

# Or use Docker Desktop (Windows/Mac)
```

---

### 6.2 "Port already allocated"

**Solution:**
```bash
# Change port in docker-compose.yml
ports:
  - "8001:8000"

# Or stop existing container
docker-compose down
docker-compose up
```

---

### 6.3 Container Exits Immediately

**Solution:**
```bash
# Check logs
docker-compose logs

# Verify env vars
cat .env
```

---

## 7. Development Issues

### 7.1 Tests Failing

```bash
# Run with verbose output
pytest tests/ -v -s

# Run specific test
pytest tests/test_all.py::test_tool_registry -v

# Check Python version
python --version  # Should be 3.11+
```

---

### 7.2 Import Errors in IDE

**Solution:**
```bash
# Mark project root as sources root
# In PyCharm: Right-click folder → Mark as Sources Root

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

---

### 7.3 Hot Reload Not Working

**Solution:**
```bash
python -m uvicorn web.server:app --host 0.0.0.0 --port 8020 --reload
```
---

## 8. Windows-Specific Issues

### 8.1 "Microsoft Visual C++ required"

**Solution:**
```powershell
# Install Build Tools
# https://visualstudio.microsoft.com/visual-cpp-build-tools/

# Or use pre-built wheels
pip install --only-binary :all: <package>
```

---

### 8.2 Path Issues (Cyrillic characters)

**Solution:**
```bash
# Move project to ASCII path
# C:\Users\Username\Desktop\my-agent\  (OK)
# C:\Users\Имя\Desktop\my-agent\  (May cause issues)

# Or set code page
chcp 65001
```

---

### 8.3 PowerShell Execution Policy

**Solution:**
```powershell
# Check policy
Get-ExecutionPolicy

# Set for current user
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## Debug Mode

Enable detailed logging:

```python
# In core/logger.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or set environment variable:
```bash
export LOG_LEVEL=DEBUG
```

---

## Getting Help

1. Check logs: `docker-compose logs` or server console output
2. Run tests: `pytest tests/ -v`
3. Check GitHub issues (if public repo)
4. Review ARCHITECTURE.md for system design

---

## Quick Diagnostic Script

```bash
#!/bin/bash
echo "=== My Agent Diagnostics ==="
echo ""
echo "Python version:"
python --version
echo ""
echo "Installed packages:"
pip list | grep -E "fastapi|uvicorn|litellm|pydantic"
echo ""
echo "Config:"
cat config/agent.json | grep -v api_key
echo ""
echo "Agents:"
python -c "from core.agent_store import AgentStore; print(len(AgentStore().list_agents()), 'agents')"
echo ""
echo "Skills:"
ls skills/ | wc -l
echo "skill directories"
echo ""
echo "Tests:"
pytest tests/ --co -q 2>/dev/null | tail -1
echo ""
echo "Port 8020:"
netstat -ano 2>/dev/null | grep :8020 || echo "Not in use"
```

---

End of Troubleshooting Guide
