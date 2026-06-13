"""Symbolic terms + unification — the core of agentlex.

A small, classical symbolic-AI representation that agents use to say things to each
other precisely (vs. trading raw natural-language strings). Four term kinds:

    Symbol      a bareword atom            vessel        high
    Var         a logic variable           ?x            ?risk
    Literal     a string or number         "Neptune"     42
    Compound    functor with arguments     risk(vessel, high)

Syntax (compact, line-friendly):
    risk(vessel-210111000, high)
    sighted(?vessel, location(36.42, 22.96))

`unify` does standard first-order unification (with occurs-check), which is what lets
one agent's pattern  `risk(?v, high)`  match another's fact  `risk(vessel-1, high)`
and bind `?v = vessel-1`. Pure standard library.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union


@dataclass(frozen=True)
class Symbol:
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class Var:
    name: str

    def __str__(self) -> str:
        return "?" + self.name


@dataclass(frozen=True)
class Literal:
    value: Union[str, int, float]

    def __str__(self) -> str:
        return f'"{self.value}"' if isinstance(self.value, str) else str(self.value)


@dataclass(frozen=True)
class Compound:
    functor: str
    args: tuple = field(default_factory=tuple)

    def __str__(self) -> str:
        return f"{self.functor}({', '.join(str(a) for a in self.args)})"


Term = Union[Symbol, Var, Literal, Compound]
Subst = dict  # Var.name -> Term


def walk(t: Term, s: Subst) -> Term:
    """Resolve a term through the substitution to its current binding."""
    while isinstance(t, Var) and t.name in s:
        t = s[t.name]
    return t


def occurs(v: Var, t: Term, s: Subst) -> bool:
    t = walk(t, s)
    if isinstance(t, Var):
        return t.name == v.name
    if isinstance(t, Compound):
        return any(occurs(v, a, s) for a in t.args)
    return False


def unify(a: Term, b: Term, s: Subst | None = None) -> Subst | None:
    """Return a substitution unifying a and b, or None if they can't unify."""
    s = {} if s is None else dict(s)
    a, b = walk(a, s), walk(b, s)
    if a == b:
        return s
    if isinstance(a, Var):
        if occurs(a, b, s):
            return None
        s[a.name] = b
        return s
    if isinstance(b, Var):
        if occurs(b, a, s):
            return None
        s[b.name] = a
        return s
    if isinstance(a, Compound) and isinstance(b, Compound):
        if a.functor != b.functor or len(a.args) != len(b.args):
            return None
        for x, y in zip(a.args, b.args):
            s = unify(x, y, s)
            if s is None:
                return None
        return s
    return None


def substitute(t: Term, s: Subst) -> Term:
    """Apply a substitution fully to a term."""
    t = walk(t, s)
    if isinstance(t, Compound):
        return Compound(t.functor, tuple(substitute(a, s) for a in t.args))
    return t
