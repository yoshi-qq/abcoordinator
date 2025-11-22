"""Populate the pickle-backed datastore with curated German sample events."""
from __future__ import annotations

from datetime import datetime, timedelta
from itertools import cycle
from pathlib import Path
from typing import Any, Callable, Dict, List
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from classes.eventTypes import Event  # noqa: E402
from classes.ruleTypes import ConditionRule, FrequencyRule  # noqa: E402
from classes.timeUnits import TimeUnit  # noqa: E402
from config.constants import DataPaths, EVENT_COLOR_PALETTE, DEFAULT_EVENT_COLOR  # noqa: E402
from handler.dataHandler import DataHandler  # noqa: E402

Definition = Dict[str, Any]
COLOR_VALUES: List[str] = [hex_code for _, hex_code in EVENT_COLOR_PALETTE]
_COLOR_CYCLE = cycle(COLOR_VALUES)


def nextColor() -> str:
    """Return the next color in the palette, falling back to the default."""
    try:
        return next(_COLOR_CYCLE)
    except StopIteration:
        return DEFAULT_EVENT_COLOR


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
        buildWeeklyEventsA(config),
        buildWeeklyEventsB(config),
        buildMonthlyEvents(config),
        buildConditionEvents(config),
        buildFocusEvents(config),
        buildAllDayEvents(config),
    ]
    return [event for section in sections for event in section]


def buildDailyEvents(config: Dict[str, datetime]) -> List[Event]:
    definitions: List[Definition] = [
        {
            "name": "Schlafenszeit (Abend)",
            "offset_days": 0,
            "time": (21, 30),
            "duration": durationMinutes(149),
            "rule_factory": frequencyRule("day", 1),
            "iterations": 20,
        },
        {
            "name": "Schlafenszeit (Früh)",
            "offset_days": 0,
            "time": (0, 0),
            "duration": durationMinutes(405),
            "rule_factory": frequencyRule("day", 1),
            "iterations": 20,
        },
        {
            "name": "Frühstück & Schulweg",
            "offset_days": 0,
            "time": (6, 45),
            "duration": durationMinutes(45),
            "rule_factory": frequencyRule("day", 1),
            "iterations": 20,
        },
    ]
    return buildEventsFromDefinitions(config["monday"], definitions)


