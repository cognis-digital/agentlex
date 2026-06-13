"""agentlex CLI — parse terms, unify patterns, and read/explain A2A messages.

    agentlex parse  "risk(vessel-1, high)"          # parse + echo a term
    agentlex unify  "risk(?v, high)" "risk(v1, high)"  # show the binding
    agentlex msg    "inform from:a to:b :: risk(v1, high)"   # parse a message -> JSON
    agentlex demo                                    # two agents exchange messages
"""

from __future__ import annotations

import argparse
import json
import sys

from agentlex import __version__
from agentlex.message import Message, from_wire
from agentlex.parse import ParseError, parse_term
from agentlex.terms import Symbol, Compound, substitute, unify


def _demo() -> int:
    scout = Message("inform", "scout", "command",
                    parse_term("risk(vessel-210111000, high)"), conversation="c12")
    print("scout  ->", scout.to_wire())
    query = Message("query", "command", "scout",
                    parse_term("risk(?vessel, high)"), conversation="c12", in_reply_to="m1")
    print("command->", query.to_wire())
    # command's pattern unifies against scout's fact -> learns the vessel id
    s = unify(query.content, scout.content)
    binding = substitute(query.content.args[0], s) if s is not None else None
    print("unify   -> ?vessel =", binding)
    return 0


def _reason() -> int:
    from agentlex.kb import KnowledgeBase
    kb = KnowledgeBase()
    for f in ["risk(vessel-1, high)", "location(vessel-1, hormuz)", "risk(vessel-2, low)"]:
        kb.assert_fact(parse_term(f))
    # conjunctive query: a high-risk vessel AND where it is
    res = kb.query([parse_term("risk(?v, high)"), parse_term("location(?v, ?where)")])
    print("facts asserted:", len(kb.facts))
    for s in res:
        print("  match: ?v =", s["v"], "  ?where =", s["where"])
    # a rule: high-risk + in a chokepoint => watchlist it
    kb.assert_fact(parse_term("chokepoint(hormuz)"))
    kb.add_rule(parse_term("watchlist(?v)"),
                [parse_term("risk(?v, high)"), parse_term("location(?v, ?c)"), parse_term("chokepoint(?c)")])
    derived = kb.infer()
    print("derived by forward-chaining:", [str(d) for d in derived])
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="agentlex", description=__doc__.splitlines()[0])
    p.add_argument("--version", action="version", version=f"agentlex {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("parse"); sp.add_argument("term")
    su = sub.add_parser("unify"); su.add_argument("a"); su.add_argument("b")
    sm = sub.add_parser("msg"); sm.add_argument("wire")
    sub.add_parser("demo")
    sub.add_parser("reason")
    args = p.parse_args(argv)

    try:
        if args.cmd == "parse":
            print(str(parse_term(args.term)))
        elif args.cmd == "unify":
            s = unify(parse_term(args.a), parse_term(args.b))
            if s is None:
                print("no unifier (terms do not unify)"); return 1
            print(json.dumps({k: str(v) for k, v in s.items()}, indent=2) if s else "{} (already equal)")
        elif args.cmd == "msg":
            print(json.dumps(from_wire(args.wire).to_dict(), indent=2))
        elif args.cmd == "demo":
            return _demo()
        elif args.cmd == "reason":
            return _reason()
    except (ParseError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr); return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
