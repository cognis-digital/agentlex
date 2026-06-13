"""KnowledgeBase: fact assertion, unification queries, conjunctive joins, rules."""

from __future__ import annotations

from agentlex import KnowledgeBase, parse_term
from agentlex.cli import main


def _kb(*facts):
    kb = KnowledgeBase()
    for f in facts:
        kb.assert_fact(parse_term(f))
    return kb


def test_assert_dedup_and_retract():
    kb = KnowledgeBase()
    assert kb.assert_fact(parse_term("risk(v1, high)")) is True
    assert kb.assert_fact(parse_term("risk(v1, high)")) is False   # dup
    assert kb.retract(parse_term("risk(v1, high)")) is True
    assert kb.retract(parse_term("risk(v1, high)")) is False


def test_single_pattern_query_binds():
    kb = _kb("risk(vessel-1, high)", "risk(vessel-2, low)")
    res = kb.query(parse_term("risk(?v, high)"))
    assert len(res) == 1 and str(res[0]["v"]) == "vessel-1"
    assert kb.ask(parse_term("risk(?v, low)")) is True
    assert kb.ask(parse_term("risk(?v, extreme)")) is False


def test_conjunctive_query_joins_on_shared_var():
    kb = _kb("risk(vessel-1, high)", "location(vessel-1, hormuz)",
             "risk(vessel-2, high)", "location(vessel-2, baltic)")
    res = kb.query([parse_term("risk(?v, high)"), parse_term("location(?v, ?where)")])
    pairs = {(str(s["v"]), str(s["where"])) for s in res}
    assert pairs == {("vessel-1", "hormuz"), ("vessel-2", "baltic")}


def test_forward_chaining_rule():
    kb = _kb("risk(vessel-1, high)", "location(vessel-1, hormuz)", "chokepoint(hormuz)")
    kb.add_rule(parse_term("watchlist(?v)"),
                [parse_term("risk(?v, high)"), parse_term("location(?v, ?c)"), parse_term("chokepoint(?c)")])
    derived = kb.infer()
    assert parse_term("watchlist(vessel-1)") in derived
    assert kb.ask(parse_term("watchlist(vessel-1)"))


def test_cli_reason(capsys):
    assert main(["reason"]) == 0
    out = capsys.readouterr().out
    assert "?v = vessel-1" in out and "watchlist(vessel-1)" in out
