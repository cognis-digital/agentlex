"""Parser for the agentlex term/message syntax (recursive descent, stdlib only)."""

from __future__ import annotations

import re

from agentlex.terms import Compound, Literal, Symbol, Term, Var

_TOKEN = re.compile(r"""
    \s*(?:
      (?P<lparen>\()
    | (?P<rparen>\))
    | (?P<comma>,)
    | (?P<string>"(?:[^"\\]|\\.)*")
    | (?P<number>-?\d+\.\d+|-?\d+)
    | (?P<var>\?[A-Za-z_][A-Za-z0-9_]*)
    | (?P<sym>[A-Za-z_][A-Za-z0-9_\-./:]*)
    )""", re.VERBOSE)


class ParseError(ValueError):
    pass


def _tokens(text: str):
    pos = 0
    while pos < len(text):
        if text[pos].isspace():
            pos += 1
            continue
        m = _TOKEN.match(text, pos)
        if not m or m.end() == pos:
            raise ParseError(f"unexpected input at {pos!r}: {text[pos:pos+20]!r}")
        pos = m.end()
        kind = m.lastgroup
        yield kind, m.group(kind).strip()
    yield "end", ""


class _Parser:
    def __init__(self, text: str):
        self._it = _tokens(text)
        self._cur = next(self._it)

    def _advance(self):
        tok = self._cur
        self._cur = next(self._it)
        return tok

    def parse_term(self) -> Term:
        kind, val = self._cur
        if kind == "var":
            self._advance()
            return Var(val[1:])
        if kind == "string":
            self._advance()
            return Literal(bytes(val[1:-1], "utf-8").decode("unicode_escape"))
        if kind == "number":
            self._advance()
            return Literal(float(val) if ("." in val) else int(val))
        if kind == "sym":
            self._advance()
            if self._cur[0] == "lparen":      # compound
                self._advance()
                args = []
                if self._cur[0] != "rparen":
                    args.append(self.parse_term())
                    while self._cur[0] == "comma":
                        self._advance()
                        args.append(self.parse_term())
                if self._cur[0] != "rparen":
                    raise ParseError("expected ')'")
                self._advance()
                return Compound(val, tuple(args))
            return Symbol(val)
        raise ParseError(f"unexpected token {kind}:{val!r}")


def parse_term(text: str) -> Term:
    p = _Parser(text)
    t = p.parse_term()
    if p._cur[0] != "end":
        raise ParseError(f"trailing input after term: {p._cur}")
    return t