def buildWeeklyEventsA(config: Dict[str, datetime]) -> List[Event]:
    definitions: List[Definition] = [
        # Montag: Profilkurs
        {
            "name": "Unterricht Block 1 (Mo)",
            "offset_days": 0,
            "time": (8, 0),
            "duration": durationMinutes(90),
            "iterations": 1,
        },
        {
            "name": "Pause (Mo)",
            "offset_days": 0,
            "time": (9, 30),
            "duration": durationMinutes(15),
            "iterations": 1,
        },
        {
            "name": "Unterricht Block 2 (Mo)",
            "offset_days": 0,
            "time": (9, 45),
            "duration": durationMinutes(90),
            "iterations": 1,
        },
        {
            "name": "Mittagspause (Mo)",
            "offset_days": 0,
            "time": (11, 15),
            "duration": durationMinutes(45),
            "iterations": 1,
        },
        {
            "name": "Unterricht Block 3 (Mo)",
            "offset_days": 0,
            "time": (12, 0),
            "duration": durationMinutes(90),
            "iterations": 1,
        },
        {
            "name": "Profilkurs Chemie-Labor",
            "offset_days": 0,
            "time": (14, 0),
            "duration": durationMinutes(90),
            "rule_factory": frequencyRule("week", 1),
            "iterations": 10,
        },
        {
            "name": "Hausaufgaben (Mo)",
            "offset_days": 0,
            "time": (16, 30),
            "duration": durationMinutes(90),
            "iterations": 1,
        },
        # Dienstag: Fußballtraining
        {
            "name": "Unterricht Block 1 (Di)",
            "offset_days": 1,
            "time": (8, 0),
            "duration": durationMinutes(135),
            "iterations": 1,
        },
        {
            "name": "Große Pause (Di)",
            "offset_days": 1,
            "time": (10, 15),
            "duration": durationMinutes(30),
            "iterations": 1,
        },
        {
            "name": "Unterricht Block 2 (Di)",
            "offset_days": 1,
            "time": (10, 45),
            "duration": durationMinutes(90),
            "iterations": 1,
        },
        {
            "name": "Mittagspause (Di)",
            "offset_days": 1,
            "time": (12, 15),
            "duration": durationMinutes(45),
            "iterations": 1,
        },
        {
            "name": "Unterricht Block 3 (Di)",
            "offset_days": 1,
            "time": (13, 0),
            "duration": durationMinutes(120),
            "iterations": 1,
        },
        {
            "name": "Freistunde (Di)",
            "offset_days": 1,
            "time": (15, 0),
            "duration": durationMinutes(60),
            "iterations": 1,
        },
        {
            "name": "Hausaufgaben kurz (Di)",
            "offset_days": 1,
            "time": (16, 0),
            "duration": durationMinutes(60),
            "iterations": 1,
        },
        {
            "name": "Vereinstraining Fußball",
            "offset_days": 1,
            "time": (17, 30),
            "duration": durationMinutes(120),
            "rule_factory": frequencyRule("week", 1),
            "iterations": 10,
        },

        # Mittwoch: Lange mitMusikschule
        {
            "name": "Unterricht Block 1 (Mi)",
            "offset_days": 2,
            "time": (8, 0),
            "duration": durationMinutes(90),
            "iterations": 1,
        },
        {
            "name": "Kurze Pause (Mi)",
            "offset_days": 2,
            "time": (9, 30),
            "duration": durationMinutes(10),
            "iterations": 1,
        },
        {
            "name": "Unterricht Block 2 (Mi)",
            "offset_days": 2,
            "time": (9, 40),
            "duration": durationMinutes(90),
            "iterations": 1,
        },
        {
            "name": "Mittagspause (Mi)",
            "offset_days": 2,
            "time": (11, 10),
            "duration": durationMinutes(50),
            "iterations": 1,
        },
        {
            "name": "Unterricht Block 3 (Mi)",
            "offset_days": 2,
            "time": (12, 0),
            "duration": durationMinutes(135),
            "iterations": 1,
        },
        {
            "name": "Arbeitsgemeinschaft (Mi)",
            "offset_days": 2,
            "time": (14, 15),
            "duration": durationMinutes(75),
            "iterations": 1,
        },
        {
            "name": "Musikschule (Klavier)",
            "offset_days": 2,
            "time": (16, 0),
            "duration": durationMinutes(60),
            "rule_factory": frequencyRule("week", 1),
            "iterations": 10,
        },
        {
            "name": "Hausaufgaben (Mi)",
            "offset_days": 2,
            "time": (17, 30),
            "duration": durationMinutes(90),
            "iterations": 1,
        },

        # Donnerstag: Nachhilfe
        {
            "name": "Unterricht Block 1 (Do)",
            "offset_days": 3,
            "time": (8, 0),
            "duration": durationMinutes(120),
            "iterations": 1,
        },
        {
            "name": "Pause (Do)",
            "offset_days": 3,
            "time": (10, 0),
            "duration": durationMinutes(20),
            "iterations": 1,
        },
        {
            "name": "Unterricht Block 2 (Do)",
            "offset_days": 3,
            "time": (10, 20),
            "duration": durationMinutes(90),
            "iterations": 1,
        },
        {
            "name": "Mittagspause (Do)",
            "offset_days": 3,
            "time": (11, 50),
            "duration": durationMinutes(40),
            "iterations": 1,
        },
        {
            "name": "Unterricht Block 3 (Do)",
            "offset_days": 3,
            "time": (12, 30),
            "duration": durationMinutes(105),
            "iterations": 1,
        },
        {
            "name": "Lernzeit betreut (Do)",
            "offset_days": 3,
            "time": (14, 15),
            "duration": durationMinutes(60),
            "iterations": 1,
        },
        {
            "name": "Freistunde (Do)",
            "offset_days": 3,
            "time": (15, 15),
            "duration": durationMinutes(45),
            "iterations": 1,
        },
        {
            "name": "Hausaufgaben (Do)",
            "offset_days": 3,
            "time": (16, 30),
            "duration": durationMinutes(60),
            "iterations": 1,
        },
        {
            "name": "Nachhilfe Mathematik",
            "offset_days": 3,
            "time": (18, 0),
            "duration": durationMinutes(75),
            "rule_factory": frequencyRule("week", 1),
            "iterations": 10,
        },

        # Freitag: Kurz mit Jugendtreff
        {
            "name": "Unterricht Block 1 (Fr)",
            "offset_days": 4,
            "time": (8, 0),
            "duration": durationMinutes(90),
            "iterations": 1,
        },
        {
            "name": "Pause (Fr)",
            "offset_days": 4,
            "time": (9, 30),
            "duration": durationMinutes(15),
            "iterations": 1,
        },
        {
            "name": "Unterricht Block 2 (Fr)",
            "offset_days": 4,
            "time": (9, 45),
            "duration": durationMinutes(90),
            "iterations": 1,
        },
        {
            "name": "Mittagspause (Fr)",
            "offset_days": 4,
            "time": (11, 15),
            "duration": durationMinutes(45),
            "iterations": 1,
        },
        {
            "name": "Unterricht Block 3 (Fr)",
            "offset_days": 4,
            "time": (12, 0),
            "duration": durationMinutes(90),
            "iterations": 1,
        },
        {
            "name": "Hausaufgaben Wochenende (Fr)",
            "offset_days": 4,
            "time": (14, 0),
            "duration": durationMinutes(90),
            "iterations": 1,
        },
        {
            "name": "Freie Zeit (Fr)",
            "offset_days": 4,
            "time": (16, 0),
            "duration": durationMinutes(120),
            "iterations": 1,
        },
        {
            "name": "Jugendtreff & Ehrenamt",
            "offset_days": 4,
            "time": (19, 0),
            "duration": durationMinutes(120),
            "rule_factory": frequencyRule("week", 1),
            "iterations": 10,
        },

        # Samstag: Freizeit
        {
            "name": "Ausschlafen (Sa)",
            "offset_days": 5,
            "time": (9, 0),
            "duration": durationMinutes(60),
            "iterations": 1,
        },
        {
            "name": "Freizeit im Park",
            "offset_days": 5,
            "time": (11, 0),
            "duration": durationMinutes(120),
            "rule_factory": frequencyRule("week", 1),
            "iterations": 10,
        },
        {
            "name": "Mittagessen Familie (Sa)",
            "offset_days": 5,
            "time": (13, 0),
            "duration": durationMinutes(60),
            "iterations": 1,
        },
        {
            "name": "Freie Zeit Nachmittag (Sa)",
            "offset_days": 5,
            "time": (14, 30),
            "duration": durationMinutes(180),
            "iterations": 1,
        },
        # Sonntag: Entspannung
        {
            "name": "Familienfrühstück (So)",
            "offset_days": 6,
            "time": (10, 0),
            "duration": durationMinutes(90),
            "iterations": 1,
        },
        {
            "name": "Freie Zeit Vormittag (So)",
            "offset_days": 6,
            "time": (12, 0),
            "duration": durationMinutes(120),
            "iterations": 1,
        },
        {
            "name": "Sonntagsspaziergang",
            "offset_days": 6,
            "time": (14, 30),
            "duration": durationMinutes(90),
            "iterations": 1,
        },
        {
            "name": "Familienabend & Spiele",
            "offset_days": 6,
            "time": (17, 0),
            "duration": durationMinutes(150),
            "rule_factory": frequencyRule("week", 1),
            "iterations": 10,
        },
        {
            "name": "Vorbereitung Schulwoche (So)",
            "offset_days": 6,
            "time": (19, 30),
            "duration": durationMinutes(60),
            "iterations": 1,
        },
    ]
    return buildEventsFromDefinitions(config["monday"], definitions)


