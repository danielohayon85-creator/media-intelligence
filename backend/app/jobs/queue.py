"""תור עיבוד פשוט (in-process, thread-based) לניתוח AI אסינכרוני של פריטים
שנקלטו. זו נקודת הרחבה: Interface זהה (enqueue_analysis) יכול בהמשך לדחוף
ל-Redis/RQ/Celery בלי לשנות את שאר המערכת (סעיף 2 במפרט: Background Jobs)."""

import logging
import queue
import threading

logger = logging.getLogger(__name__)

_queue: "queue.Queue[str]" = queue.Queue()
_worker_thread: threading.Thread | None = None


def _worker_loop() -> None:
    from app.jobs.analysis_worker import analyze_item_by_id

    while True:
        item_id = _queue.get()
        try:
            analyze_item_by_id(item_id)
        except Exception:  # noqa: BLE001
            logger.exception("Failed to analyze item %s", item_id)
        finally:
            _queue.task_done()


def start_worker() -> None:
    global _worker_thread
    if _worker_thread is not None and _worker_thread.is_alive():
        return
    _worker_thread = threading.Thread(target=_worker_loop, daemon=True, name="analysis-worker")
    _worker_thread.start()


def enqueue_analysis(item_ids: list[str]) -> None:
    start_worker()
    for item_id in item_ids:
        _queue.put(item_id)


def pending_count() -> int:
    return _queue.qsize()
