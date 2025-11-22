"""Populate the pickle-backed datastore with curated German sample events."""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from classes.eventTypes import Event  # noqa: E402
from classes.ruleTypes import ConditionRule, FrequencyRule  # noqa: E402
from classes.timeUnits import TimeUnit  # noqa: E402
from config.constants import DataPaths  # noqa: E402
from handler.dataHandler import DataHandler  # noqa: E402

Definition = Dict[str, Any]


def main() -> None:
    config = buildConfig()
    handler = initDataHandler()
    events = generateEvents(config)
    persistDataset(handler, events)
    reportSuccess(events)


def buildConfig() -> Dict[str, datetime]:
    anchor = datetime.now()
    monday = resolveMonday(anchor)
    return {"anchor": anchor, "monday": monday}


def initDataHandler() -> DataHandler:
    return DataHandler()


def generateEvents(config: Dict[str, datetime]) -> List[Event]:
    sections = [
        buildDailyEvents(config),
        buildWeeklyEvents(config),
        buildMonthlyEvents(config),
        buildConditionEvents(config),
        buildFocusEvents(config),
        buildAllDayEvents(config),
    ]
    return [event for section in sections for event in section]


def buildDailyEvents(config: Dict[str, datetime]) -> List[Event]:
    definitions: List[Definition] = [
        {
            "name": "Tägliches Stand-up",
            "offset_days": 0,
            "time": (8, 45),
            "duration": durationMinutes(15),
            "rule_factory": frequencyRule("day", 1),
            "iterations": 15,
        },
        {
            "name": "Kunden-Support-Schicht",
            "offset_days": 0,
            "time": (13, 15),
            "duration": durationMinutes(60),
            "rule_factory": frequencyRule("day", 1),
            "iterations": 10,
        },
        {
            "name": "Abschlusscheck Produktion",
            "offset_days": 0,
            "time": (18, 0),
            "duration": durationMinutes(20),
            "rule_factory": frequencyRule("day", 1),
            "iterations": 12,
        },
    ]
    return buildEventsFromDefinitions(config["monday"], definitions)


def buildWeeklyEvents(config: Dict[str, datetime]) -> List[Event]:
    definitions: List[Definition] = [
        {
            "name": "Sprint Planung",
            "offset_days": 0,
            "time": (10, 0),
            "duration": durationMinutes(120),
            "rule_factory": frequencyRule("week", 1),
            "iterations": 8,
        },
        {
            "name": "Design Sync",
            "offset_days": 2,
            "time": (11, 30),
            "duration": durationMinutes(90),
            "rule_factory": frequencyRule("week", 1),
            "iterations": 8,
        },
        {
            "name": "Team Retro",
            "offset_days": 4,
            "time": (16, 0),
            "duration": durationMinutes(90),
            "rule_factory": frequencyRule("week", 1),
            "iterations": 8,
        },
    ]
    return buildEventsFromDefinitions(config["monday"], definitions)


def buildMonthlyEvents(config: Dict[str, datetime]) -> List[Event]:
    definitions: List[Definition] = [
        {
            "name": "Monatliches Steering",
            "offset_days": 1,
            "time": (9, 30),
            "duration": durationMinutes(120),
            "rule_factory": frequencyRule("month", 1),
            "iterations": 6,
        },
        {
            "name": "Budget Review",
            "offset_days": 3,
            "time": (15, 0),
            "duration": durationMinutes(60),
            "rule_factory": frequencyRule("month", 1),
            "iterations": 6,
        },
    ]
    return buildEventsFromDefinitions(config["monday"], definitions)


def buildConditionEvents(config: Dict[str, datetime]) -> List[Event]:
    definitions: List[Definition] = [
        {
            "name": "Produktionsrelease",
            "offset_days": 0,
            "time": (7, 30),
            "duration": durationMinutes(90),
            "rule_factory": conditionRule(
                reference="week",
                reference_factor=2,
                unit="day",
                unit_factor=3,
                index=2,
            ),
            "iterations": 4,
        },
        {
            "name": "Patchwelle",
            "offset_days": 1,
            "time": (19, 0),
            "duration": durationMinutes(60),
            "rule_factory": conditionRule(
                reference="week",
                reference_factor=1,
                unit="day",
                unit_factor=2,
                index=1,
            ),
            "iterations": 6,
        },
    ]
    return buildEventsFromDefinitions(config["monday"], definitions)


