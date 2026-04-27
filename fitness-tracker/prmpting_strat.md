# Prompting Strategy for Building Apps with AI

## 1. What prompt likely generated this code

Based on the `design_philosophy.md` and project structure, it was probably something like:

> *"Build a fitness tracker web app. Backend: FastAPI + SQLite + SQLAlchemy. Frontend: plain HTML/CSS/JS. Support uploading ZIP/CSV/GPX files from Mi Fitness and Runkeeper. Separate concerns into models, routes, and parsers. Single user, personal use."*

The `design_philosophy.md` itself reads like it was either written as the prompt or written from the prompt — it defines the architecture contract that the code follows.

---

## 2. How to prompt better for apps

**The key insight: give the AI the same information a senior engineer would need before writing code.**

### Good app-building prompt structure:
```
1. WHAT: What the app does (1-2 sentences)
2. WHO: Who uses it, how many users, usage patterns
3. STACK: Languages, frameworks, DB (be specific)
4. ARCHITECTURE: How to split the code (models/routes/services)
5. DATA: What entities exist, their fields, relationships
6. FEATURES: Specific features, not vague goals
7. CONSTRAINTS: What to avoid (e.g., no auth needed, no Docker)
```

**Bad prompt:**
> *"Make a fitness tracker"*

**Good prompt:**
> *"Make a fitness tracker. Single user, personal use. FastAPI backend, SQLite DB via SQLAlchemy, plain HTML/JS frontend. Models: Activity (id, date, type, duration, calories, source). Routes: POST /upload (accept ZIP/CSV/GPX), GET /activities (list with filters), GET /stats (aggregated). No auth needed."*

---

## 3. Should you split backend and frontend prompts?

**Yes, almost always.** Here's why and when:

| Scenario | Split? |
|---|---|
| App > ~5 routes or 3+ pages | Yes |
| Different tech stacks | Yes (always) |
| You want to iterate on each independently | Yes |
| Tiny app, 1 page, 2 routes | No |

**Workflow that works well:**
1. **Prompt 1 — Architecture**: *"Design the data models, API routes, and file structure. Don't write code yet."* → Review and correct the design
2. **Prompt 2 — Backend**: Full backend with models, routes, DB
3. **Prompt 3 — Frontend**: *"Build the frontend that consumes these APIs: [paste route list]"*

Splitting keeps each prompt focused and the output higher quality.

---

## 4. How APIs and routes work (the mental model)

Think of your **backend as a post office**:

```
Client (browser/app)
    │
    │  HTTP Request: GET /activities?type=run
    ▼
Router  ← "Which function handles this address?"
    │
    ▼
Route Handler (function)
    ├── Validate inputs
    ├── Query the DB (via Model)
    ├── Transform data (via Parser/Service)
    └── Return JSON response
    │
    ▼
Client receives JSON → renders it
```

**Route** = a URL + HTTP method + handler function
**Model** = defines what goes in/out of the database
**API** = the set of all routes your backend exposes

In FastAPI specifically:
```python
@app.get("/activities")          # Route definition
def get_activities(type: str):   # Handler function
    return db.query(Activity)    # Model query → returns JSON
```

---

## 5. Should backend prompts include model/route details?

**Yes — this is the highest-leverage thing you can do.**

The more specific you are about your data shape, the better the output:

**Vague:**
> *"Create an activities API"*

**Specific (much better):**
> *"Create these FastAPI routes:*
> - `POST /upload` — accepts multipart file, detects format (ZIP/CSV/GPX), returns `{status, count}`
> - `GET /activities` — query params: `type`, `date_from`, `date_to`, `limit`. Returns list of Activity objects
> - `GET /stats` — returns `{total_distance, total_calories, activity_counts_by_type}`*
>
> *Activity model: id, date (ISO string), type (run/walk/cycle), duration_minutes, distance_km, calories, source_app*

---

## 6. How agentic architecture helps in coding

**Traditional AI coding:** You ask → AI responds → done. One shot.

**Agentic coding:** AI can take *sequences of actions* — read files, run tests, fix errors, search the web, call APIs — in a loop until a goal is achieved.

How it helps:
- **Self-correction**: AI writes code → runs tests → sees failure → fixes → re-runs
- **Codebase awareness**: AI reads your actual files before writing, so it matches your patterns
- **Multi-step tasks**: "Refactor all routes to use async" — reads every file, edits each one, verifies
- **Tool use**: AI can query your DB, fetch docs, run linters as part of coding

This is what Claude Code does — it's not just chat, it reads your files, runs commands, and iterates.

---

## 7. How to create agentic apps

**Agentic app = AI model + tools + a loop**

The simplest pattern:

```python
while not goal_achieved:
    action = llm.decide(history, available_tools)
    result = execute_tool(action)
    history.append(result)
```

**Core components you need:**

| Component | What it is | Example |
|---|---|---|
| **LLM** | The brain | Claude, GPT-4 |
| **Tools** | Things it can do | search_web(), query_db(), run_code() |
| **Memory** | What it knows | conversation history, vector store |
| **Loop** | Runs until done | while not complete |

**To build one with Claude:**
- Use the **Anthropic SDK** with tool use
- Define tools as JSON schemas
- Feed tool results back into the conversation
- The model decides when it has enough info to stop

**Simple example use cases to start with:**
1. A coding assistant that can read files + run tests
2. A research agent that can search + summarize
3. A data agent that can query your SQLite DB + generate charts

---

## TL;DR on prompting

- Be specific about stack, models, routes, and constraints upfront
- Split architecture → backend → frontend into separate prompts
- Paste your actual data shapes and route signatures — don't let the AI guess them
- The `design_philosophy.md` pattern in this project is a great template: write the design doc first, then use it as your prompt
