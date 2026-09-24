"""
Codex CLI integration boundary (production path on Mac mini).

Prototype default uses MockAI instead. When USE_CODEX_CLI=true, the worker
selects CodexRunner. Real CLI invocation is intentionally not required to
run the demo — call sites must catch CodexUnavailableError and fall back.
"""

from __future__ import annotations

import logging
import shutil
import subprocess

from ai.types import NoteNormalizationResult

logger = logging.getLogger("worker.ai.codex")


class CodexUnavailableError(RuntimeError):
    pass


class CodexRunner:
    """
    Production-oriented adapter. Integration point for Codex CLI on Mac mini.

    Expected future command (illustrative, not executed unless binary exists):
      codex exec --json "Normalize this quotation note: ..."
    """

    def normalize_note(self, raw_note: str) -> NoteNormalizationResult:
        logger.info("ai_step=normalize_note provider=codex status=start chars=%s", len(raw_note or ""))

        codex_bin = shutil.which("codex")
        if not codex_bin:
            logger.warning("ai_step=normalize_note provider=codex status=unavailable reason=binary_missing")
            raise CodexUnavailableError(
                "Codex CLI not found on PATH. On Mac mini, install/authenticate Codex CLI "
                "and keep USE_CODEX_CLI=true. Prototype can use MockAI with USE_CODEX_CLI=false."
            )

        prompt = (
            "Normalize the following customer quotation note into a short professional "
            "Vietnamese/English summary. Return ONLY plain text summary. "
            "Do NOT invent quantity, unit price, payment terms, or products.\n\n"
            f"NOTE:\n{raw_note}"
        )
        try:
            # Integration point — real Mac mini deployment wires Codex here.
            # Probe only: prove binary discovery without requiring a full Codex session.
            completed = subprocess.run(
                [codex_bin, "--version"],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            logger.info(
                "ai_step=normalize_note provider=codex status=probe exit=%s out=%s prompt_chars=%s",
                completed.returncode,
                (completed.stdout or completed.stderr or "")[:200],
                len(prompt),
            )
            raise CodexUnavailableError(
                "Codex CLI is installed but full note-normalization invoke is not enabled "
                "in this prototype. Wire `codex exec` (or equivalent) here for production. "
                f"Prepared prompt length={len(prompt)}."
            )
        except FileNotFoundError as exc:
            raise CodexUnavailableError("Codex CLI disappeared from PATH") from exc
        except subprocess.TimeoutExpired as exc:
            raise CodexUnavailableError("Codex CLI timed out") from exc
        # Unreachable success path reserved for production wiring:
        # return NoteNormalizationResult(summary=..., tags=(), source="codex")
