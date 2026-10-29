"""Offline check of the graph wiring with a fake model (no API key needed): pytest test_graphs.py"""
import graphs


class FakeLLM:
    def __init__(self, schema):
        self.schema = schema

    def invoke(self, prompt):
        if self.schema is graphs.Verdict:
            return graphs.Verdict(real='"file": "shop/money.py"' in prompt, reason="fake")
        name = next((f for f in graphs.FILES if f"# shop/{f}" in prompt), "x.py")
        return graphs.Findings(findings=[graphs.Finding(file=f"shop/{name}", line=1, description="fake")])


def run(kind, monkeypatch):
    calls = []
    monkeypatch.setattr(graphs, "llm", lambda schema: calls.append(schema) or FakeLLM(schema))
    out = graphs.GRAPHS[kind]().invoke({"raw": [], "verified": []})
    return out, calls


def test_single(monkeypatch):
    out, calls = run("single", monkeypatch)
    assert len(calls) == 1 and out["findings"]


def test_fanout_runs_one_reviewer_per_file_then_one_merge(monkeypatch):
    out, calls = run("fanout", monkeypatch)
    assert calls.count(graphs.Findings) == len(graphs.FILES) + 1


def test_verify_runs_one_skeptic_per_finding_and_filters(monkeypatch):
    out, calls = run("verify", monkeypatch)
    assert calls.count(graphs.Verdict) == len(graphs.FILES)
    assert [f["file"] for f in out["findings"]] == ["shop/money.py"]
