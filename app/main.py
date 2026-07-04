"""FastAPI app exposing the NL-to-SQL agent."""

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
def query(request: QueryRequest) -> QueryResponse:
    try:
        answer = ask(request.question)
        return QueryResponse(question=request.question, answer=answer)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Agent failed to process query: {e}"
        )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
