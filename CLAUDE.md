# CLAUDE.md

This file gives Claude Code the full context and plan for this project. Follow it in order — don't skip steps even if they seem obvious, each one maps to a specific resume claim that needs to be literally true, not aspirational.

Nothing has been built yet. Start from Step 1.

## Project

**NL-to-SQL Agent** — a conversational agent that takes plain-English questions (e.g. "what were total sales in March?") and turns them into validated SQL queries against a real SQLite database, returning grounded answers instead of hallucinated numbers.

**Resume claim this project must fully satisfy:**
> Python, LangChain, LangSmith, SQLite, FastAPI, Docker, GCP
> - Built a LangChain SQL agent using `SQLDatabaseToolkit` and `create_sql_agent`, translating natural language into validated SQL queries with grounded execution against a structured orders database.
> - Instrumented all agent runs with LangSmith tracing for step-by-step visibility into tool calls, prompt inputs, and query latency.
> - Exposed the agent via a FastAPI `/query` endpoint with Pydantic schemas and error handling for malformed or out-of-scope requests.
> - Containerized the service with Docker and deployed to GCP Cloud Run, configuring environment variables and health checks for public HTTPS access.

## Constraints & scope

- **Language:** Python only, type hints throughout.
- **Read-only agent:** v1 must only run `SELECT` statements. No INSERT/UPDATE/DELETE. Enforce this at the toolkit level.
- **No multi-turn memory** in v1 — each question is independent.
- **Out-of-scope questions** (e.g. "what's the weather today?") must be handled gracefully — the agent should say it can't answer, not hallucinate or crash.
- **LLM provider:** pick Groq (`langchain-groq`, `llama-3.3-70b-versatile`) or Gemini (`langchain-google-genai`) and stick with it — `temperature=0` for deterministic SQL generation.

## Tech stack

| Layer | Tool |
|---|---|
| Language | Python 3.11 |
| Agent framework | `langchain`, `langchain-community` |
| LLM | Groq or Gemini (pick one, see Step 7) |
| Observability | LangSmith |
| Database | SQLite |
| API layer | FastAPI + Pydantic |
| Containerization | Docker |
| Cloud | GCP Cloud Run |

## Project structure

```
sql-agent/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app
│   ├── agent.py           # LangChain SQL agent
│   └── db_setup.py        # Creates + seeds SQLite DB
├── data/
│   └── orders.db
├── schema_design.md
├── ground_truth.md         # Manual SQL results used to validate agent answers
├── requirements.txt
├── Dockerfile
├── .env                    # not committed
└── README.md
```

## Build order

- [x] 1. Understand the problem — define input/output/constraints (write to README later)
- [x] 2. Design architecture — diagram: FastAPI → LangChain agent → SQLite → LangSmith
- [x] 3. Design schema → `schema_design.md`
- [x] 4. Build DB → `app/db_setup.py`, run it locally, verify `data/orders.db` exists
- [x] 5. Test SQL manually via `sqlite3` CLI — record expected outputs as ground truth
- [x] 6. Connect LangChain to the DB — sanity-check `db.run()`
- [x] 7. Connect the LLM (Groq, `llama-3.3-70b-versatile`, `temperature=0`)
- [x] 8. Build the SQL agent with `SQLDatabaseToolkit` + `create_sql_agent`
- [x] 9. Wrap in FastAPI `/query` endpoint
- [x] 10. Add Pydantic validation + error handling
- [x] 11. Enable LangSmith tracing, verify traces in dashboard
- [x] 12. Dockerize, test locally
- [x] 13. Deploy to GCP Cloud Run with `/health` check — https://sql-agent-932926002490.asia-south1.run.app
- [x] 14. Document (README) + final test pass against deployed URL (LangSmith screenshot for README still pending)

## Step details

### 1. Understand the problem
Write down (later, in your README):
- **Input:** a natural language question about order/sales data.
- **Output:** a grounded answer derived from actual SQL execution — not the LLM guessing a number.
- **Constraints:** the agent must refuse or gracefully handle questions that can't be answered from the schema.
- **Non-goals for v1:** multi-turn memory, write operations.

### 2. Design the architecture
```
User question (HTTP POST)
        ↓
FastAPI /query endpoint (Pydantic validates input)
        ↓
LangChain SQL Agent
    ├── Toolkit: list tables, get schema, query DB, check query
    ├── LLM: reasons about which SQL to generate
    └── LangSmith: traces every step above
        ↓
SQLite database (orders.db)
        ↓
Agent formats result → returned as JSON
```

