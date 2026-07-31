#!/usr/bin/env python3
"""Generate the presentation's hand-drawn figures.

Each function returns one finished SVG. Seeds are fixed, so re-running this
produces byte-identical files and a rebuild is never a spurious diff.
"""

from __future__ import annotations

import sys
from pathlib import Path

from sketch import (
    INK,
    MUTED,
    Pen,
    Text,
    document,
    ink,
    rough_arrow,
    rough_line,
    rough_rect,
    rough_region,
    wash,
)

GREEN = "#e4f3e7"
SAND = "#fff0d8"
STONE = "#eef2ed"
BLUSH = "#f9e8e5"


def box(pen, x, y, w, h, label, sub=None, fill=None, size=14, wobble=3.0):
    """A sketched box with a bold label and an optional muted second line."""
    parts = []
    if fill:
        parts.append(wash(rough_region(pen, x, y, w, h, wobble), fill))
    parts.append(ink(rough_rect(pen, x, y, w, h, wobble), 2.0))
    if sub:
        parts.append(Text(x + w / 2, y + h / 2 - 2, label, size, "600").render())
        parts.append(Text(x + w / 2, y + h / 2 + 16, sub, size - 3, "400", fill=MUTED).render())
    else:
        parts.append(Text(x + w / 2, y + h / 2 + 5, label, size, "600").render())
    return parts


# --------------------------------------------------------------------------
# 02 — the black box
# --------------------------------------------------------------------------

def black_box() -> str:
    pen = Pen(23)
    p = []
    p.append(Text(300, 26, "One opaque object", 15, "700").render())

    # the box itself, hatched to read as impenetrable. The hatch is clipped to
    # the box so an unsteady stroke cannot wander outside the thing it fills.
    p.append(
        '<defs><clipPath id="bb-clip">'
        '<rect x="178" y="50" width="244" height="164"/>'
        "</clipPath></defs>"
    )
    p.append(wash(rough_region(pen, 176, 48, 248, 168, 3.6), STONE))
    hatch = []
    for index in range(11):
        offset = 176 + index * 27
        hatch.append(ink(rough_line(pen, offset + 26, 44, offset - 30, 220, 2.0), 1.0, MUTED, 0.3))
    p.append('<g clip-path="url(#bb-clip)">' + "".join(hatch) + "</g>")
    p.append(ink(rough_rect(pen, 176, 48, 248, 168, 3.6), 2.4))

    for index, label in enumerate(
        ("company rules", "AI instructions", "software code", "the model's guesswork")
    ):
        p.append(Text(300, 84 + index * 34, label, 13.5, "500").render())

    # four questions that cannot be answered from outside
    for index, (qx, qy) in enumerate(((60, 78), (60, 186), (540, 78), (540, 186))):
        anchor = "start" if qx < 300 else "end"
        p.append(Text(qx, qy, "?", 26, "700", anchor="middle", fill=MUTED).render())

    p.append(ink(rough_arrow(pen, 84, 86, 168, 108, 2.4), 1.8, MUTED))
    p.append(ink(rough_arrow(pen, 84, 182, 168, 158, 2.4), 1.8, MUTED))
    p.append(ink(rough_arrow(pen, 516, 86, 432, 108, 2.4), 1.8, MUTED))
    p.append(ink(rough_arrow(pen, 516, 182, 432, 158, 2.4), 1.8, MUTED))

    p.append(Text(300, 244, "Wrong answer. Which part caused it?", 13.5, "600", fill=MUTED).render())

    return document(
        width=600,
        height=262,
        slug="bb",
        title="Business rules, prompts, code, and model weights inside one opaque object",
        desc=(
            "A single hatched box contains business rules, the system prompt, application code, and "
            "model weights together. Question marks press in from all four sides. When the answer is "
            "wrong, nothing outside the box says which part produced it."
        ),
        body="\n".join("  " + part for part in p),
    )


# --------------------------------------------------------------------------
# 04 — knowledge answers, judgment decides
# --------------------------------------------------------------------------

