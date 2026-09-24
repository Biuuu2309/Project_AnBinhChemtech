"""Mock Mac Mini automation worker — polls backend for pending quote jobs."""

from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path

import httpx

from ai.service import apply_note_only, assert_protected_fields_unchanged, normalize_quotation_note
from config import settings
from jobs.create_template import create_quotation_template
from jobs.template_service import build_field_mapping, fill_template
from jobs.validator import validate_quotation_file

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [worker] %(message)s",
)
logger = logging.getLogger("worker")


def _process_job(client: httpx.Client, job: dict) -> None:
    quotation_id = job["id"]
    customer_id = job["customer_id"]

    customer_resp = client.get(f"/api/customers/{customer_id}")
    customer_resp.raise_for_status()
    customer = customer_resp.json()

    # Optional AI step — returns a note string only; commercial fields stay on `job`
    normalized_note, ai_meta = normalize_quotation_note(job.get("note"))
    if ai_meta is not None:
        logger.info(
            "quotation_id=%s attempt_no=%s ai_note source=%s tags=%s event=ai_normalize",
            quotation_id,
            job.get("attempt_count"),
            ai_meta.source,
            list(ai_meta.tags),
        )

    job_for_doc = apply_note_only(job, normalized_note)
    assert_protected_fields_unchanged(job, job_for_doc)

    # Deterministic pipeline (mapping reads qty/price/terms from original job fields)
    mapping = build_field_mapping(job_for_doc, customer)
    output_path = Path(settings.output_dir) / f"{quotation_id}.docx"

    try:
        fill_template(Path(settings.template_path), output_path, mapping)
        validate_quotation_file(output_path)
    except Exception as exc:
        logger.error(
            "quotation_id=%s event=template_or_validate_failed error=%s",
            quotation_id,
            str(exc)[:200],
        )
        raise

    complete = client.post(
        f"/api/internal/jobs/{quotation_id}/complete",
        json={"output_path": str(output_path.resolve())},
    )
    complete.raise_for_status()
    logger.info(
        "quotation_id=%s attempt_no=%s event=completed file=%s",
        quotation_id,
        job.get("attempt_count"),
        output_path.name,
    )


def _fail_job(client: httpx.Client, quotation_id: str, error: str) -> None:
    try:
        resp = client.post(
            f"/api/internal/jobs/{quotation_id}/fail",
            json={"error_message": error[:1000]},
        )
        resp.raise_for_status()
    except Exception:
        logger.exception("Failed to report failure for %s", quotation_id)


def poll_once(client: httpx.Client) -> bool:
    resp = client.get("/api/internal/jobs/next")
    if resp.status_code == 204:
        return False
    resp.raise_for_status()
    job = resp.json()
    quotation_id = job["id"]
    logger.info("Claimed job %s (PROCESSING)", quotation_id)
    try:
        _process_job(client, job)
    except Exception as exc:
        logger.exception("Job %s failed", quotation_id)
        _fail_job(client, quotation_id, str(exc))
    return True


def run(once: bool = False) -> None:
    template = Path(settings.template_path)
    if not template.is_file():
        create_quotation_template(template)
        logger.info("Generated missing template at %s", template)

    Path(settings.output_dir).mkdir(parents=True, exist_ok=True)
    logger.info(
        "Worker ready (automation mock). backend=%s use_codex_cli=%s ai_note_enabled=%s",
        settings.backend_url,
        settings.use_codex_cli,
        settings.ai_note_enabled,
    )

    with httpx.Client(base_url=settings.backend_url, timeout=30.0) as client:
        if once:
            processed = poll_once(client)
            if not processed:
                logger.info("No pending jobs")
            return

        while True:
            try:
                poll_once(client)
            except httpx.HTTPError as exc:
                logger.warning("Backend unreachable: %s", exc)
            time.sleep(settings.worker_poll_interval)


def main() -> None:
    parser = argparse.ArgumentParser(description="Automation worker (Mock Mac mini agent)")
    parser.add_argument("--once", action="store_true", help="Process at most one job then exit")
    args = parser.parse_args()
    run(once=args.once)


if __name__ == "__main__":
    main()
