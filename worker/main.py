"""Mock Mac Mini worker — polls backend for pending quote jobs."""

from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path

import httpx

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

    if settings.use_codex_cli:
        logger.warning("USE_CODEX_CLI=true but Codex is stubbed; using deterministic fill")

    mapping = build_field_mapping(job, customer)
    output_path = Path(settings.output_dir) / f"{quotation_id}.docx"

    fill_template(Path(settings.template_path), output_path, mapping)
    validate_quotation_file(output_path)

    complete = client.post(
        f"/api/internal/jobs/{quotation_id}/complete",
        json={"output_path": str(output_path.resolve())},
    )
    complete.raise_for_status()
    logger.info("Completed %s -> %s", quotation_id, output_path)


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
        "Worker ready (Mock Mac Mini). backend=%s template=%s output=%s",
        settings.backend_url,
        settings.template_path,
        settings.output_dir,
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
    parser = argparse.ArgumentParser(description="Mock Mac Mini quotation worker")
    parser.add_argument("--once", action="store_true", help="Process at most one job then exit")
    args = parser.parse_args()
    run(once=args.once)


if __name__ == "__main__":
    main()