def knowledge_vs_judgment() -> str:
    pen = Pen(41)
    p = []

    p.extend(box(pen, 24, 56, 216, 150, "Knowledge", "what do we know?", STONE, 17))
    for index, line in enumerate(
        ("documents, databases,", "search results", "— no opinion on what to do")
    ):
        p.append(Text(132, 236 + index * 22, line, 12.5, "400", fill=MUTED).render())

    p.extend(box(pen, 360, 56, 216, 150, "Judgment", "so what happens?", GREEN, 17))
    for index, line in enumerate(
        ("which rule applies,", "what overrides it,", "when to ask a person")
    ):
        p.append(Text(468, 236 + index * 22, line, 12.5, "400", fill=MUTED).render())

    p.append(ink(rough_arrow(pen, 252, 131, 348, 131, 2.4, 11), 2.1))
    p.append(Text(300, 118, "feeds", 12.5, "600", fill=MUTED).render())

    p.append(Text(300, 32, "One feeds the other", 15, "700").render())
    return document(
        width=600,
        height=310,
        slug="kj",
        title="Knowledge is an input to judgment, not a layer above it",
        desc=(
            "Two boxes side by side. Knowledge answers what is known — documents, tables, APIs, "
            "retrieval and citation — and holds no view on what follows. It feeds Judgment, which "
            "decides what follows: applicability and rules, exceptions and escalation, testable and "
            "portable."
        ),
        body="\n".join("  " + part for part in p),
    )


# --------------------------------------------------------------------------
# 05 — what a pack declares
# --------------------------------------------------------------------------

def pack_anatomy() -> str:
    pen = Pen(59)
    p = []
    p.append(Text(340, 26, "One document, one decision", 15, "700").render())

    p.append(wash(rough_region(pen, 88, 44, 504, 296, 3.4), "#ffffff"))
    p.append(ink(rough_rect(pen, 88, 44, 504, 296, 3.4), 2.3))

    rows = (
        ("the decision", "what is being decided, and why", GREEN),
        ("evidence", "what facts it needs", None),
        ("when it applies", "and when it does not", None),
        ("rules", "what follows from those facts", None),
        ("exceptions", "what overrides the normal answer", None),
        ("missing facts", "what to do when something is unknown", None),
        ("answers", "the fixed set it may return", None),
        ("ask a human", "when a person must take over", SAND),
    )
    for index, (name, gloss, fill) in enumerate(rows):
        top = 62 + index * 35
        if fill:
            p.append(wash(rough_region(pen, 100, top, 480, 28, 2.0), fill))
        p.append(Text(114, top + 19, name, 13, "700", anchor="start").render())
        p.append(Text(240, top + 19, gloss, 12, "400", anchor="start", fill=MUTED).render())

    p.append(Text(340, 364, "A plain file. No AI, no code, no vendor inside it.", 12.5, "500", fill=MUTED).render())
    return document(
        width=680,
        height=384,
        slug="pa",
        title="What one Judgment Pack declares",
        desc=(
            "A single document listing, in order: decision — what is being decided and why; evidence "
            "— what may support it; applicability — when this pack applies at all; rules — what "
            "follows from the evidence; exceptions — what overrides the ordinary outcome; "
            "uncertainty — what happens when a fact is unknown; outcomes — the closed set of "
            "permitted results; and escalation — when a human must take over. It is portable JSON "
            "with no prompt, model, or runtime inside it."
        ),
        body="\n".join("  " + part for part in p),
    )


# --------------------------------------------------------------------------
# 06 — the conformance ladder and the line
# --------------------------------------------------------------------------