def buildFocusEvents(config: Dict[str, datetime]) -> List[Event]:
    definitions: List[Definition] = [
        {
            "name": "Fokusblock Architektur",
            "offset_days": 0,
            "time": (14, 0),
            "duration": durationMinutes(150),
            "iterations": 4,
        },
        {
            "name": "Bugfix-Block",
            "offset_days": 1,
            "time": (15, 30),
            "duration": durationMinutes(90),
            "iterations": 3,
        },
        {
            "name": "Research-Zeit",
            "offset_days": 3,
            "time": (9, 30),
            "duration": durationMinutes(120),
            "iterations": 2,
        },
    ]
    return buildEventsFromDefinitions(config["monday"], definitions)


def buildAllDayEvents(config: Dict[str, datetime]) -> List[Event]:
    definitions: List[Definition] = [
        {
            "name": "Team-Fokustag (Ganztägig)",
            "offset_days": 2,
            "time": (6, 0),
            "duration": durationHours(16),
            "rule_factory": frequencyRule("week", 2),
            "iterations": 6,
        },
        {
            "name": "Feiertag: Innovations-Tag",
            "offset_days": 6,
            "time": (6, 0),
            "duration": durationHours(16),
            "rule_factory": frequencyRule("month", 1),
            "iterations": 4,
        },
    ]
    return buildEventsFromDefinitions(config["monday"], definitions)


def buildEventsFromDefinitions(baseDate: datetime, definitions: List[Definition]) -> List[Event]:
    events: List[Event] = []
    for definition in definitions:
        events.append(createEventFromDefinition(baseDate, definition))
    return events


def createEventFromDefinition(baseDate: datetime, definition: Definition) -> Event:
    date = offsetDate(baseDate, definition.get("offset_days", 0))
    start = composeDatetime(date, definition["time"])
    rule = callRuleFactory(definition.get("rule_factory"))
    return createEvent(
        name=definition["name"],
        start=start,
        duration=definition["duration"],
        rule=rule,
        iterations=definition.get("iterations"),
        deadline=definition.get("deadline"),
    )


def createEvent(
    *,
    name: str,
    start: datetime,
    duration: timedelta,
    rule: FrequencyRule | ConditionRule | None,
    iterations: int | None,
    deadline: datetime | None,
) -> Event:
    return Event(
        name=name,
        startDate=start,
        duration=duration,
        rule=rule,
        iterationsRemaining=iterations,
        deadline=deadline,
    )


def persistDataset(handler: DataHandler, events: List[Event]) -> None:
    writeEvents(handler, events)
    clearCalendarState()


def writeEvents(handler: DataHandler, events: List[Event]) -> None:
    handler.events = events
    handler.rules = []
    handler.instances = []
    handler.saveData()


def reportSuccess(events: List[Event]) -> None:
    print(f"[done] Wrote {len(events)} events to {DataPaths.EVENTS.value}")
    print("       Manual calendar state cleared; launch the app to view the sample week.")


def clearCalendarState() -> None:
    state_path = Path(DataPaths.CALENDAR_STATE.value)
    try:
        if state_path.exists():
            state_path.unlink()
    except OSError as exc:
        print(f"Warning: could not remove calendar state file: {exc}")


def resolveMonday(anchor: datetime) -> datetime:
    return anchor - timedelta(days=anchor.weekday())


def offsetDate(base: datetime, days: int) -> datetime:
    return base + timedelta(days=days)


def composeDatetime(base: datetime, timeTuple: tuple[int, int]) -> datetime:
    hour, minute = timeTuple
    return base.replace(hour=hour, minute=minute, second=0, microsecond=0)


def durationMinutes(value: int) -> timedelta:
    return timedelta(minutes=value)


def durationHours(value: float) -> timedelta:
    return timedelta(hours=value)


def frequencyRule(unit: TimeUnit, rate: float) -> Callable[[], FrequencyRule]:
    def factory() -> FrequencyRule:
        return FrequencyRule(unit=unit, rate=rate)

    return factory


def conditionRule(
    *,
    reference: TimeUnit,
    reference_factor: float,
    unit: TimeUnit,
    unit_factor: float,
    index: int,
) -> Callable[[], ConditionRule]:
    def factory() -> ConditionRule:
        return ConditionRule(
            reference=reference,
            referenceFactor=reference_factor,
            unit=unit,
            unitFactor=unit_factor,
            index=index,
        )

    return factory


def callRuleFactory(
    factory: Callable[[], FrequencyRule | ConditionRule] | None,
) -> FrequencyRule | ConditionRule | None:
    if factory is None:
        return None
    return factory()


if __name__ == "__main__":
    main()
