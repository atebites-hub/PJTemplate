# RLM Hybrid REPL — Workflow Examples

Two end-to-end examples showing the exact sequence of `execute_code` calls the
agent makes when this skill is active. All calls go through the `MCP_DOCKER`
server. File content is always injected as Python strings from Cursor — the
container has no host filesystem access.

---

## Example 1: Dependency Graph Analysis

**Goal**: Find all circular import dependencies in a Python backend module.

### Step 1 — Gather files with Cursor native tools

The agent uses `@codebase` or semantic search to locate all Python files in
`source/server/` and reads their content:

```
@codebase show me the content of all Python files in source/server/
```

Cursor returns the file paths and their full string content.

### Step 2 — Bootstrap the REPL

```
Tool: execute_code
Arguments:
  code: <full contents of scripts/bootstrap.py>
  (no session_id — first call)
```

Response includes `session_id: 42` (example integer). Store this value.

Expected output:
```
Loaded 1 file(s). Total in codebase: 1
Bootstrap complete
Helpers ready: load_batch(), reset_repl(), get_status(), mark_as_loaded()
Status -> files_loaded: 0 | signature: None
```

### Step 3 — Dirty check

```
Tool: execute_code
Arguments:
  code: get_status()
  session_id: 42
```

Output: `signature: None` — no prior state, proceed to load.

### Step 4 — Inject files as strings

The agent passes the content Cursor returned in Step 1 directly as Python string
literals. No `open()` calls — the container cannot read from disk.

```
Tool: execute_code
Arguments:
  session_id: 42
  code: |
    load_batch({
        "source/server/app.py": "import utils\nimport models\n# ... rest of file ...",
        "source/server/utils.py": "import models\n# ... rest of file ...",
        "source/server/models.py": "import app\n# ... rest of file ...",
    })
    mark_as_loaded("PJTemplate:main")
```

### Step 5 — Analyze: extract imports

```
Tool: execute_code
Arguments:
  session_id: 42
  code: |
    import re

    def extract_imports(content):
        return re.findall(r"^(?:import|from)\s+([\w.]+)", content, re.MULTILINE)

    graph = {
        path.split("/")[-1].replace(".py", ""): extract_imports(content)
        for path, content in codebase.items()
    }
    print(graph)
```

Output:
```python
{'app': ['utils', 'models'], 'utils': ['models'], 'models': ['app']}
```

### Step 6 — Analyze: detect cycles

```
Tool: execute_code
Arguments:
  session_id: 42
  code: |
    def find_cycles(graph):
        visited, path, cycles = set(), [], []

        def dfs(node):
            if node in path:
                cycles.append(list(path[path.index(node):]) + [node])
                return
            if node in visited:
                return
            visited.add(node)
            path.append(node)
            for neighbor in graph.get(node, []):
                if neighbor in graph:
                    dfs(neighbor)
            path.pop()

        for node in graph:
            dfs(node)
        return cycles

    print(find_cycles(graph))
```

Output:
```
[['app', 'models', 'app']]
```

Agent reports: circular dependency between `app.py` and `models.py` via
`models → app`. All state (`graph`, `extract_imports`, `find_cycles`) persists
in the session for follow-up questions.

---

## Example 2: Recursive Refactoring Plan for a Large File

**Goal**: A 1,200-line file `source/server/api/routes.py` needs to be split into
focused modules. Produce a concrete refactoring plan.

### Step 1 — Gather the file

```
@file source/server/api/routes.py
```

Cursor returns the full file content as a string.

### Step 2 — Bootstrap (if not already done this session)

Same as Example 1 Step 2. If already bootstrapped, skip — just use the existing
`session_id`.

### Step 3 — Inject the file

```
Tool: execute_code
Arguments:
  session_id: 42
  code: |
    load_batch({
        "source/server/api/routes.py": """<full file content from Cursor>"""
    })
```

### Step 4 — Measure and slice

```
Tool: execute_code
Arguments:
  session_id: 42
  code: |
    content = codebase["source/server/api/routes.py"]
    lines = content.splitlines()
    print("Total lines: {}".format(len(lines)))
```

Output: `Total lines: 1200`

### Step 5 — Find all definitions

```
Tool: execute_code
Arguments:
  session_id: 42
  code: |
    import re

    definitions = [
        (i + 1, line.strip())
        for i, line in enumerate(lines)
        if re.match(r"^(def |class |async def )", line)
    ]
    for lineno, defn in definitions:
        print("  L{}: {}".format(lineno, defn))
```

Output (example):
```
  L12: def health_check():
  L45: def get_users():
  L89: class AuthRoutes:
  L312: def login():
  L398: def logout():
  L450: class ProductRoutes:
```

### Step 6 — Group by domain and produce the plan

```
Tool: execute_code
Arguments:
  session_id: 42
  code: |
    groups = {
        "auth": [d for d in definitions if any(k in d[1].lower() for k in ("auth", "login", "logout"))],
        "users": [d for d in definitions if "user" in d[1].lower()],
        "products": [d for d in definitions if "product" in d[1].lower()],
        "health": [d for d in definitions if "health" in d[1].lower()],
    }

    for group, defs in groups.items():
        if defs:
            print("Extract {} ({} definitions, L{}–L{}) -> source/server/api/{}.py".format(
                group, len(defs), defs[0][0], defs[-1][0], group
            ))
```

Output:
```
Extract auth (3 definitions, L89–L398) -> source/server/api/auth.py
Extract users (1 definitions, L45–L88) -> source/server/api/users.py
Extract products (1 definitions, L450–L1150) -> source/server/api/products.py
Extract health (1 definitions, L12–L44) -> source/server/api/health.py
```

Agent delivers this as the refactoring recommendation with exact line ranges and
target file names — all derived programmatically from the injected content.
The `definitions`, `groups`, and `lines` variables remain in the session for any
follow-up analysis without re-injecting the file.