def buildWeeklyEventsB(config: Dict[str, datetime]) -> List[Event]:
    """Alternative Woche B mit anderen Unterrichtszeiten und Aktivitäten."""
    monday_week_b = config["monday"] + timedelta(days=7)
    definitions: List[Definition] = [
        # Montag Woche B: Andere Verteilung
        {
            "name": "Unterricht Block 1 (Mo-B)",
            "offset_days": 0,
            "time": (8, 0),
            "duration": durationMinutes(105),
            "iterations": 1,
        },
        {
            "name": "Pause (Mo-B)",
            "offset_days": 0,
            "time": (9, 45),
            "duration": durationMinutes(20),
            "iterations": 1,
        },
        {
            "name": "Unterricht Block 2 (Mo-B)",
            "offset_days": 0,
            "time": (10, 5),
            "duration": durationMinutes(90),
            "iterations": 1,
        },
        {
            "name": "Mittagspause (Mo-B)",
            "offset_days": 0,
            "time": (11, 35),
            "duration": durationMinutes(50),
            "iterations": 1,
        },
        {
            "name": "Unterricht Block 3 (Mo-B)",
            "offset_days": 0,
            "time": (12, 25),
            "duration": durationMinutes(90),
            "iterations": 1,
        },
        {
            "name": "Profilkurs Chemie-Labor",
            "offset_days": 0,
            "time": (14, 0),
            "duration": durationMinutes(90),
            "rule_factory": frequencyRule("week", 2),
            "iterations": 5,
        },
        {
            "name": "Freistunde (Mo-B)",
            "offset_days": 0,
            "time": (15, 45),
            "duration": durationMinutes(60),
            "iterations": 1,
        },
        {
            "name": "Hausaufgaben (Mo-B)",
            "offset_days": 0,
            "time": (17, 0),
            "duration": durationMinutes(75),
            "iterations": 1,
        },

        # Dienstag Woche B
        {
            "name": "Unterricht Block 1 (Di-B)",
            "offset_days": 1,
            "time": (8, 0),
            "duration": durationMinutes(120),
            "iterations": 1,
        },
        {
            "name": "Pause (Di-B)",
            "offset_days": 1,
            "time": (10, 0),
            "duration": durationMinutes(25),
            "iterations": 1,
        },
        {
            "name": "Unterricht Block 2 (Di-B)",
            "offset_days": 1,
            "time": (10, 25),
            "duration": durationMinutes(105),
            "iterations": 1,
        },
        {
            "name": "Mittagspause (Di-B)",
            "offset_days": 1,
            "time": (12, 10),
            "duration": durationMinutes(50),
            "iterations": 1,
        },
        {
            "name": "Unterricht Block 3 (Di-B)",
            "offset_days": 1,
            "time": (13, 0),
            "duration": durationMinutes(90),
            "iterations": 1,
        },
        {
            "name": "AG Robotik (Di-B)",
            "offset_days": 1,
            "time": (14, 45),
            "duration": durationMinutes(90),
            "iterations": 1,
        },
        {
            "name": "Hausaufgaben (Di-B)",
            "offset_days": 1,
            "time": (16, 15),
            "duration": durationMinutes(60),
            "iterations": 1,
        },
        {
            "name": "Vereinstraining Fußball",
            "offset_days": 1,
            "time": (17, 30),
            "duration": durationMinutes(120),
            "rule_factory": frequencyRule("week", 2),
            "iterations": 5,
        },

        # Mittwoch Woche B
        {
            "name": "Unterricht Block 1 (Mi-B)",
            "offset_days": 2,
            "time": (8, 0),
            "duration": durationMinutes(105),
            "iterations": 1,
        },
        {
            "name": "Pause (Mi-B)",
            "offset_days": 2,
            "time": (9, 45),
            "duration": durationMinutes(15),
            "iterations": 1,
        },
        {
            "name": "Unterricht Block 2 (Mi-B)",
            "offset_days": 2,
            "time": (10, 0),
            "duration": durationMinutes(90),
            "iterations": 1,
        },
        {
            "name": "Mittagspause (Mi-B)",
            "offset_days": 2,
            "time": (11, 30),
            "duration": durationMinutes(45),
            "iterations": 1,
        },
        {
            "name": "Unterricht Block 3 (Mi-B)",
            "offset_days": 2,
            "time": (12, 15),
            "duration": durationMinutes(120),
            "iterations": 1,
        },
        {
            "name": "Freistunde (Mi-B)",
            "offset_days": 2,
            "time": (14, 15),
            "duration": durationMinutes(45),
            "iterations": 1,
        },
        {
            "name": "Musikschule (Klavier)",
            "offset_days": 2,
            "time": (16, 0),
            "duration": durationMinutes(60),
            "rule_factory": frequencyRule("week", 2),
            "iterations": 5,
        },
        {
            "name": "Hausaufgaben (Mi-B)",
            "offset_days": 2,
            "time": (17, 30),
            "duration": durationMinutes(90),
            "iterations": 1,
        },

        # Donnerstag Woche B
        {
            "name": "Unterricht Block 1 (Do-B)",
            "offset_days": 3,
            "time": (8, 0),
            "duration": durationMinutes(90),
            "iterations": 1,
        },
        {
            "name": "Kurze Pause (Do-B)",
            "offset_days": 3,
            "time": (9, 30),
            "duration": durationMinutes(10),
            "iterations": 1,
        },
        {
            "name": "Unterricht Block 2 (Do-B)",
            "offset_days": 3,
            "time": (9, 40),
            "duration": durationMinutes(105),
            "iterations": 1,
        },
        {
            "name": "Mittagspause (Do-B)",
            "offset_days": 3,
            "time": (11, 25),
            "duration": durationMinutes(50),
            "iterations": 1,
        },
        {
            "name": "Unterricht Block 3 (Do-B)",
            "offset_days": 3,
            "time": (12, 15),
            "duration": durationMinutes(120),
            "iterations": 1,
        },
        {
            "name": "Bibliothek (Do-B)",
            "offset_days": 3,
            "time": (14, 30),
            "duration": durationMinutes(75),
            "iterations": 1,
        },
        {
            "name": "Hausaufgaben (Do-B)",
            "offset_days": 3,
            "time": (16, 15),
            "duration": durationMinutes(75),
            "iterations": 1,
        },
        {
            "name": "Nachhilfe Mathematik",
            "offset_days": 3,
            "time": (18, 0),
            "duration": durationMinutes(75),
            "rule_factory": frequencyRule("week", 2),
            "iterations": 5,
        },

        # Freitag Woche B
        {
            "name": "Unterricht Block 1 (Fr-B)",
            "offset_days": 4,
            "time": (8, 0),
            "duration": durationMinutes(105),
            "iterations": 1,
        },
        {
            "name": "Pause (Fr-B)",
            "offset_days": 4,
            "time": (9, 45),
            "duration": durationMinutes(20),
            "iterations": 1,
        },
        {
            "name": "Unterricht Block 2 (Fr-B)",
            "offset_days": 4,
            "time": (10, 5),
            "duration": durationMinutes(90),
            "iterations": 1,
        },
        {
            "name": "Mittagspause (Fr-B)",
            "offset_days": 4,
            "time": (11, 35),
            "duration": durationMinutes(40),
            "iterations": 1,
        },
        {
            "name": "Unterricht Block 3 (Fr-B)",
            "offset_days": 4,
            "time": (12, 15),
            "duration": durationMinutes(75),
            "iterations": 1,
        },
        {
            "name": "Klassenprojekt (Fr-B)",
            "offset_days": 4,
            "time": (13, 45),
            "duration": durationMinutes(90),
            "iterations": 1,
        },
        {
            "name": "Freie Zeit (Fr-B)",
            "offset_days": 4,
            "time": (15, 30),
            "duration": durationMinutes(150),
            "iterations": 1,
        },
        {
            "name": "Jugendtreff & Ehrenamt",
            "offset_days": 4,
            "time": (19, 0),
            "duration": durationMinutes(120),
            "rule_factory": frequencyRule("week", 2),
            "iterations": 5,
        },

        # Samstag Woche B
        {
            "name": "Sport & Fitness (Sa-B)",
            "offset_days": 5,
            "time": (10, 0),
            "duration": durationMinutes(90),
            "iterations": 1,
        },
        {
            "name": "Freizeit im Park",
            "offset_days": 5,
            "time": (11, 30),
            "duration": durationMinutes(120),
            "rule_factory": frequencyRule("week", 2),
            "iterations": 5,
        },
        {
            "name": "Mittagessen (Sa-B)",
            "offset_days": 5,
            "time": (13, 30),
            "duration": durationMinutes(45),
            "iterations": 1,
        },
        {
            "name": "Freunde treffen (Sa-B)",
            "offset_days": 5,
            "time": (14, 45),
            "duration": durationMinutes(180),
            "iterations": 1,
        },

        # Sonntag Woche B
        {
            "name": "Familienfrühstück (So-B)",
            "offset_days": 6,
            "time": (9, 30),
            "duration": durationMinutes(75),
            "iterations": 1,
        },
        {
            "name": "Hobby-Zeit (So-B)",
            "offset_days": 6,
            "time": (11, 30),
            "duration": durationMinutes(150),
            "iterations": 1,
        },
        {
            "name": "Familienausflug (So-B)",
            "offset_days": 6,
            "time": (14, 30),
            "duration": durationMinutes(120),
            "iterations": 1,
        },
        {
            "name": "Familienabend & Spiele",
            "offset_days": 6,
            "time": (17, 0),
            "duration": durationMinutes(150),
            "rule_factory": frequencyRule("week", 2),
            "iterations": 5,
        },
        {
            "name": "Schulvorbereitung (So-B)",
            "offset_days": 6,
            "time": (19, 45),
            "duration": durationMinutes(45),
            "iterations": 1,
        },
    ]
    return buildEventsFromDefinitions(monday_week_b, definitions)