def conformance_line() -> str:
    pen = Pen(71)
    p = []
    p.append(Text(300, 26, "What can be checked — and what never can", 14, "700").render())

    inside = (
        ("Readable", "the file opens, and is what it says it is"),
        ("Well-formed", "every part is present and correctly shaped"),
        ("Consistent", "nothing inside it contradicts anything else"),
        ("Agreed", "two separate tools get the same answer from it"),
    )
    outside = (
        ("Is it true?", "whether the facts behind it are real"),
        ("Is it allowed?", "whether anyone with authority approved it"),
        ("Is it safe?", "whether acting on it here is wise"),
    )

    for index, (name, gloss) in enumerate(inside):
        top = 44 + index * 44
        p.append(wash(rough_region(pen, 40, top, 520, 36, 2.4), GREEN))
        p.append(ink(rough_rect(pen, 40, top, 520, 36, 2.4), 1.9))
        p.append(Text(58, top + 23, name, 13.5, "700", anchor="start").render())
        p.append(Text(180, top + 23, gloss, 12.5, "400", anchor="start", fill=MUTED).render())

    # the line the specification stops at
    p.append(ink(rough_line(pen, 26, 232, 574, 232, 2.6), 2.6, "#8d3026"))
    p.append(ink(rough_line(pen, 26, 236, 574, 236, 2.6), 1.4, "#8d3026", 0.5))
    p.append(Text(300, 254, "nothing below this line is ever claimed", 12.5, "700", fill="#8d3026").render())

    for index, (name, gloss) in enumerate(outside):
        top = 268 + index * 44
        p.append(ink(rough_rect(pen, 40, top, 520, 36, 2.4), 1.7, MUTED))
        p.append(Text(58, top + 23, name, 13.5, "700", anchor="start", fill=MUTED).render())
        p.append(Text(210, top + 23, gloss, 12.5, "400", anchor="start", fill=MUTED).render())

    return document(
        width=600,
        height=412,
        slug="cl",
        title="What conformance establishes, and what it never establishes",
        desc=(
            "Four filled rows above a drawn line: carrier — the bytes parse as declared; structural "
            "— the document fits the schema; semantic — its references and cross-field rules hold; "
            "evaluator — an implementation computes the specified result. Below the line, drawn in "
            "outline only: factual grounding, authorization, and operational fitness. The "
            "specification stops at the line on purpose."
        ),
        body="\n".join("  " + part for part in p),
    )


# --------------------------------------------------------------------------
# 07 — one portable result
# --------------------------------------------------------------------------

def portable_result() -> str:
    pen = Pen(89)
    p = []
    p.append(Text(300, 26, "Same file, same facts, different software", 15, "700").render())

    p.extend(box(pen, 216, 46, 168, 56, "one decision file", None, GREEN, 13.5))

    p.append(ink(rough_arrow(pen, 250, 106, 150, 142, 2.4), 1.9))
    p.append(ink(rough_arrow(pen, 350, 106, 450, 142, 2.4), 1.9))

    p.extend(box(pen, 44, 146, 212, 60, "the reference tool", None, None, 13))
    p.extend(box(pen, 344, 146, 212, 60, "an independent rebuild", None, None, 13))
    p.append(Text(150, 222, "built by the project", 11.5, "400", fill=MUTED).render())
    p.append(Text(450, 222, "built from the written spec alone", 11.5, "400", fill=MUTED).render())

    p.append(ink(rough_arrow(pen, 150, 232, 250, 268, 2.4), 1.9))
    p.append(ink(rough_arrow(pen, 450, 232, 350, 268, 2.4), 1.9))

    p.extend(box(pen, 176, 272, 248, 62, "the same answer", "identical, character for character", SAND, 15))

    p.append(Text(300, 358, "If two careful readers disagree, the writing was unclear — and the writing gets fixed.", 12, "500", fill=MUTED).render())
    return document(
        width=600,
        height=378,
        slug="pr",
        title="Two independent implementations produce one byte-identical result",
        desc=(
            "One pack and its facts feed two separately written implementations — the Go reference "
            "runtime and a clean-room evaluator, each written from the specification text alone. "
            "Both produce one disposition, byte-identical after RFC 8785 canonicalization. A "
            "disagreement between them locates ambiguity in the prose."
        ),
        body="\n".join("  " + part for part in p),
    )


# --------------------------------------------------------------------------
# 08 — where the inputs come from
# --------------------------------------------------------------------------

