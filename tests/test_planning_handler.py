"""Unit tests for the planning handler."""
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timedelta
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from classes.eventTypes import Event  # noqa: E402
from classes.ruleTypes import FrequencyRule  # noqa: E402
from handler.planningHandler import PlanningHandler  # noqa: E402


class PlanningHandlerTests(unittest.TestCase):
    def test_monthly_frequency_tracks_real_calendar(self) -> None:
        start = datetime(2024, 1, 31, 9, 0)
        recurring = Event(
            name="Month End Review",
            startDate=start,
            duration=timedelta(hours=1),
            rule=FrequencyRule('month', 1),
            iterationsRemaining=3,
        )

        handler = PlanningHandler([recurring])
        dates = sorted(handler.days.keys())
        formatted = [d.strftime("%Y-%m-%d") for d in dates]

        self.assertEqual(formatted, ["2024-01-31", "2024-02-29", "2024-03-31"])

    def test_yearly_frequency_handles_leap_year_rollover(self) -> None:
        start = datetime(2020, 2, 29, 10, 0)
        yearly = Event(
            name="Leap Anniversary",
            startDate=start,
            duration=timedelta(hours=2),
            rule=FrequencyRule('year', 1),
            iterationsRemaining=2,
        )

        handler = PlanningHandler([yearly])
        dates = sorted(handler.days.keys())

        self.assertEqual([d.strftime("%Y-%m-%d") for d in dates], ["2020-02-29", "2021-02-28"])


if __name__ == '__main__':
    unittest.main()
