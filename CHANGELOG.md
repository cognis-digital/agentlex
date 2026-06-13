# Changelog

## [0.2.0] — 2026-06-13
### Added
- **`KnowledgeBase`** (`kb.py`) — store ground facts (the content of `inform`
  messages) and query them by unification: single-pattern queries, **conjunctive
  (joined) queries** over a shared variable (Datalog-style), `ask()`, and `retract()`.
- **Forward-chaining rules** (`Rule` / `kb.infer()`) — derive new facts from Horn
  clauses until fixpoint (e.g. high-risk + in a chokepoint ⇒ watchlist).
- `agentlex reason` CLI demo; 16 tests total.

## [0.1.0] — 2026-06-13
- Initial release: symbolic terms + first-order unification, recursive-descent parser,
  speech-act messages (wire + JSON), CLI (parse/unify/msg/demo). Stdlib, cross-OS CI.
