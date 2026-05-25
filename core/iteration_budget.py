"""Iteration Budget — prevents runaway agent loops.

Tracks remaining tool-call budget and emits warnings as the agent
approaches its limit. Hard-stops when budget reaches zero.
"""

import logging

logger = logging.getLogger(__name__)


class BudgetExhaustedError(Exception):
    """Raised when the agent's iteration budget is exhausted."""
    pass


class IterationBudget:
    """Tracks tool-call budget for a single agent run.

    Parameters
    ----------
    max_iterations : int
        Maximum number of tool-calling turns allowed.
    warning_thresholds : list[int]
        Remaining-turn counts at which to emit warnings.
    """

    def __init__(self, max_iterations: int = 90, warning_thresholds=None):
        self.max_iterations = max_iterations
        self.remaining = max_iterations
        if warning_thresholds is None:
            self.warning_thresholds = [10, 5, 1]
        else:
            self.warning_thresholds = sorted(warning_thresholds)
        self._warned = set()

    def consume(self) -> str | None:
        """Consume one turn from the budget.

        Returns a warning string if a threshold was crossed, otherwise None.
        Raises BudgetExhaustedError if budget is exhausted.
        """
        self.remaining -= 1

        if self.remaining in self.warning_thresholds and self.remaining not in self._warned:
            self._warned.add(self.remaining)
            msg = f"WARNING: {self.remaining} tool-call turns remaining before hard stop."
            logger.warning(msg)
            return msg

        if self.remaining <= 0:
            raise BudgetExhaustedError(
                f"Iteration budget exhausted (max={self.max_iterations}). "
                "The agent has made too many tool calls. Consider breaking your "
                "request into smaller sub-tasks."
            )

        return None

    def is_exhausted(self) -> bool:
        return self.remaining <= 0

    def pct_remaining(self) -> float:
        return self.remaining / max(self.max_iterations, 1)
