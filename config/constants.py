from datetime import timedelta
from enum import Enum

WINDOW_WIDTH = 900
WINDOW_HEIGHT = 400
BG_TOP_FRAME = "#f0f0f0"
BTN_BG_PRIMARY = "#4a90e2"
BTN_BG_TODAY = "#7ed321"
BTN_BG_CREATE = "#f5a623"
BTN_FG = "white"
DAY_LABEL_BG_ODD = "#ffffff"
DAY_LABEL_BG_EVEN = "#e6f2ff"
DAY_LABEL_FG = "#333333"
DAY_LABEL_FONT = ("Arial", 10, "bold")
DAY_LABEL_WIDTH = 12
DAY_LABEL_HEIGHT = 8


CUTOFF_DISTANCE: timedelta = timedelta(days=30)
CHECK_INTERVAL: timedelta = timedelta(minutes=15)


class DataPaths(Enum):
	EVENTS = 'data/events.pkl'
	RULES = 'data/rules.pkl'
	INSTANCES = 'data/instances.pkl'
	CALENDAR_STATE = 'data/calendar_state.pkl'