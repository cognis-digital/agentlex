"""agentlex — a symbolic agent-to-agent language (speech acts + unifiable terms)."""

from agentlex.kb import KnowledgeBase, Rule
from agentlex.message import PERFORMATIVES, Message, from_dict, from_wire
from agentlex.parse import ParseError, parse_term
from agentlex.terms import (Compound, Literal, Subst, Symbol, Term, Var,
                            substitute, unify, walk)

__version__ = "0.2.0"

__all__ = [
    "Symbol", "Var", "Literal", "Compound", "Term", "Subst", "unify", "walk",
    "substitute", "parse_term", "ParseError", "Message", "from_wire", "from_dict",
    "PERFORMATIVES", "KnowledgeBase", "Rule", "__version__",
]
