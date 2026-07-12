"""Worker de procesamiento asíncrono — no bloqueante para el ERP."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zovrake_motor.enterprise_integration.apqm.queue_manager import AsyncProcessingQueueManager


class AsyncQueueWorker:
    """
    Worker in-process para procesamiento concurrente.

    Preparado para múltiples workers sin modificar el núcleo del APQM.
    """

    def __init__(
        self,
        manager: AsyncProcessingQueueManager,
        *,
        max_concurrent_workers: int = 10,
    ) -> None:
        self._manager = manager
        self._semaphore = threading.Semaphore(max_concurrent_workers)
        self._lock = threading.Lock()

    def schedule_item(self, item_id: str) -> None:
        thread = threading.Thread(
            target=self._run_item,
            args=(item_id,),
            daemon=True,
            name=f"apqm-worker-{item_id[:8]}",
        )
        thread.start()

    def _run_item(self, item_id: str) -> None:
        with self._semaphore:
            self._manager.execute_item(item_id)

    def process_pending_synchronously(self) -> int:
        """Procesa ítems pendientes en el hilo actual — útil para pruebas determinísticas."""
        processed = 0
        while True:
            item_id = self._manager.next_pending_item_id()
            if item_id is None:
                break
            self._manager.execute_item(item_id)
            processed += 1
        return processed
