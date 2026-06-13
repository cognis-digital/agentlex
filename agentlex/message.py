"""Agent-to-agent messages — speech acts carrying symbolic content.

agentlex separates *intent* (the performative: are you telling me, asking me, or
proposing something?) from *content* (a symbolic term). This is the lesson of the
classic agent communication languages (KQML, FIPA-ACL), kept tiny and modern so it
drops onto any transport (an edgemesh /v1 stream, MCP, a queue, a socket).

Wire form (one line, human-readable):
    inform from:scout to:command conv:c12 :: risk(vessel-210111000, high)
    query  from:command to:scout conv:c12 :: risk(?vessel, high)

Pure standard library.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from agentlex.parse import parse_term
from agentlex.terms import Term

# Speech-act types (a pragmatic subset of FIPA-ACL performatives).
PERFORMATIVES = {
    "inform",    # I assert this is true
    "request",   # please do this
    "query",     # is this true? / what binds this pattern?
    "propose",   # I suggest this
    "agree",     # I accept a request/proposal
    "refuse",    # I decline
    "subscribe", # notify me when this changes
    "ack",       # received
}


@dataclass
class Message:
    performative: str
    sender: str
    receiver: str
    content: Term
    conversation: str = ""
    in_reply_to: str = ""
    ontology: str = ""

    def __post_init__(self):
        if self.performative not in PERFORMATIVES:
            raise ValueError(f"unknown performative {self.performative!r}; "
                             f"expected one of {sorted(PERFORMATIVES)}")

    def to_wire(self) -> str:
        head = [self.performative, f"from:{self.sender}", f"to:{self.receiver}"]
        if self.conversation:
            head.append(f"conv:{self.conversation}")
        if self.in_reply_to:
            head.append(f"reply:{self.in_reply_to}")
        if self.ontology:
            head.append(f"onto:{self.ontology}")
        return " ".join(head) + " :: " + str(self.content)

    def to_dict(self) -> dict:
        return {"performative": self.performative, "sender": self.sender,
                "receiver": self.receiver, "content": str(self.content),
                "conversation": self.conversation, "in_reply_to": self.in_reply_to,
                "ontology": self.ontology}


def from_wire(line: str) -> Message:
    if "::" not in line:
        raise ValueError("message missing ' :: ' content separator")
    header, content = line.split("::", 1)
    parts = header.split()
    if not parts:
        raise ValueError("empty message header")
    perf = parts[0]
    fields = {"from": "", "to": "", "conv": "", "reply": "", "onto": ""}
    for tok in parts[1:]:
        if ":" in tok:
            k, _, v = tok.partition(":")
            if k in fields:
                fields[k] = v
    return Message(performative=perf, sender=fields["from"], receiver=fields["to"],
                   content=parse_term(content.strip()), conversation=fields["conv"],
                   in_reply_to=fields["reply"], ontology=fields["onto"])


def from_dict(d: dict) -> Message:
    return Message(performative=d["performative"], sender=d.get("sender", ""),
                   receiver=d.get("receiver", ""), content=parse_term(d["content"]),
                   conversation=d.get("conversation", ""), in_reply_to=d.get("in_reply_to", ""),
                   ontology=d.get("ontology", ""))