### 3. Design the schema (`schema_design.md`)
```
Table: orders
├── id            INTEGER PRIMARY KEY
├── customer_name TEXT NOT NULL
├── product       TEXT NOT NULL
├── quantity      INTEGER NOT NULL
├── price         REAL NOT NULL
├── order_date    TEXT NOT NULL   (ISO format: YYYY-MM-DD)
└── region        TEXT NOT NULL   (North / South / East / West)
```
Check it supports: total revenue by region, orders in a given month, what a specific customer ordered. Add columns now if a planned demo question isn't answerable.

### 4. Build the database (`app/db_setup.py`)
```python
import sqlite3

DB_PATH = "data/orders.db"

def create_db(path: str = DB_PATH) -> None:
    conn = sqlite3.connect(path)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            customer_name TEXT NOT NULL,
            product TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            order_date TEXT NOT NULL,
            region TEXT NOT NULL
        )
    """)

    sample_rows = [
        (1, "Ravi Kumar", "Laptop", 1, 55000.0, "2026-01-15", "North"),
        (2, "Ayesha Khan", "Mouse", 3, 500.0, "2026-01-20", "South"),
        (3, "Rahul Verma", "Monitor", 2, 8000.0, "2026-02-05", "West"),
        (4, "Sneha Iyer", "Laptop", 1, 55000.0, "2026-03-10", "South"),
        (5, "Aman Gupta", "Keyboard", 5, 700.0, "2026-03-18", "North"),
        (6, "Priya Nair", "Monitor", 1, 8000.0, "2026-03-22", "East"),
        (7, "Vikram Singh", "Laptop", 2, 55000.0, "2026-04-02", "North"),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO orders VALUES (?,?,?,?,?,?,?)", sample_rows
    )
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_db()
    print(f"Database created at {DB_PATH}")
```
Run locally:
```bash
mkdir -p data
python app/db_setup.py
```
Verify `data/orders.db` actually exists on disk before moving on.

### 5. Test SQL manually
```bash
sqlite3 data/orders.db
```
```sql
SELECT region, SUM(quantity * price) AS revenue FROM orders GROUP BY region;
SELECT * FROM orders WHERE order_date LIKE '2026-03%';
SELECT product, quantity FROM orders WHERE customer_name = 'Ravi Kumar';
```
Record the actual output of each query in `ground_truth.md` — this is what you'll check the agent's answers against later. Don't skip this; it's the proof behind "grounded execution."

### 6. Connect LangChain
```bash
pip install langchain langchain-community python-dotenv
```
```python
from langchain_community.utilities import SQLDatabase

db = SQLDatabase.from_uri("sqlite:///data/orders.db")
print(db.get_usable_table_names())   # should print ['orders']
print(db.run("SELECT COUNT(*) FROM orders"))  # should match row count
```
Run as a standalone script. If `db.run()` doesn't return the right count, stop here — don't build the agent on a broken connection.

### 7. Connect the LLM
Groq:
```bash
pip install langchain-groq
```
```python
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0, api_key=os.getenv("GROQ_API_KEY"))
print(llm.invoke("Say hello in one word.").content)
```
Or Gemini:
```bash
pip install langchain-google-genai
```
```python
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0, google_api_key=os.getenv("GOOGLE_API_KEY"))
```
`.env`:
```
GROQ_API_KEY=your_key_here
# or
GOOGLE_API_KEY=your_key_here
```