def attested_inputs() -> str:
    pen = Pen(101)
    p = []
    p.append(Text(300, 24, "The AI never touches the evidence", 15, "700").render())

    p.extend(box(pen, 24, 52, 130, 58, "source", None, None, 13.5))
    p.append(ink(rough_arrow(pen, 158, 81, 210, 81, 2.2, 10), 1.9))
    p.extend(box(pen, 214, 44, 172, 74, "gateway", "fetches it and signs it", GREEN, 15))
    p.append(ink(rough_arrow(pen, 390, 81, 442, 81, 2.2, 10), 1.9))
    p.extend(box(pen, 446, 52, 130, 58, "receipt", None, SAND, 13.5))

    # the chain of receipts, sealed
    p.append(Text(300, 148, "linked in order, then sealed", 12.5, "600", fill=MUTED).render())
    for index in range(4):
        left = 148 + index * 78
        p.append(ink(rough_rect(pen, left, 160, 58, 34, 2.2), 1.7))
        if index < 3:
            p.append(ink(rough_line(pen, left + 58, 177, left + 78, 177, 1.6), 1.5, MUTED))
    p.append(Text(177, 182, "r1", 12, "600").render())
    p.append(Text(255, 182, "r2", 12, "600").render())
    p.append(Text(333, 182, "r3", 12, "600").render())
    p.append(wash(rough_region(pen, 382, 160, 58, 34, 2.2), SAND))
    p.append(Text(411, 182, "seal", 12, "700").render())

    p.append(ink(rough_arrow(pen, 300, 202, 300, 236, 2.2, 10), 1.9))
    p.extend(box(pen, 180, 240, 240, 56, "verifier", "needs only a public key", None, 14.5))

    p.append(Text(300, 324, "Shows the data was not tampered with. Never that the data is correct.", 12, "600", fill="#8d3026").render())
    return document(
        width=600,
        height=344,
        slug="ai",
        title="Attested inputs: signed receipts, a sealed session, and a public-key verifier",
        desc=(
            "A source is run by the gateway, which signs each result into a receipt. Receipts are "
            "chained per session and the session is then sealed. A verifier checks the chain and the "
            "seal using only the public key, so checking grants no power to forge. The mechanism "
            "proves the byte-lineage of the inputs a judgment was computed over — never that those "
            "bytes are true."
        ),
        body="\n".join("  " + part for part in p),
    )


# --------------------------------------------------------------------------
# 01 — the premise
# --------------------------------------------------------------------------

def decision_engine() -> str:
    pen = Pen(131)
    p = []
    p.append(Text(300, 26, "What a company actually produces", 15, "700").render())

    p.append(wash(rough_region(pen, 40, 48, 200, 200, 3.4), STONE))
    p.append(ink(rough_rect(pen, 40, 48, 200, 200, 3.4), 2.2))
    p.append(Text(140, 76, "the organization", 14, "700").render())
    for index, line in enumerate(("policy", "precedent", "expertise", "hard-won exceptions")):
        p.append(Text(140, 108 + index * 30, line, 12.5, "400", fill=MUTED).render())

    p.append(ink(rough_arrow(pen, 246, 148, 322, 148, 2.4, 11), 2.0))
    p.append(Text(284, 134, "judgment", 12, "600", fill=MUTED).render())

    p.append(wash(rough_region(pen, 326, 84, 234, 128, 3.4), GREEN))
    p.append(ink(rough_rect(pen, 326, 84, 234, 128, 3.4), 2.2))
    p.append(Text(443, 114, "decisions", 15, "700").render())
    for index, line in enumerate(("approve  ·  reject", "escalate  ·  hold")):
        p.append(Text(443, 146 + index * 26, line, 13, "500", fill=MUTED).render())

    p.append(Text(300, 276, "Hand the work to AI and this arrow is what matters most —", 12.5, "500", fill=MUTED).render())
    p.append(Text(300, 296, "and it is the one thing nobody wrote down.", 12.5, "700").render())
    return document(
        width=600,
        height=316,
        slug="de",
        title="The organization turns policy, precedent, and expertise into decisions",
        desc=(
            "An organization box holds policy, precedent, expertise, and hard-won exceptions. An "
            "arrow labelled judgment leads from it to a box of decisions: approve, reject, escalate, "
            "hold. When execution is handed to an agent, that arrow is the only thing that matters — "
            "and it is the one thing nobody wrote down."
        ),
        body="\n".join("  " + part for part in p),
    )


FIGURES = {
    "deck-decision-engine": decision_engine,
    "deck-black-box": black_box,
    "deck-knowledge-vs-judgment": knowledge_vs_judgment,
    "deck-pack-anatomy": pack_anatomy,
    "deck-conformance-line": conformance_line,
    "deck-portable-result": portable_result,
    "deck-attested-inputs": attested_inputs,
}


def main() -> int:
    destination = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    destination.mkdir(parents=True, exist_ok=True)
    for name, builder in FIGURES.items():
        path = destination / f"{name}.svg"
        path.write_text(builder(), encoding="utf-8")
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
