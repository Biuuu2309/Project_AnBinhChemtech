"""
Codex CLI integration boundary.

Prototype happy path does NOT call Codex.
Template fill / validation / job state stay deterministic Python code.

In production this module can invoke Codex CLI only for tasks that
truly need AI assistance (e.g. free-text note normalization).
"""


def run_codex_assist(prompt: str) -> str:
    raise NotImplementedError(
        "Codex CLI is stubbed for the prototype. "
        "Deterministic template filling is used instead."
    )