def buildMonthlyEvents(config: Dict[str, datetime]) -> List[Event]:
    definitions: List[Definition] = [
        {
            "name": "Elternabend & Klassenrat",
            "offset_days": 2,
            "time": (18, 30),
            "duration": durationMinutes(120),
            "rule_factory": frequencyRule("month", 1),
            "iterations": 6,
        },
        {
            "name": "Projektpräsentation im Kurs",
            "offset_days": 4,
            "time": (10, 0),
            "duration": durationMinutes(90),
            "rule_factory": frequencyRule("month", 1),
            "iterations": 6,
        },
        {
            "name": "Schulbücherei-Volunteer",
            "offset_days": 0,
            "time": (15, 30),
            "duration": durationMinutes(120),
            "rule_factory": frequencyRule("month", 1),
            "iterations": 6,
        },
    ]
    return buildEventsFromDefinitions(config["monday"], definitions)


def buildConditionEvents(config: Dict[str, datetime]) -> List[Event]:
    definitions: List[Definition] = [
        {
            "name": "Vokabeltest Englisch",
            "offset_days": 0,
            "time": (9, 0),
            "duration": durationMinutes(45),
            "rule_factory": conditionRule(
                reference="week",
                reference_factor=2,
                unit="day",
                unit_factor=5,
                index=1,
            ),
            "iterations": 4,
        },
        {
            "name": "Klassenarbeit Vorbereitung",
            "offset_days": 1,
            "time": (16, 30),
            "duration": durationMinutes(120),
            "rule_factory": conditionRule(
                reference="week",
                reference_factor=3,
                unit="day",
                unit_factor=2,
                index=2,
            ),
            "iterations": 4,
        },
    ]
    return buildEventsFromDefinitions(config["monday"], definitions)