### 8. Build the SQL agent (`app/agent.py`)
```python
import os
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit, create_sql_agent
from langchain_groq import ChatGroq

load_dotenv()

def build_agent():
    db = SQLDatabase.from_uri("sqlite:///data/orders.db")

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        api_key=os.getenv("GROQ_API_KEY"),
    )

    toolkit = SQLDatabaseToolkit(db=db, llm=llm)

    agent = create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        verbose=True,
        agent_type="tool-calling",
    )
    return agent

def ask(question: str) -> str:
    agent = build_agent()
    result = agent.invoke({"input": question})
    return result["output"]
```
Add a system prompt constraint (via the agent's prefix) so it only answers from the `orders` table and refuses otherwise. Enforce read-only (SELECT-only) execution at the toolkit level.

Quick manual test:
```python
# test.py
from app.agent import ask
print(ask("What is the total revenue from the North region?"))
```

### 9. Expose with FastAPI (`app/main.py`)
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.agent import ask

app = FastAPI(title="NL-to-SQL Agent")

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    question: str
    answer: str

@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    try:
        answer = ask(request.question)
        return QueryResponse(question=request.question, answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok"}
```
Run:
```bash
uvicorn app.main:app --reload --port 8000
```
Test:
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What products did Ravi Kumar order?"}'
```

### 10. Add validation and error handling
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from app.agent import ask

app = FastAPI(title="NL-to-SQL Agent")

class QueryRequest(BaseModel):
    question: str

    @field_validator("question")
    @classmethod
    def question_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Question cannot be empty")
        if len(v) > 500:
            raise ValueError("Question too long (max 500 characters)")
        return v.strip()

class QueryResponse(BaseModel):
    question: str
    answer: str

@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    try:
        answer = ask(request.question)
        return QueryResponse(question=request.question, answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent failed to process query: {str(e)}")

@app.get("/health")
def health():
    return {"status": "ok"}
```
Test the failure paths, not just the happy path:
```bash
curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"question": ""}'
curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"question": "What is the capital of France?"}'
```
If the out-of-scope case hallucinates, add a system prompt constraint telling the agent to only answer from the `orders` table and refuse otherwise.

### 11. Enable LangSmith
```bash
pip install langsmith
```
`.env` (add these):
```
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=sql-agent
```
No code changes needed. Verify traces appear at smith.langchain.com under project `sql-agent`, with individual tool calls (list tables → get schema → generate SQL → execute → format answer) visible as separate steps. Screenshot for README.

### 12. Dockerize
`requirements.txt`:
```
langchain
langchain-community
langchain-groq
fastapi
uvicorn[standard]
pydantic
python-dotenv
langsmith
```
`Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY data/ ./data/

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```
Build and test locally before touching any cloud platform:
```bash
docker build -t sql-agent .
docker run -p 8080:8080 --env-file .env sql-agent
```
```bash
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Total revenue by region?"}'
```
If it doesn't work locally in Docker, it won't work in the cloud either — debug here first.

### 13. Deploy to GCP Cloud Run
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/sql-agent

gcloud run deploy sql-agent \
  --image gcr.io/YOUR_PROJECT_ID/sql-agent \
  --platform managed \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars GROQ_API_KEY=your_key,LANGCHAIN_TRACING_V2=true,LANGCHAIN_API_KEY=your_key,LANGCHAIN_PROJECT=sql-agent
```
Point the liveness probe / health check at `/health` in the Cloud Run console, then verify:
```bash
curl https://YOUR-SERVICE-URL.run.app/health
```
Test the live endpoint exactly as you did locally.

### 14. Document and final test pass
Write `README.md`: what it does, architecture diagram, tech stack, live demo URL, local setup, example queries with real answers, LangSmith screenshot.

Re-run every `ground_truth.md` question against the **deployed** URL:
```python
import requests

url = "https://YOUR-SERVICE-URL.run.app/query"
questions = [
    "What is the total revenue from the North region?",
    "What products did Ravi Kumar order?",
    "How many orders were placed in March 2026?",
]

for q in questions:
    resp = requests.post(url, json={"question": q})
    print(f"Q: {q}\nA: {resp.json()['answer']}\n")
```
If every answer matches `ground_truth.md`, LangSmith shows traces for all of them, and the container is live on Cloud Run — every resume line is now literally true.

## Final checklist (cross-check against resume claims)

- [x] `SQLDatabaseToolkit` and `create_sql_agent` both actually used
- [x] Agent answers verified against `ground_truth.md`, not just "looks right"
- [x] LangSmith shows real traces with tool calls, prompts, latency visible
- [x] FastAPI `/query` uses Pydantic schemas
- [x] Error handling covers empty input, oversized input, agent failures
- [x] Docker container runs and responds correctly locally before deploying
- [x] Deployed and reachable on GCP Cloud Run with working `/health`
- [x] README documents architecture, setup, includes live demo link

## Conventions

- Python only, type hints throughout, Pydantic models for request/response schemas.
- Read-only DB access enforced at the toolkit level — a real safety detail, not just a nice-to-have.
- Re-check every SQL-generating change against `ground_truth.md` before moving to the next step.
- Run everything locally in this repo — nothing should depend on a sandbox or external state.
