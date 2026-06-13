"""Tests for agentlex: terms, unification, parsing, and messages."""

from __future__ import annotations

import pytest

from agentlex import (Compound, Literal, Message, Symbol, Var, from_wire,
                      parse_term, substitute, unify)
from agentlex.cli import main
from agentlex.parse import ParseError


# --- parsing / serialization -------------------------------------------------
def test_parse_roundtrip():
    for text in ["vessel", "?x", "42", '"Neptune Star"', "risk(vessel-1, high)",
                 "sighted(?v, location(36.42, 22.96))"]:
        t = parse_term(text)
        # re-parsing the serialization yields an equal term
        assert parse_term(str(t)) == t


def test_parse_kinds():
    assert parse_term("vessel") == Symbol("vessel")
    assert parse_term("?v") == Var("v")
    assert parse_term("42") == Literal(42)
    assert parse_term("3.5") == Literal(3.5)
    assert parse_term("risk(v1, high)") == Compound("risk", (Symbol("v1"), Symbol("high")))


def test_parse_errors():
    with pytest.raises(ParseError):
        parse_term("risk(v1, high")     # unbalanced
    with pytest.raises(ParseError):
        parse_term("a b c")             # trailing junk


# --- unification -------------------------------------------------------------
def test_unify_binds_variable():
    s = unify(parse_term("risk(?v, high)"), parse_term("risk(vessel-1, high)"))
    assert s is not None
    assert substitute(parse_term("?v"), s) == Symbol("vessel-1")


def test_unify_failure_and_occurs_check():
    assert unify(parse_term("risk(v1, high)"), parse_term("risk(v1, low)")) is None
    # occurs check: ?x = f(?x) must fail
    assert unify(Var("x"), Compound("f", (Var("x"),))) is None


def test_unify_two_variables():
    s = unify(parse_term("p(?x, ?y)"), parse_term("p(?y, c)"))
    assert s is not None
    assert substitute(parse_term("?x"), s) == Symbol("c")


# --- messages ----------------------------------------------------------------
def test_message_wire_roundtrip():
    m = Message("inform", "scout", "command", parse_term("risk(vessel-1, high)"),
                conversation="c12", in_reply_to="m1")
    wire = m.to_wire()
    back = from_wire(wire)
    assert back.performative == "inform" and back.sender == "scout"
    assert back.receiver == "command" and back.conversation == "c12"
    assert back.in_reply_to == "m1" and back.content == m.content


def test_unknown_performative_rejected():
    with pytest.raises(ValueError):
        Message("yell", "a", "b", Symbol("x"))


def test_query_pattern_matches_inform_fact():
    fact = from_wire("inform from:scout to:cmd conv:c1 :: risk(vessel-9, high)")
    pattern = from_wire("query from:cmd to:scout conv:c1 :: risk(?v, high)")
    s = unify(pattern.content, fact.content)
    assert s is not None and substitute(Var("v"), s) == Symbol("vessel-9")


# --- cli ---------------------------------------------------------------------
def test_cli_demo_and_unify(capsys):
    assert main(["demo"]) == 0
    assert main(["unify", "risk(?v, high)", "risk(v1, high)"]) == 0
    out = capsys.readouterr().out
    assert "?vessel = vessel-210111000" in out and '"v"' in out


def test_cli_bad_unify_returns_1():
    assert main(["unify", "a", "b"]) == 1
