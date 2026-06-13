"""A tiny knowledge base + query engine over agentlex terms.

Speaking a language is half of it; the other half is *reasoning over what you're
told*. A `KnowledgeBase` stores ground facts (the content of `inform` messages) and
answers queries by **unification** — including conjunctive (multi-pattern) queries,
which is the core of a Datalog-style engine:

    kb.assert_fact(parse_term("risk(vessel-1, high)"))
    kb.assert_fact(parse_term("location(vessel-1, hormuz)"))
    kb.query([parse_term("risk(?v, high)"), parse_term("location(?v, ?where)")])
    # -> [{v: vessel-1, where: hormuz}]

Optional **rules** (Horn clauses) enable forward-chaining: derive new facts from
existing ones until nothing new appears. Pure standard library.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from agentlex.terms import Subst, Term, substitute, unify


@dataclass
class Rule:
    head: Term
    body: list[Term] = field(default_factory=list)


class KnowledgeBase:
    def __init__(self) -> None:
        self.facts: list[Term] = []
        self.rules: list[Rule] = []

    def assert_fact(self, term: Term) -> bool:
        """Add a ground fact. Returns False if already present."""
        if term in self.facts:
            return False
        self.facts.append(term)
        return True

    def retract(self, term: Term) -> bool:
        if term in self.facts:
            self.facts.remove(term)
            return True
        return False

    def add_rule(self, head: Term, body: list[Term]) -> None:
        self.rules.append(Rule(head, list(body)))

    # --- querying ------------------------------------------------------------
    def _solve(self, goals: list[Term], subst: Subst):
        """Backtracking conjunctive solver: yield each satisfying substitution."""
        if not goals:
            yield subst
            return
        goal, rest = goals[0], goals[1:]
        g = substitute(goal, subst)
        for fact in self.facts:
            s2 = unify(g, fact, subst)
            if s2 is not None:
                yield from self._solve(rest, s2)

    def query(self, pattern: Term | list[Term]) -> list[Subst]:
        """All variable bindings under which the pattern(s) hold. Empty list = none."""
        goals = pattern if isinstance(pattern, list) else [pattern]
        out, seen = [], set()
        for s in self._solve(goals, {}):
            key = tuple(sorted((k, str(v)) for k, v in s.items()))
            if key not in seen:
                seen.add(key)
                out.append(s)
        return out

    def ask(self, pattern: Term | list[Term]) -> bool:
        """True if the pattern(s) can be satisfied."""
        return bool(self.query(pattern))

    # --- forward chaining ----------------------------------------------------
    def infer(self, max_rounds: int = 100) -> list[Term]:
        """Apply rules until fixpoint; return the newly derived facts."""
        derived: list[Term] = []
        for _ in range(max_rounds):
            new_this_round = []
            for rule in self.rules:
                for s in self._solve(rule.body, {}):
                    fact = substitute(rule.head, s)
                    if fact not in self.facts and fact not in new_this_round:
                        new_this_round.append(fact)
            if not new_this_round:
                break
            self.facts.extend(new_this_round)
            derived.extend(new_this_round)
        return derived
