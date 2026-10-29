"""The same three topologies as LangGraph StateGraphs.

Needs ANTHROPIC_API_KEY. Run: python graphs.py {single|fanout|verify} > findings.json
Then score: python ../score.py findings.json

Difference from the Claude Code workflows: each node here is one model call with the
file text pasted into the prompt, not a full agent with tools. That keeps the graph
shape identical while making each node cheaper and more predictable.
"""
import json
import operator
import sys
from pathlib import Path
from typing import Annotated, TypedDict

from langchain_anthropic import ChatAnthropic
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1] / "target" / "shop"
FILES = sorted(p.name for p in ROOT.glob("*.py") if p.name != "__init__.py")
MODEL = "claude-sonnet-5-5"

RULES = (
    "Report only real defects: code that misbehaves for some input, or that contradicts its own "
    "docstring or comments. No style, typing or naming remarks. Report each defect once, at the "
    "line of the faulty code. Name files as shop/<name>.py."
)


class Finding(BaseModel):
    file: str = Field(description="path like shop/money.py")
    line: int = Field(description="1-based line of the faulty code")
    description: str = Field(description="one sentence: what is wrong and why")


class Findings(BaseModel):
    findings: list[Finding]


class Verdict(BaseModel):
    real: bool = Field(description="true only if you could not refute it")
    reason: str


def numbered(name: str) -> str:
    lines = (ROOT / name).read_text().splitlines()
    return f"# shop/{name}\n" + "\n".join(f"{i + 1:4d} | {t}" for i, t in enumerate(lines))


def llm(schema):
    return ChatAnthropic(model=MODEL, max_tokens=4096).with_structured_output(schema)


class State(TypedDict, total=False):
    file: str                                             # set per branch by Send
    finding: dict                                         # set per branch by Send
    raw: Annotated[list[dict], operator.add]              # reducer: branches append
    verified: Annotated[list[dict], operator.add]
    findings: list[dict]


# --- Topology 1: single node over the whole package -------------------------------
def review_all(state: State) -> State:
    code = "\n\n".join(numbered(f) for f in FILES)
    out = llm(Findings).invoke(f"Review this Python package for bugs.\n\n{code}\n\n{RULES}")
    return {"findings": [f.model_dump() for f in out.findings]}


def build_single():
    g = StateGraph(State)
    g.add_node("review_all", review_all)
    g.add_edge(START, "review_all")
    g.add_edge("review_all", END)
    return g.compile()


# --- Shared per-file reviewer (topologies 2 and 3) --------------------------------
def fan_out_files(state: State):
    return [Send("review_file", {"file": f}) for f in FILES]


def review_file(state: State) -> State:
    out = llm(Findings).invoke(f"Review ONE file for bugs.\n\n{numbered(state['file'])}\n\n{RULES}")
    return {"raw": [f.model_dump() for f in out.findings]}


# --- Topology 2: fan-out per file, fan-in merger ----------------------------------
def merge(state: State) -> State:
    out = llm(Findings).invoke(
        "Merge these per-file bug findings into one list: remove duplicates, keep everything else "
        f"unchanged, add nothing.\n\n{json.dumps(state['raw'], indent=2)}"
    )
    return {"findings": [f.model_dump() for f in out.findings]}


def build_fanout():
    g = StateGraph(State)
    g.add_node("review_file", review_file)
    g.add_node("merge", merge)
    g.add_conditional_edges(START, fan_out_files, ["review_file"])
    g.add_edge("review_file", "merge")    # barrier: waits for every Send branch
    g.add_edge("merge", END)
    return g.compile()


# --- Topology 3: per-file reviewer, then a skeptic per finding --------------------
def fan_out_findings(state: State):
    return [Send("verify", {"finding": f}) for f in state["raw"]] or [Send("collect", {})]


def verify(state: State) -> State:
    code = "\n\n".join(numbered(f) for f in FILES)
    v = llm(Verdict).invoke(
        f"A reviewer claims this is a bug:\n{json.dumps(state['finding'])}\n\nTry to REFUTE it. "
        "It is real only if you can name a concrete input that misbehaves, or a clear contradiction "
        f"with its docstring or comments. If unsure, answer real=false.\n\n{code}"
    )
    return {"verified": [{**state["finding"], "verdict": v.model_dump()}]}


def gather(state: State) -> State:
    return {}                             # join point: runs once, after every reviewer


def collect(state: State) -> State:
    return {"findings": [f for f in state.get("verified", []) if f["verdict"]["real"]]}


def build_verify():
    # LangGraph runs in super-steps, so this version has a barrier after review that the
    # Claude Code pipeline() does not. Same graph, different scheduling.
    g = StateGraph(State)
    g.add_node("review_file", review_file)
    g.add_node("gather", gather)
    g.add_node("verify", verify)
    g.add_node("collect", collect)
    g.add_conditional_edges(START, fan_out_files, ["review_file"])
    g.add_edge("review_file", "gather")
    g.add_conditional_edges("gather", fan_out_findings, ["verify", "collect"])
    g.add_edge("verify", "collect")
    g.add_edge("collect", END)
    return g.compile()


GRAPHS = {"single": build_single, "fanout": build_fanout, "verify": build_verify}

if __name__ == "__main__":
    graph = GRAPHS[sys.argv[1]]()
    result = graph.invoke({"raw": [], "verified": []})
    print(json.dumps(result["findings"], indent=2))
