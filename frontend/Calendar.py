"""PyQt5 calendar UI for ABCoordinator.

This module requires PyQt5 at runtime. It uses TYPE_CHECKING and Any-typed Qt objects so static
analysis tools won't raise import/type errors when PyQt5 is not present in the environment.
"""
from typing import Any, Dict, List
from datetime import datetime, timedelta

# UI constants (used for styling)
from config.constants import WINDOW_HEIGHT, WINDOW_WIDTH, BTN_BG_PRIMARY, BTN_BG_TODAY, BTN_BG_CREATE, DAY_LABEL_BG_EVEN, DAY_LABEL_BG_ODD

# Runtime import of PyQt5. Use type-ignore so linters without PyQt5 installed won't fail parsing.
try:
    from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QGridLayout, QInputDialog, QMessageBox, QSizePolicy  # type: ignore[import]
    from PyQt5.QtCore import Qt  # type: ignore[import]
except Exception as exc:  # pragma: no cover - runtime dependency
    raise ImportError("PyQt5 is required. Install it with: python -m pip install --user PyQt5") from exc

# Helper
def _get_monday(date: datetime) -> datetime:
    return date - timedelta(days=date.weekday())

class CalendarApp:
    """A simple, styled week calendar implemented with PyQt5.

    Public API: .run() -> int
    """

    def __init__(self) -> None:
        # QApplication
        self._app: Any = QApplication.instance()
        if self._app is None:
            self._app = QApplication([])

        # Main window
        self.window: Any = QWidget()
        self.window.setWindowTitle("ABCoordinator")
        self.window.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

        # State
        self.current_monday: datetime = _get_monday(datetime.today())
        self.events: Dict[str, List[str]] = {}

        # Layouts
        root_layout: Any = QVBoxLayout(self.window)
        top_bar: Any = QHBoxLayout()
        root_layout.addLayout(top_bar)

        # Header
        self.header: Any = QLabel(self._week_range_text())
        self.header.setStyleSheet("font-weight:700; font-size:16px; margin:6px 0;")
        top_bar.addWidget(self.header)
        top_bar.addStretch(1)

        # Controls
        prev_btn: Any = QPushButton("<< Prev")
        prev_btn.clicked.connect(self.prev_week)
        top_bar.addWidget(prev_btn)

        today_btn: Any = QPushButton("Today")
        today_btn.setObjectName('today')
        today_btn.clicked.connect(self.go_to_today)
        top_bar.addWidget(today_btn)

        next_btn: Any = QPushButton("Next >>")
        next_btn.clicked.connect(self.next_week)
        top_bar.addWidget(next_btn)

        create_btn: Any = QPushButton("Create Event")
        create_btn.setObjectName('create')
        create_btn.clicked.connect(self.create_event)
        top_bar.addWidget(create_btn)

        # Week grid
        self.grid: Any = QGridLayout()
        root_layout.addLayout(self.grid)

        self.day_labels: List[Any] = []
        for i in range(7):
            lbl: Any = QLabel()
            lbl.setWordWrap(True)
            color = DAY_LABEL_BG_EVEN if i % 2 == 0 else DAY_LABEL_BG_ODD
            lbl.setStyleSheet(f'background:{color}; padding:10px; border-radius:8px;')
            lbl.setMinimumWidth(120)
            lbl.setMinimumHeight(120)
            self.grid.addWidget(lbl, 0, i)
            self.day_labels.append(lbl)

        # Apply simple theme for buttons
        try:
            self._app.setStyleSheet(
                f"""
QPushButton {{ background: {BTN_BG_PRIMARY}; color: white; border-radius:6px; padding:6px 10px; }}
QPushButton#today {{ background: {BTN_BG_TODAY}; }}
QPushButton#create {{ background: {BTN_BG_CREATE}; }}
"""
            )
        except Exception:
            pass

        self.update_week()

    def _week_range_text(self) -> str:
        start = self.current_monday
        end = self.current_monday + timedelta(days=6)
        return f"Week: {start.strftime('%d %b %Y')} — {end.strftime('%d %b %Y')}"

    def update_week(self) -> None:
        self.header.setText(self._week_range_text())
        for i in range(7):
            day = self.current_monday + timedelta(days=i)
            events_list = self.events.get(day.strftime("%Y-%m-%d"), [])
            if events_list:
                events_text = "\n".join(f"• {e}" for e in events_list)
                text = f"<b>{day.strftime('%A')}</b><br><small>{day.strftime('%d %b %Y')}</small><br><br>{events_text}"
            else:
                text = f"<b>{day.strftime('%A')}</b><br><small>{day.strftime('%d %b %Y')}</small><br><br><span style='color:#777'>(no events)</span>"
            self.day_labels[i].setText(text)

    def prev_week(self) -> None:
        self.current_monday -= timedelta(days=7)
        self.update_week()

    def next_week(self) -> None:
        self.current_monday += timedelta(days=7)
        self.update_week()

    def go_to_today(self) -> None:
        self.current_monday = _get_monday(datetime.today())
        self.update_week()

    def create_event(self) -> None:
        date_str, ok = QInputDialog.getText(self.window, "Event Date", "Enter date (YYYY-MM-DD):")  # type: ignore[arg-type]
        if not ok or not date_str:
            return
        date_str = date_str.strip()
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            QMessageBox.warning(self.window, "Error", "Invalid date format")  # type: ignore[arg-type]
            return
        name, ok2 = QInputDialog.getText(self.window, "Event Name", "Enter event name:")  # type: ignore[arg-type]
        if not ok2 or not name:
            return
        self.events.setdefault(date_str, []).append(name.strip())
        self.update_week()

    def run(self) -> int:
        self.window.show()
        return self._app.exec()  # type: ignore[return-value]


def get_calendar() -> CalendarApp:
    """Factory used by entryPoint; returns a PyQt5 CalendarApp instance."""
    return CalendarApp()