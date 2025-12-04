# Python Code Execution Server

HTTP API for executing Python code with resource limits, persistent sessions, and sandboxing.

**GitHub Repository:** https://github.com/YoussefAhmed99/Namaa-Backend-Challenge

---

## Setup Instructions

### Prerequisites

**Install Python 3.12+**

- **Windows:** Download from [python.org](https://www.python.org/downloads/)
- **Linux/WSL:** `sudo apt update && sudo apt install python3.12 python3.12-venv`

**Verify Installation:**
```bash
python --version  # or python3 --version
```

---

### Installation from Email Attachment

**Extract the zip file**, then:

#### Windows

```powershell
cd "Namaa Backend Challenge"

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# If requirements.txt is corrupt, manually install:
pip install fastapi uvicorn pydantic psutil pytest requests
```

#### Linux (WSL)

```bash
cd "Namaa Backend Challenge"

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# If requirements.txt is corrupt, manually install:
pip install fastapi uvicorn pydantic psutil pytest requests
```

---

### Installation from GitHub

#### Windows

```powershell
# Clone repository
git clone https://github.com/YoussefAhmed99/Namaa-Backend-Challenge.git
cd Namaa-Backend-Challenge

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

#### Linux (WSL)

```bash
# Clone repository
git clone https://github.com/YoussefAhmed99/Namaa-Backend-Challenge.git
cd Namaa-Backend-Challenge

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Running the Server

```bash
python run.py
```

Server runs on `http://localhost:8000`

---

## Running Tests

```bash
# All tests (34 total)
pytest tests -v

# Specific phase
pytest tests/test_a_phase_one.py -v
```

All 34 tests complete in ~10 seconds.

---

## Configuration

Default settings (hardcoded in `app/services/`):

| Setting | Value |
|---------|-------|
| Timeout | 2 seconds |
| Memory Limit | 100 MB |
| Max Sessions | 40 |
| Idle Timeout | 60 seconds |

**To modify:** Edit constants in `SessionManager` and `SessionProcess` classes.

---

## Implementation vs Specification

### Level 1: Basic Code Execution ✅

**Implemented:**
- POST `/execute` endpoint
- JSON request/response with `code`, `stdout`, `stderr`, `error`
- Mutual exclusivity: `error` XOR `stdout/stderr`

**Tech Stack:**
- FastAPI for HTTP server
- Pydantic for request/response validation

---

### Level 2: Resource Limits ✅

**Implemented:**
- 2 second timeout
- 100 MB memory limit

**Approach (Both Platforms):**
- `psutil.Process().memory_info().rss` monitors physical RAM
- External thread polls every 100ms
- Kills process when RSS exceeds limit

**Why This Approach:**
- RSS measures actual physical RAM usage consistently
- Works identically on Windows and Linux
- Simple, no kernel-level complexities

**Why NOT Linux Kernel Limits:**
- `RLIMIT_AS` measures virtual space (too strict - includes Python overhead ~50-70 MB)
- `RLIMIT_DATA` causes slow retries instead of immediate termination
- `RLIMIT_RSS` is deprecated and ignored by modern kernels

---

### Level 3: Persistent Sessions ✅

**Implemented:**
- Server-generated session IDs (UUID)
- State persistence using `InteractiveInterpreter`
- Automatic cleanup after 60 seconds idle
- Max 40 concurrent sessions

**Architecture:**
- `SessionManager` - Singleton orchestrating all sessions
- `SessionProcess` - Wraps worker process + queues
- `worker_function` - Runs persistent interpreter in isolated process

**Why Multiprocessing:**
- True isolation between sessions
- Clean termination on timeout/memory exceeded
- Cross-platform (Windows + Linux)

**Why NOT Client-Provided IDs:**
- Security: Prevents session hijacking
- Simplicity: Server controls ID generation

---

### Level 4: Sandboxing ✅

**Implemented:**
- Filesystem blocking (with `/proc/` exception for psutil)
- Network blocking

**Method: Monkey-Patching**
- Replaces `open()`, `os.remove()`, `socket.socket()`, etc. with stubs
- Raises `PermissionError` when called
- Applied before user code execution

**Why Monkey-Patching:**
- No external dependencies (Docker, VMs)
- Works on both Windows and Linux
- No root/admin privileges required
- Sufficient for challenge scope

**Why NOT OS-Level Sandboxing:**
- Requires root access (seccomp, AppArmor)
- Platform-specific (Linux-only)
- Overkill for this use case

**Why NOT Containers:**
- Adds complexity and dependencies
- Not required by specification
- Would need Docker installation

---

## Limitations

### Resource Constraints

1. **2 second timeout:** Long-running computations will be killed
2. **100 MB memory limit:** Memory-intensive operations will fail
3. **40 session maximum:** New sessions rejected when limit reached
4. **100ms polling interval:** Brief memory spikes (<100ms) may not be detected
5. **60-second cleanup granularity:** Idle sessions removed in batches every 60s

### Security

- **Sandbox not production-grade:** Monkey-patching can be bypassed by determined attackers
- **Not safe for untrusted production use:** Suitable for controlled environments only

---

## Recommended Environment Variables (.env)

While the application uses hardcoded defaults, you can structure a `.env` file for future configurability:

```env
# Server Configuration
HOST=0.0.0.0
PORT=8000

# Execution Limits
TIMEOUT_SECONDS=2
MEMORY_LIMIT_MB=100

# Session Management
MAX_SESSIONS=40
IDLE_TIMEOUT_SECONDS=60
```

**Note:** Current implementation does not read from `.env`. This is provided as a suggestion for production deployment.

---

## API Reference

### POST /execute

**Request:**
```json
{
  "code": "print('Hello')",
  "id": "optional-session-uuid"
}
```

**Response:**
```json
{
  "id": "uuid",
  "stdout": "Hello\n",
  "stderr": null,
  "error": null
}
```

**Error Types:**
- `"execution timeout"` (2 seconds exceeded)
- `"memory limit exceeded"` (100 MB exceeded)
- `"max sessions reached"` (40 sessions active)
- `"session not found"` (invalid ID)

---

## Test Suite (34 Tests)

### Phase 1: Basic Execution (5 tests)

| Test | Description | Expected Output |
|------|-------------|-----------------|
| `test_stdout` | Execute print statement | `{"stdout": "Hello\n"}` |
| `test_stderr` | Execute division by zero | `{"stderr": "...ZeroDivisionError..."}` |
| `test_no_output` | Execute assignment only | `{"stdout": null, "stderr": null, "error": null}` |
| `test_syntax_error` | Execute code with syntax error | `{"stderr": "...SyntaxError..."}` |
| `test_empty_code_rejected` | Submit empty code string | HTTP 422 validation error |

### Phase 2: Resource Limits (5 tests)

| Test | Description | Expected Output |
|------|-------------|-----------------|
| `test_timeout` | Execute infinite loop | `{"error": "execution timeout"}` (~2s) |
| `test_memory_limit` | Allocate 150 MB bytearray | `{"error": "memory limit exceeded"}` |
| `test_normal_with_limits` | Execute simple print | `{"stdout": "ok\n"}` |
| `test_sleep_within_limit` | Sleep for 1 second | `{"stdout": "done\n"}` |
| `test_small_memory_allocation` | Allocate 10 MB bytearray | `{"stdout": "ok\n"}` |

### Phase 3: Persistent Sessions (14 tests)

| Test | Description | Expected Output |
|------|-------------|-----------------|
| `test_session_id_returned` | First execution without ID | `{"id": "uuid..."}` |
| `test_variable_persistence` | Set variable, then access it | Variable accessible across requests |
| `test_import_persistence` | Import module, then use it | Module remains imported |
| `test_function_persistence` | Define function, then call it | Function callable in next request |
| `test_session_not_found` | Use non-existent session ID | `{"error": "session not found"}` |
| `test_session_isolation` | Two sessions, same variable name | Independent namespaces |
| `test_session_cannot_access_other_session_variables` | Access another session's variable | `{"stderr": "...NameError..."}` |
| `test_crashed_session_isolated` | Crash one session, use another | Other sessions unaffected |
| `test_session_survives_errors` | Error in session, then reuse | Session usable after error |
| `test_multiple_executions_in_session` | Execute 5 operations sequentially | State accumulates correctly |
| `test_concurrent_sessions` | Run 5 sessions simultaneously | All sessions execute correctly |
| `test_session_with_timeout_still_returns_id` | Timeout in session | `{"error": "execution timeout", "id": "..."}` |
| `test_session_with_memory_limit_still_returns_id` | Memory limit in session | `{"error": "memory limit exceeded", "id": "..."}` |
| `test_class_persistence` | Define class, instantiate later | Class definition persists |

### Phase 4: Sandboxing (10 tests)

| Test | Description | Expected Output |
|------|-------------|-----------------|
| `test_os_remove_blocked` | Attempt `os.remove('file.txt')` | `{"stderr": "...PermissionError: [Errno 13]..."}` |
| `test_builtin_open_blocked` | Attempt `open('test.txt', 'w')` | `{"stderr": "...PermissionError: [Errno 13]..."}` |
| `test_os_mkdir_blocked` | Attempt `os.mkdir('newdir')` | `{"stderr": "...PermissionError: [Errno 13]..."}` |
| `test_socket_blocked` | Attempt `socket.socket()` | `{"stderr": "...PermissionError..."}` |
| `test_urllib_blocked` | Attempt `urllib.request.urlopen()` | `{"stderr": "...PermissionError..."}` |
| `test_os_getcwd_works` | Execute `os.getcwd()` | `{"stdout": "/path/to/dir"}` |
| `test_os_path_join_works` | Execute `os.path.join('a', 'b')` | `{"stdout": "a/b"}` |
| `test_math_works` | Import and use math module | `{"stdout": "4.0"}` |
| `test_computation_works` | Execute list comprehension | `{"stdout": "[0, 1, 4, 9, 16]"}` |
| `test_sandbox_persists_in_session` | Multiple requests in session | All requests remain sandboxed |

---

## Architecture

```
HTTP Request
    ↓
FastAPI (main.py + routes/execute.py)
    ↓
SessionManager (singleton)
    ├─ Manages session pool (max 40)
    ├─ Background cleanup thread (60s)
    └─ Routes to SessionProcess
        ↓
SessionProcess (per session)
    ├─ Communication queues (input/output)
    ├─ Memory monitoring thread (psutil)
    └─ Spawns Worker Process
        ↓
Worker Process (multiprocessing.Process)
    ├─ InteractiveInterpreter (persistent state)
    ├─ Sandbox applied (monkey-patching)
    ├─ stdout/stderr capture
    └─ Code execution (exec)
```

**Key Components:**
- **FastAPI Layer:** HTTP handling, request validation (Pydantic models)
- **SessionManager:** Orchestrates sessions, enforces 40 session limit, cleanup
- **SessionProcess:** Wraps worker, manages queues, monitors memory/timeout
- **Worker Process:** Isolated interpreter, sandboxed execution environment

---

## Notes

**Memory Testing:** Tests use `bytearray` with writes to force physical allocation:
```python
x = bytearray(150 * 1024 * 1024)
x[0] = 1  # Forces physical RAM usage
```

**Why:** Simple `bytes()` may use lazy allocation - memory reserved but not loaded until accessed.

---

## Usage

### Starting the Server

```bash
python run.py
```

Server starts on `http://localhost:8000`

### Interactive API Documentation

Open in browser: `http://localhost:8000/docs`

**To test the API:**
1. Click on `POST /execute` endpoint
2. Click "Try it out" button
3. Edit the request body with your code
4. Click "Execute" button
5. View response below

- Swagger UI for interactive testing
- View request/response schemas
- No additional tools needed

### Running Tests

```bash
# All tests
pytest tests -v

# Specific phase
pytest tests/test_a_phase_one.py -v

# With output
pytest tests -v -s
```