def buildFocusEvents(config: Dict[str, datetime]) -> List[Event]:
    definitions: List[Definition] = [
        {
            "name": "Lerncamp Abitur",
            "offset_days": 0,
            "time": (14, 30),
            "duration": durationMinutes(150),
            "iterations": 4,
        },
        {
            "name": "Gruppenarbeit Science-Fair",
            "offset_days": 2,
            "time": (15, 30),
            "duration": durationMinutes(120),
            "iterations": 3,
        },
        {
            "name": "Selbstständige Recherche",
            "offset_days": 4,
            "time": (10, 0),
            "duration": durationMinutes(120),
            "iterations": 2,
        },
    ]
    return buildEventsFromDefinitions(config["monday"], definitions)


def buildAllDayEvents(config: Dict[str, datetime]) -> List[Event]:
    definitions: List[Definition] = [
        {
            "name": "Projekttag Nachhaltigkeit",
            "offset_days": 1,
            "time": (6, 0),
            "duration": durationHours(16),
            "rule_factory": frequencyRule("week", 2),
            "iterations": 4,
        },
        {
            "name": "Ferientag / beweglicher Feiertag",
            "offset_days": 5,
            "time": (6, 0),
            "duration": durationHours(16),
            "rule_factory": frequencyRule("month", 1),
            "iterations": 3,
        },
        {
            "name": "Klassenfahrt (Vorbereitungstag)",
            "offset_days": 6,
            "time": (6, 0),
            "duration": durationHours(16),
            "rule_factory": frequencyRule("month", 2),
            "iterations": 2,
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
        color=definition.get("color") or nextColor(),
    )


def createEvent(
    *,
    name: str,
    start: datetime,
    duration: timedelta,
    rule: FrequencyRule | ConditionRule | None,
    iterations: int | None,
    deadline: datetime | None,
    color: str | None,
) -> Event:
    return Event(
        name=name,
        startDate=start,
        duration=duration,
        rule=rule,
        iterationsRemaining=iterations,
        deadline=deadline,
        color=color,
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
