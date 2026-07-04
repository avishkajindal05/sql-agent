"""LangChain SQL agent: translates natural language into validated, read-only SQL."""

import os
import re
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv
from langchain_community.agent_toolkits import SQLDatabaseToolkit, create_sql_agent
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langchain_community.utilities import SQLDatabase
from langchain_core.tools import BaseTool
from langchain_groq import ChatGroq

load_dotenv()

# mode=ro opens SQLite read-only, so even a query that slipped past
# validation could not modify the database.
DB_URI = "sqlite:///file:data/orders.db?mode=ro&uri=true"

_FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|TRUNCATE"
    r"|ATTACH|DETACH|PRAGMA|VACUUM|REINDEX)\b",
    re.IGNORECASE,
)

SYSTEM_PREFIX = """You are an agent designed to answer questions about an orders database.
You have access to tools for interacting with a {dialect} database containing a single table: orders.

Given an input question, create a syntactically correct {dialect} SELECT query to run,
then look at the results and return the answer. Unless the user specifies a specific
number of examples, limit your query to at most {top_k} results.

Rules you must follow:
- Only run SELECT statements. Never run INSERT, UPDATE, DELETE, DROP or any other
  statement that modifies the database. Such statements will be rejected.
- Only answer questions that can be answered from the orders table. If a question
  is unrelated to the orders data (e.g. general knowledge, weather, opinions),
  do not guess: reply that you can only answer questions about the orders database.
- Base every number in your answer on actual query results, never on estimation.
- Your final answer must repeat the executed query's result values EXACTLY as returned.
  For example, if the query result is [(3,)], the answer must contain the number 3 —
  never substitute a different number.
- The database contains dates in the year 2026. These are valid, real records that
  have already happened. Never assume a date is "in the future" or that no data can
  exist for it — trust only what the query returns.
- Double-check your query before executing it."""


def _is_read_only(query: str) -> bool:
    stripped = query.strip().rstrip(";").strip()
    if not stripped or _FORBIDDEN.search(stripped):
        return False
    return stripped.split(None, 1)[0].upper() in ("SELECT", "WITH")


class ReadOnlyQuerySQLTool(QuerySQLDatabaseTool):
    """Query tool that rejects anything other than SELECT statements."""

    def _run(self, query: str, **kwargs: Any) -> Any:
        if not _is_read_only(query):
            return (
                "Error: only read-only SELECT statements are allowed. "
                "Rewrite the query as a SELECT."
            )
        result = super()._run(query, **kwargs)
        if isinstance(result, str) and result.startswith("Error"):
            return result
        # The instruction is attached to the result itself because the model's
        # training prior (e.g. "2026 is the future, so there can be no orders")
        # sometimes overrides a correct result it only saw earlier in the trace.
        return (
            f"Query executed successfully. Authoritative result: {result}\n"
            "Copy these exact values into your final answer."
        )


class ReadOnlySQLDatabaseToolkit(SQLDatabaseToolkit):
    """SQLDatabaseToolkit whose query-execution tool is SELECT-only."""

    def get_tools(self) -> list[BaseTool]:
        return [
            ReadOnlyQuerySQLTool(db=self.db, description=tool.description)
            if isinstance(tool, QuerySQLDatabaseTool)
            else tool
            for tool in super().get_tools()
        ]


@lru_cache(maxsize=1)
def build_agent() -> Any:
    """Build the SQL agent once; reused across requests."""
    db = SQLDatabase.from_uri(DB_URI)

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        api_key=os.getenv("GROQ_API_KEY"),
    )

    toolkit = ReadOnlySQLDatabaseToolkit(db=db, llm=llm)

    return create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        agent_type="tool-calling",
        prefix=SYSTEM_PREFIX,
        verbose=True,
    )


def ask(question: str) -> str:
    agent = build_agent()
    result = agent.invoke({"input": question})
    return str(result["output"])
