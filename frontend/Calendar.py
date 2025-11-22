from typing import Any, Dict, List, Optional, cast
from datetime import datetime, timedelta, timezone
import pickle
import os
from config.constants import (
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    BTN_BG_PRIMARY,
    BTN_BG_TODAY,
    BTN_BG_CREATE,
    DAY_LABEL_BG_EVEN,
    DAY_LABEL_BG_ODD,
    CHECK_INTERVAL,
    DataPaths,
    EVENT_COLOR_PALETTE,
    DEFAULT_EVENT_COLOR,
)
from handler.dataHandler import DataHandler
from handler.planningHandler import PlanningHandler
from classes.eventTypes import Event
from classes.ruleTypes import FrequencyRule, ConditionRule, Rule
from classes.timeUnits import TimeUnit
try:
    from PyQt5.QtWidgets import (
        QApplication,
        QWidget,
        QPushButton,
        QLabel,
        QVBoxLayout,
        QHBoxLayout,
        QScrollArea,
        QDialog,
        QLineEdit,
        QFormLayout,
        QDialogButtonBox,
        QDateEdit,
        QTimeEdit,
        QCheckBox,
        QComboBox,
        QStackedWidget,
        QSpinBox,
        QDoubleSpinBox,
        QMessageBox,
    )  # type: ignore[import]
    from PyQt5.QtCore import QTimer, Qt, QDate, QTime  # type: ignore[import]
except Exception as exc:
    raise ImportError("PyQt5 is required. Install it with: python -m pip install --user PyQt5") from exc

UTC_PLUS_1 = timezone(timedelta(hours=1))

def _resolveQtAttr(name: str, default: int) -> Any:
    """Return a Qt attribute value even if the binding exposes nested enums."""
    attr = getattr(Qt, name, None)
    if attr is not None:
        return attr
    policy = getattr(Qt, 'ScrollBarPolicy', None)
    if policy is not None:
        resolved = getattr(policy, name, None)
        if resolved is not None:
            return resolved
    return default

SCROLL_ALWAYS_OFF = _resolveQtAttr('ScrollBarAlwaysOff', 1)
SCROLL_AS_NEEDED = _resolveQtAttr('ScrollBarAsNeeded', 0)

def _resolveQtKey(name: str, default: int) -> int:
    """Return a Qt key constant with graceful fallback."""
    attr = getattr(Qt, name, None)
    if attr is not None:
        return int(attr)
    key_enum = getattr(Qt, 'Key', None)
    if key_enum is not None:
        resolved = getattr(key_enum, name, None)
        if resolved is not None:
            return int(resolved)
    return default

KEY_LEFT = _resolveQtKey('Key_Left', 0x01000012)
KEY_RIGHT = _resolveQtKey('Key_Right', 0x01000014)
KEY_T = _resolveQtKey('Key_T', ord('T'))
KEY_HOME = _resolveQtKey('Key_Home', 0x01000010)


def _normalizeColorValue(value: Optional[str]) -> str:
    """Return a sanitized #RRGGBB string or the default color."""
    if not value:
        return DEFAULT_EVENT_COLOR
    text = value.strip()
    if not text:
        return DEFAULT_EVENT_COLOR
    if not text.startswith('#'):
        text = f'#{text}'
    if len(text) == 4:
        text = '#' + ''.join(ch * 2 for ch in text[1:])
    if len(text) != 7:
        return DEFAULT_EVENT_COLOR
    try:
        int(text[1:], 16)
    except ValueError:
        return DEFAULT_EVENT_COLOR
    return text.upper()


def _hexToRgbTuple(value: Optional[str]) -> tuple[int, int, int]:
    """Convert a hex color into its RGB tuple."""
    normalized = _normalizeColorValue(value)
    return (
        int(normalized[1:3], 16),
        int(normalized[3:5], 16),
        int(normalized[5:7], 16),
    )


def _eventColorStyles(value: Optional[str]) -> Dict[str, str]:
    """Return background/border/solid colors derived from *value*."""
    r, g, b = _hexToRgbTuple(value)
    return {
        'background': f"rgba({r},{g},{b},0.18)",
        'border': f"rgba({r},{g},{b},0.65)",
        'solid': _normalizeColorValue(value),
    }

def _getNowUtc1() -> datetime:
    """Return the current UTC+1 timestamp without timezone info."""
    utc_now = datetime.now(timezone.utc)
    utc1_now = utc_now.astimezone(UTC_PLUS_1)
    return utc1_now.replace(tzinfo=None)

def _getTodayUtc1() -> datetime:
    """Return today's midnight timestamp in UTC+1."""
    return _getNowUtc1().replace(hour=0, minute=0, second=0, microsecond=0)

def _getMonday(date: datetime) -> datetime:
    """Return the monday of the provided date's week."""
    return date - timedelta(days=date.weekday())

class EventLabel(QLabel):
    def __init__(self, payload: Dict[str, Any], owner: Any, *args: Any, **kwargs: Any) -> None:
        """Store metadata payload references for later click handling."""
        super().__init__(*args, **kwargs)
        self._payload = payload
        self._owner = owner

    def mousePressEvent(self, ev: Any) -> None:
        """Delegate click handling to the calendar app when enabled."""
        if not self._payload.get('clickable', True):
            return
        try:
            self._owner.onEventClick(self._payload)
        except Exception:
            pass


class EventDialog(QDialog):
    """Dialog for creating or editing an event with optional scheduling rules."""

    _TIME_UNITS = ["second", "minute", "hour", "day", "week", "month", "year"]

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        initial_data: Optional[Dict[str, Any]] = None,
        allow_delete: bool = False,
        allow_all_day: bool = True,
    ) -> None:
        """Configure the dialog widgets and hydrate provided initial data."""
        super().__init__(parent)
        self.setWindowTitle("Create Event")
        self.setModal(True)
        self.setMinimumWidth(420)
        self.delete_requested: bool = False
        self.allow_all_day = allow_all_day

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        form_layout.addRow("Name", self.name_edit)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        today = _getTodayUtc1()
        self.date_edit.setDate(QDate(today.year, today.month, today.day))
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        form_layout.addRow("Date", self.date_edit)

        self.all_day_checkbox = QCheckBox("All-day event")
        self.all_day_checkbox.toggled.connect(self._onAllDayToggled)
        self.all_day_checkbox.setEnabled(self.allow_all_day)
        form_layout.addRow("Duration", self.all_day_checkbox)

        self.start_time_edit = QTimeEdit()
        self.start_time_edit.setDisplayFormat("HH:mm")
        self.start_time_edit.setTime(QTime(9, 0))
        form_layout.addRow("Start", self.start_time_edit)

        self.end_time_edit = QTimeEdit()
        self.end_time_edit.setDisplayFormat("HH:mm")
        self.end_time_edit.setTime(QTime(10, 0))
        form_layout.addRow("End", self.end_time_edit)

        self.color_combo = QComboBox()
        for label, hex_value in EVENT_COLOR_PALETTE:
            self.color_combo.addItem(f"{label} ({hex_value})", hex_value)
        self._selectColor(DEFAULT_EVENT_COLOR)
        form_layout.addRow("Color", self.color_combo)

        self.iterations_spin = QSpinBox()
        self.iterations_spin.setMinimum(0)
        self.iterations_spin.setMaximum(999)
        self.iterations_spin.setSpecialValueText("Unlimited")
        form_layout.addRow("Iterations", self.iterations_spin)

        self.time_remaining_spin = QDoubleSpinBox()
        self.time_remaining_spin.setDecimals(1)
        self.time_remaining_spin.setSuffix(" h")
        self.time_remaining_spin.setMinimum(0.0)
        self.time_remaining_spin.setMaximum(1000.0)
        self.time_remaining_spin.setSingleStep(0.5)
        self.time_remaining_spin.setSpecialValueText("Auto")
        form_layout.addRow("Time Remaining", self.time_remaining_spin)

        layout.addLayout(form_layout)

        rule_header = QLabel("Rule")
        rule_header.setStyleSheet("font-weight:600; margin-top:8px;")
        layout.addWidget(rule_header)

        self.rule_combo = QComboBox()
        self.rule_combo.addItems(["None", "Frequency", "Condition"])
        self.rule_combo.currentIndexChanged.connect(self._onRuleChanged)
        layout.addWidget(self.rule_combo)

        self.rule_stack = QStackedWidget()
        self.rule_stack.addWidget(QWidget())  # None
        self.rule_stack.addWidget(self._buildFrequencyPage())
        self.rule_stack.addWidget(self._buildConditionPage())
        layout.addWidget(self.rule_stack)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)  # type: ignore[attr-defined]
        self.button_box.accepted.connect(self._onAccept)
        self.button_box.rejected.connect(self.reject)

        if allow_delete:
            delete_btn = QPushButton("Delete")
            self.button_box.addButton(delete_btn, QDialogButtonBox.DestructiveRole)  # type: ignore[attr-defined]
            delete_btn.clicked.connect(self._onDelete)

        layout.addWidget(self.button_box)

        if initial_data:
            self._applyInitialData(initial_data)

        if not self.allow_all_day:
            self.all_day_checkbox.setChecked(False)
            self.start_time_edit.setEnabled(True)
            self.end_time_edit.setEnabled(True)

    def _buildFrequencyPage(self) -> QWidget:
        """Create the controls for frequency-based rules."""
        widget = QWidget()
        layout = QFormLayout(widget)

        self.freq_rate_spin = QDoubleSpinBox()
        self.freq_rate_spin.setDecimals(2)
        self.freq_rate_spin.setMinimum(0.1)
        self.freq_rate_spin.setValue(1.0)
        layout.addRow("Rate", self.freq_rate_spin)

        self.freq_unit_combo = QComboBox()
        self.freq_unit_combo.addItems([unit.title() for unit in self._TIME_UNITS])
        layout.addRow("Unit", self.freq_unit_combo)

        return widget

    def _buildConditionPage(self) -> QWidget:
        """Create the controls for condition-based rules."""
        widget = QWidget()
        layout = QFormLayout(widget)

        self.cond_reference_factor = QDoubleSpinBox()
        self.cond_reference_factor.setDecimals(2)
        self.cond_reference_factor.setMinimum(0.1)
        self.cond_reference_factor.setValue(1.0)
        layout.addRow("Reference Factor", self.cond_reference_factor)

        self.cond_reference_unit = QComboBox()
        self.cond_reference_unit.addItems([unit.title() for unit in self._TIME_UNITS])
        layout.addRow("Reference Unit", self.cond_reference_unit)

        self.cond_unit_factor = QDoubleSpinBox()
        self.cond_unit_factor.setDecimals(2)
        self.cond_unit_factor.setMinimum(0.1)
        self.cond_unit_factor.setValue(1.0)
        layout.addRow("Rule Factor", self.cond_unit_factor)

        self.cond_unit = QComboBox()
        self.cond_unit.addItems([unit.title() for unit in self._TIME_UNITS])
        layout.addRow("Rule Unit", self.cond_unit)

        self.cond_index_spin = QSpinBox()
        self.cond_index_spin.setMinimum(1)
        self.cond_index_spin.setValue(1)
        layout.addRow("Occurrence Index", self.cond_index_spin)

        return widget

    def _selectColor(self, value: Optional[str]) -> None:
        """Select the matching color entry, falling back to the default."""
        normalized = _normalizeColorValue(value)
        idx = self.color_combo.findData(normalized)
        if idx < 0:
            idx = self.color_combo.findData(DEFAULT_EVENT_COLOR)
        if idx >= 0:
            self.color_combo.setCurrentIndex(idx)

    def _onAllDayToggled(self, checked: bool) -> None:
        """Enable or disable time fields when all-day mode changes."""
        self.start_time_edit.setEnabled(not checked)
        self.end_time_edit.setEnabled(not checked)

    def _onRuleChanged(self, index: int) -> None:
        """Switch rule configuration pages to match the combo selection."""
        self.rule_stack.setCurrentIndex(index)

    def _onAccept(self) -> None:
        """Validate the dialog input before accepting the form."""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Missing Name", "Please provide an event name.")
            return

        if not self.all_day_checkbox.isChecked():
            start = self.start_time_edit.time()
            end = self.end_time_edit.time()
            if start >= end:
                QMessageBox.warning(self, "Invalid Time", "End time must be after start time.")
                return

        self.accept()

    def _onDelete(self) -> None:
        """Mark the dialog so the caller deletes the event."""
        self.delete_requested = True
        self.accept()

    def _applyInitialData(self, data: Dict[str, Any]) -> None:
        """Populate the dialog fields from an existing event payload."""
        self.setWindowTitle("Edit Event")
        self.name_edit.setText(data.get("name", ""))
        date_str = data.get("date")
        if date_str:
            try:
                parsed = datetime.strptime(date_str, "%Y-%m-%d")
                self.date_edit.setDate(QDate(parsed.year, parsed.month, parsed.day))
            except ValueError:
                pass

        all_day = bool(data.get("all_day", False)) and self.allow_all_day
        self.all_day_checkbox.setChecked(all_day)
        start_time = data.get("start_time") or "09:00"
        end_time = data.get("end_time") or "10:00"
        try:
            sh, sm = map(int, start_time.split(":"))
            eh, em = map(int, end_time.split(":"))
            self.start_time_edit.setTime(QTime(sh, sm))
            self.end_time_edit.setTime(QTime(eh, em))
        except Exception:
            pass

        iterations = data.get("iterations_remaining")
        self.iterations_spin.setValue(iterations if iterations is not None else 0)
        time_remaining = data.get("time_remaining")
        self.time_remaining_spin.setValue(time_remaining if time_remaining is not None else 0.0)

        rule = data.get("rule")
        if not rule:
            self.rule_combo.setCurrentIndex(0)
        else:
            rtype = rule.get("type")
            if rtype == "frequency":
                self.rule_combo.setCurrentIndex(1)
                self.freq_rate_spin.setValue(float(rule.get("rate", 1.0)))
                unit = rule.get("unit", "day")
                try:
                    idx = self._TIME_UNITS.index(unit)
                except ValueError:
                    idx = 3
                self.freq_unit_combo.setCurrentIndex(idx)
            elif rtype == "condition":
                self.rule_combo.setCurrentIndex(2)
                self.cond_reference_factor.setValue(float(rule.get("reference_factor", 1.0)))
                ref_unit = rule.get("reference_unit", "day")
                try:
                    ref_idx = self._TIME_UNITS.index(ref_unit)
                except ValueError:
                    ref_idx = 3
                self.cond_reference_unit.setCurrentIndex(ref_idx)
                self.cond_unit_factor.setValue(float(rule.get("unit_factor", 1.0)))
                unit = rule.get("unit", "day")
                try:
                    unit_idx = self._TIME_UNITS.index(unit)
                except ValueError:
                    unit_idx = 3
                self.cond_unit.setCurrentIndex(unit_idx)
                self.cond_index_spin.setValue(int(rule.get("index", 1)))

        self._selectColor(data.get("color"))

    def getData(self) -> Dict[str, Any]:
        """Return the sanitized dialog data for persistence or scheduling."""
        date_qt = self.date_edit.date()
        date_str = date_qt.toString("yyyy-MM-dd")
        all_day = self.all_day_checkbox.isChecked()
        start_time = None if all_day else self.start_time_edit.time().toString("HH:mm")
        end_time = None if all_day else self.end_time_edit.time().toString("HH:mm")

        rule_type = self.rule_combo.currentText().lower()
        rule_data: Optional[Dict[str, Any]] = None
        if rule_type == "frequency":
            rule_data = {
                "type": "frequency",
                "rate": float(self.freq_rate_spin.value()),
                "unit": self._TIME_UNITS[self.freq_unit_combo.currentIndex()],
            }
        elif rule_type == "condition":
            rule_data = {
                "type": "condition",
                "reference_factor": float(self.cond_reference_factor.value()),
                "reference_unit": self._TIME_UNITS[self.cond_reference_unit.currentIndex()],
                "unit_factor": float(self.cond_unit_factor.value()),
                "unit": self._TIME_UNITS[self.cond_unit.currentIndex()],
                "index": int(self.cond_index_spin.value()),
            }

        return {
            "name": self.name_edit.text().strip(),
            "date": date_str,
            "all_day": all_day,
            "start_time": start_time,
            "end_time": end_time,
            "rule": rule_data,
            "color": _normalizeColorValue(cast(Optional[str], self.color_combo.currentData())),
            "iterations_remaining": int(self.iterations_spin.value()) or None,
            "time_remaining": float(self.time_remaining_spin.value()) if self.time_remaining_spin.value() > 0 else None,
        }

class CalendarApp:
    def __init__(self, planning_handler: Optional[Any] = None, data_handler: Optional[DataHandler] = None) -> None:
        """Bootstrap the calendar UI, data handlers, and timers."""
        self.app: Any = self._ensureApplication()
        self.window: Any = self._createWindow()
        self._initializeHandlers(planning_handler, data_handler)
        self._initializeStateStores()
        self._buildInterface()
        self._applyGlobalStyle()
        self._configureTimers()
        self._hydrateInitialData()
        self.updateWeek()
        self._setupBackgroundRefresh()

    def _ensureApplication(self) -> Any:
        """Return a QApplication instance, creating one if necessary."""
        existing = QApplication.instance()
        return existing if existing is not None else QApplication([])

    def _createWindow(self) -> QWidget:
        """Create the main window and wire high-level event handlers."""
        window = QWidget()
        window.setWindowTitle("ABCoordinator")
        window.resize(WINDOW_WIDTH, WINDOW_HEIGHT + 200)
        window.resizeEvent = self._onWindowResize  # type: ignore[assignment]
        window.keyPressEvent = self._handleWindowKeyPress  # type: ignore[assignment]
        return window

    def _initializeHandlers(self, planning_handler: Optional[Any], data_handler: Optional[DataHandler]) -> None:
        """Store handler references for scheduling and persistence."""
        self.planning_handler = planning_handler
        self.data_handler = data_handler

    def _initializeStateStores(self) -> None:
        """Prepare mutable state containers required by the UI."""
        self.current_monday = _getMonday(_getTodayUtc1())
        self.events: Dict[str, List[Dict[str, Any]]] = {}
        self.scheduled_events: Dict[str, List[Dict[str, Any]]] = {}
        self._data_watch_timer: Optional[Any] = None
        self._events_mtime: Optional[float] = None

    def _buildInterface(self) -> None:
        """Assemble the layout, including toolbar and scrollable week view."""
        root_layout: Any = QVBoxLayout(self.window)
        root_layout.addLayout(self._buildTopBar())
        middle_layout: Any = QHBoxLayout()
        root_layout.addLayout(middle_layout)
        self._buildWeekArea(middle_layout)

    def _buildTopBar(self) -> QHBoxLayout:
        """Build the top bar with navigation and creation controls."""
        top_bar: Any = QHBoxLayout()
        self.header = QLabel(self._weekRangeText())
        self.header.setStyleSheet("font-weight:700; font-size:16px; margin:6px 0;")
        top_bar.addWidget(self.header)
        top_bar.addStretch(1)
        prev_btn: Any = QPushButton("<< Prev")
        prev_btn.clicked.connect(self.prevWeek)
        top_bar.addWidget(prev_btn)
        today_btn: Any = QPushButton("Today")
        today_btn.setObjectName('today')
        today_btn.clicked.connect(self.goToToday)
        top_bar.addWidget(today_btn)
        next_btn: Any = QPushButton("Next >>")
        next_btn.clicked.connect(self.nextWeek)
        top_bar.addWidget(next_btn)
        create_btn: Any = QPushButton("Create Event")
        create_btn.setObjectName('create')
        create_btn.clicked.connect(self.createEvent)
        top_bar.addWidget(create_btn)
        return top_bar

    def _buildWeekArea(self, middle_layout: Any) -> None:
        """Create the timeline legend and the seven day columns."""
        self.ALLDAY_AREA_HEIGHT = 220
        self.HOUR_HEIGHT = 150
        time_widget: Any = QWidget()
        time_widget.setMinimumWidth(92)
        time_widget.setMaximumWidth(92)
        self.time_widget = time_widget
        time_layout: Any = QVBoxLayout(time_widget)
        time_layout.setSpacing(6)
        time_layout.setContentsMargins(4, 4, 4, 4)
        spacer_top: Any = QWidget()
        spacer_top.setMinimumHeight(self.ALLDAY_AREA_HEIGHT)
        spacer_top.setMaximumHeight(self.ALLDAY_AREA_HEIGHT)
        self._time_spacer = spacer_top
        time_layout.addWidget(spacer_top)
        for hour in range(24):
            utc1_hour = (hour + 1) % 24
            tl = QLabel(f"{utc1_hour:02d}:00")
            tl.setStyleSheet("color:#555; padding:6px; font-family:monospace;")
            tl.setMinimumHeight(self.HOUR_HEIGHT)
            tl.setMaximumHeight(self.HOUR_HEIGHT)
            time_layout.addWidget(tl)
        time_layout.addStretch(0)

        week_widget: Any = QWidget()
        week_layout: Any = QHBoxLayout(week_widget)
        week_layout.setSpacing(8)
        self.day_widgets: List[Any] = []
        self.day_all_day_containers: List[Any] = []
        self.day_timed_containers: List[Any] = []
        self.day_timeline_scrolls: List[Any] = []
        self.day_timeline_widgets: List[Any] = []
        self.day_current_lines: List[Any] = []
        for index in range(7):
            day_widget: Any = QWidget()
            day_layout: Any = QVBoxLayout(day_widget)
            day_layout.setContentsMargins(6, 6, 6, 6)
            all_day_container: Any = QWidget()
            all_day_layout: Any = QVBoxLayout(all_day_container)
            all_day_layout.setContentsMargins(0, 0, 0, 0)
            all_day_container.setMinimumHeight(self.ALLDAY_AREA_HEIGHT)
            all_day_container.setMaximumHeight(self.ALLDAY_AREA_HEIGHT)
            all_day_layout.addStretch(0)
            day_layout.addWidget(all_day_container)
            timed_container: Any = QWidget()
            timed_layout: Any = QVBoxLayout(timed_container)
            timed_layout.setContentsMargins(0, 0, 0, 0)
            timed_layout.setSpacing(0)
            timeline_widget: Any = QWidget()
            timeline_widget.setMinimumHeight(self.HOUR_HEIGHT * 24)
            timeline_scroll: Any = QScrollArea()
            timeline_scroll.setWidgetResizable(True)
            timeline_scroll.setHorizontalScrollBarPolicy(SCROLL_ALWAYS_OFF)
            timeline_scroll.setVerticalScrollBarPolicy(SCROLL_AS_NEEDED)
            timeline_scroll.setWidget(timeline_widget)
            timed_layout.addWidget(timeline_scroll)
            day_layout.addWidget(timed_container)
            day_widget.setStyleSheet(
                f"background:{DAY_LABEL_BG_EVEN if index % 2 == 0 else DAY_LABEL_BG_ODD}; border-radius:8px; padding:6px;"
            )
            day_widget.setMinimumWidth(160)
            week_layout.addWidget(day_widget, 1)
            self.day_widgets.append(day_widget)
            self.day_all_day_containers.append(all_day_layout)
            self.day_timed_containers.append(timed_layout)
            self.day_timeline_scrolls.append(timeline_scroll)
            self.day_timeline_widgets.append(timeline_widget)
            line_widget = QWidget(timeline_widget)
            line_widget.setObjectName('current_line')
            line_widget.setStyleSheet('background: #E53935; border: none;')
            line_widget.setFixedHeight(2)
            line_widget.hide()
            self.day_current_lines.append(line_widget)

        content_widget: Any = QWidget()
        content_layout: Any = QHBoxLayout(content_widget)
        content_layout.setSpacing(8)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(time_widget, 0)
        content_layout.addWidget(week_widget, 1)
        scroll: Any = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content_widget)
        middle_layout.addWidget(scroll, stretch=1)
        self._left_time_line = QWidget(self.time_widget)
        self._left_time_line.setStyleSheet('background: #E53935; border: none;')
        self._left_time_line.setFixedHeight(2)
        self._left_time_line.hide()

    def _applyGlobalStyle(self) -> None:
        """Apply a lightweight stylesheet without failing hard."""
        try:
            self.app.setStyleSheet(
                f"""
QPushButton {{ background: {BTN_BG_PRIMARY}; color: white; border-radius:6px; padding:6px 10px; }}
QPushButton#today {{ background: {BTN_BG_TODAY}; }}
QPushButton#create {{ background: {BTN_BG_CREATE}; }}
"""
            )
        except Exception:
            pass

    def _configureTimers(self) -> None:
        """Start periodic updates for the current time indicator."""
        self._timer = QTimer()
        self._timer.timeout.connect(self._updateCurrentLines)
        self._timer.start(60 * 1000)
        QTimer.singleShot(0, self._updateCurrentLines)

    def _hydrateInitialData(self) -> None:
        """Load scheduled and manual events from disk or the planner."""
        if self.planning_handler is not None:
            self._loadEventsFromHandler()
        elif self.data_handler is not None and self.data_handler.events:
            self._rebuildSchedule(show_error=False)
        self._loadCalendarState()

    def _handleWindowKeyPress(self, event: Any) -> None:
        """Add keyboard shortcuts for week navigation."""
        key = event.key()
        if key == KEY_LEFT:
            self.prevWeek()
            event.accept()
            return
        if key == KEY_RIGHT:
            self.nextWeek()
            event.accept()
            return
        if key in (KEY_T, KEY_HOME):
            self.goToToday()
            event.accept()
            return
        QWidget.keyPressEvent(self.window, event)

    @staticmethod
    def _formatNumber(value: Any) -> str:
        """Format numeric-like values while trimming redundant decimals."""
        try:
            number = float(value)
            if number.is_integer():
                return str(int(number))
            return f"{number:.2f}".rstrip('0').rstrip('.')
        except (TypeError, ValueError):
            return str(value)

    @classmethod
    def _formatRuleSummary(cls, rule: Optional[Dict[str, Any]]) -> str:
        """Return a short textual summary for a scheduling rule."""
        if not rule:
            return ""
        rtype = rule.get("type")
        if rtype == "frequency":
            rate = cls._formatNumber(rule.get("rate", 1))
            unit = rule.get("unit", "")
            return f"  · Every {rate} {unit}(s)"
        if rtype == "condition":
            ref_factor = cls._formatNumber(rule.get("reference_factor", 1))
            ref_unit = rule.get("reference_unit", "")
            unit_factor = cls._formatNumber(rule.get("unit_factor", 1))
            unit = rule.get("unit", "")
            index = rule.get("index", 1)
            return (
                f"  · After {ref_factor} {ref_unit}(s), every {unit_factor} {unit}(s), occurrence {index}"
            )
        return ""

    @staticmethod
    def _serializeRule(rule: Optional[Rule]) -> Optional[Dict[str, Any]]:
        """Convert a rule object into a serializable dictionary."""
        if isinstance(rule, FrequencyRule):
            return {
                "type": "frequency",
                "unit": rule.unit,
                "rate": rule.rate,
            }
        if isinstance(rule, ConditionRule):
            return {
                "type": "condition",
                "reference_unit": rule.reference,
                "reference_factor": rule.referenceFactor,
                "unit": rule.unit,
                "unit_factor": rule.unitFactor,
                "index": rule.index,
            }
        return None

    @staticmethod
    def _buildRuleObject(rule_data: Optional[Dict[str, Any]]) -> Optional[Rule]:
        """Recreate a rule object from the dialog payload."""
        if not rule_data:
            return None
        rtype = rule_data.get("type")
        if rtype == "frequency":
            unit = cast(TimeUnit, rule_data.get("unit", "day"))
            rate = float(rule_data.get("rate", 1.0))
            return FrequencyRule(unit, rate)
        if rtype == "condition":
            reference_unit = cast(TimeUnit, rule_data.get("reference_unit", "day"))
            reference_factor = float(rule_data.get("reference_factor", 1.0))
            unit = cast(TimeUnit, rule_data.get("unit", "day"))
            unit_factor = float(rule_data.get("unit_factor", 1.0))
            index = int(rule_data.get("index", 1))
            return ConditionRule(reference_unit, reference_factor, unit, unit_factor, index)
        return None

    def _buildEventFromDialog(self, event_data: Dict[str, Any]) -> Event:
        """Convert dialog data into a schedulable Event instance."""
        start_time = event_data.get('start_time')
        end_time = event_data.get('end_time')
        if start_time is None or end_time is None:
            raise ValueError("Automatic scheduling requires a start and end time.")

        try:
            start_dt = datetime.strptime(f"{event_data['date']} {start_time}", "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(f"{event_data['date']} {end_time}", "%Y-%m-%d %H:%M")
        except ValueError as exc:
            raise ValueError("Could not parse start/end times.") from exc

        duration = end_dt - start_dt
        if duration.total_seconds() <= 0:
            raise ValueError("End time must be after start time for scheduling.")

        rule_obj = self._buildRuleObject(event_data.get('rule'))
        time_remaining = event_data.get('time_remaining')
        if time_remaining is None or time_remaining <= 0:
            time_remaining = duration.total_seconds() / 3600.0
        iterations_remaining = event_data.get('iterations_remaining')
        color = _normalizeColorValue(event_data.get('color'))

        return Event(
            name=event_data['name'],
            startDate=start_dt,
            duration=duration,
            rule=rule_obj,
            timeRemaining=time_remaining,
            iterationsRemaining=iterations_remaining,
            color=color,
        )

    def _workdayDuration(self) -> timedelta:
        """Return the effective workday span used for all-day detection."""
        if self.planning_handler is not None:
            start = getattr(self.planning_handler, 'dayStartHour', 6)
            end = getattr(self.planning_handler, 'dayEndHour', 22)
            span = end - start if end > start else (24 - start + end)
            span = max(1, span)
            return timedelta(hours=span)
        return timedelta(hours=16)

    def _isAllDayScheduled(self, scheduled: Any) -> bool:
        """Determine whether a scheduled event spans the full workday."""
        event = getattr(scheduled, 'event', None)
        duration = getattr(event, 'duration', None)
        if duration is None:
            return False
        return duration >= self._workdayDuration()

    def _onWindowResize(self, event: Any) -> None:
        """Handle window resize events."""
        QWidget.resizeEvent(self.window, event)
        QTimer.singleShot(0, self._relayoutEventWidgets)

    def _relayoutEventWidgets(self) -> None:
        """Reposition event widgets when timeline width changes."""
        for tl in self.day_timeline_widgets:
            w = tl.width()
            for child in tl.findChildren(QLabel):
                geom = child.geometry()
                try:
                    child.setGeometry(4, geom.y(), max(80, w - 8), geom.height())
                except Exception:
                    pass

    def _loadEventsFromHandler(self) -> None:
        """Load scheduled events from the planning handler into the calendar."""
        self.scheduled_events = {}
        if self.planning_handler is None:
            return

        for date_key, scheduled_events in self.planning_handler.scheduledDays.items():
            date_str = date_key.strftime("%Y-%m-%d")
            for scheduled in scheduled_events:
                event = scheduled.event
                scheduled_time = scheduled.scheduledTime
                end_time = scheduled.endTime
                is_all_day = self._isAllDayScheduled(scheduled)
                start_time_str = None if is_all_day else scheduled_time.strftime("%H:%M")
                end_time_str = None if is_all_day else end_time.strftime("%H:%M")
                ev_dict: Dict[str, Any] = {
                    'name': event.name,
                    'time': start_time_str,
                    'end_time': end_time_str,
                    'all_day': is_all_day,
                    'rule': self._serializeRule(event.rule),
                    'color': _normalizeColorValue(getattr(event, 'color', None)),
                    'source': 'scheduled',
                    'clickable': True,
                    'date': date_str,
                    'event_obj': event,
                    'scheduled_ref': scheduled,
                    'scheduled_start': scheduled_time,
                    'scheduled_end': end_time,
                }
                self.scheduled_events.setdefault(date_str, []).append(ev_dict)

    def _rebuildSchedule(self, show_error: bool = True) -> bool:
        """Recreate the planner schedule and refresh cached events."""
        if self.data_handler is None:
            return False
        try:
            self.planning_handler = PlanningHandler(self.data_handler.events)
        except Exception as exc:
            if show_error:
                QMessageBox.critical(self.window, "Scheduling Failed", f"{exc}")
            else:
                print(f"Warning: could not rebuild schedule: {exc}")
            return False
        self._loadEventsFromHandler()
        return True
    def _loadCalendarState(self) -> None:
        """Load saved calendar state from pickle file."""
        try:
            if os.path.exists(DataPaths.CALENDAR_STATE.value):
                with open(DataPaths.CALENDAR_STATE.value, 'rb') as f:
                    saved_events = pickle.load(f)
                    for date_str, event_list in saved_events.items():
                        normalized: List[Dict[str, Any]] = []
                        for saved_ev in event_list:
                            if not isinstance(saved_ev, dict):
                                continue
                            saved_dict: Dict[str, Any] = dict(cast(Dict[str, Any], saved_ev))
                            saved_dict.setdefault('source', 'manual')
                            saved_dict.setdefault('clickable', True)
                            saved_dict.setdefault('date', date_str)
                            saved_dict['color'] = _normalizeColorValue(saved_dict.get('color'))
                            normalized.append(saved_dict)
                        target = self.events.setdefault(date_str, [])
                        for saved_ev in normalized:
                            if saved_ev not in target:
                                target.append(saved_ev)
        except Exception as e:
            print(f"Warning: Could not load calendar state: {e}")
    
    def _saveCalendarState(self) -> None:
        """Save current calendar state to pickle file."""
        try:
            os.makedirs(os.path.dirname(DataPaths.CALENDAR_STATE.value), exist_ok=True)
            with open(DataPaths.CALENDAR_STATE.value, 'wb') as f:
                pickle.dump(self.events, f)
        except Exception as e:
            print(f"Warning: Could not save calendar state: {e}")

    def _storeManualEvent(self, event_data: Dict[str, Any]) -> None:
        """Persist a manual event into the local calendar cache."""
        date_key = event_data['date']
        record: Dict[str, Any] = {
            'name': event_data['name'],
            'time': event_data['start_time'],
            'end_time': event_data['end_time'],
            'all_day': event_data['all_day'],
            'rule': event_data.get('rule'),
            'color': _normalizeColorValue(event_data.get('color')),
            'source': 'manual',
            'clickable': True,
            'date': date_key,
        }
        self.events.setdefault(date_key, []).append(record)
        self._saveCalendarState()
        self.updateWeek()
    
    def _weekRangeText(self) -> str:
        """Return a friendly string describing the visible week."""
        start = self.current_monday
        end = self.current_monday + timedelta(days=6)
        return f"Week: {start.strftime('%d %b %Y')} — {end.strftime('%d %b %Y') }"
    def updateWeek(self) -> None:
        """Re-render the entire week grid based on cached data."""
        self.header.setText(self._weekRangeText())
        for i in range(7):
            day_dt = self.current_monday + timedelta(days=i)
            date = day_dt.strftime("%Y-%m-%d")
            all_layout = self.day_all_day_containers[i]
            while all_layout.count() > 0:
                item = all_layout.takeAt(0)
                w = item.widget()
                if w is not None:
                    w.setParent(None)
            date_lbl = QLabel(f"<b>{day_dt.strftime('%A %d %b %Y')}</b>")
            date_lbl.setStyleSheet('font-size:16px; margin-bottom:6px;')
            all_layout.addWidget(date_lbl)
            allday_lbl = QLabel('<b>All-day</b>')
            all_layout.addWidget(allday_lbl)
            manual_events = self.events.get(date, [])
            scheduled_events = self.scheduled_events.get(date, [])
            manual_all_day = [e for e in manual_events if e.get('all_day')]
            scheduled_all_day = [e for e in scheduled_events if e.get('all_day')]
            all_day_items = manual_all_day + scheduled_all_day
            if all_day_items:
                for ev in all_day_items:
                    summary = self._formatRuleSummary(ev.get('rule'))
                    label_prefix = "•"
                    if ev.get('source') == 'scheduled':
                        label_prefix = "• [Auto]"
                    payload: Dict[str, Any] = {
                        'date': date,
                        'event': ev,
                        'event_obj': ev.get('event_obj'),
                        'scheduled_ref': ev.get('scheduled_ref'),
                        'source': ev.get('source', 'manual'),
                        'clickable': ev.get('clickable', True),
                    }
                    lbl = EventLabel(payload, self, f"{label_prefix} {ev.get('name')}{summary}")
                    styles = _eventColorStyles(ev.get('color'))
                    lbl.setStyleSheet(
                        f"font-weight:600; padding:2px 0; border-left:4px solid {styles['solid']}; padding-left:6px;"
                    )
                    all_layout.addWidget(lbl)
            else:
                none_lbl = QLabel("(no all-day events)")
                none_lbl.setStyleSheet('color:#777;')
                all_layout.addWidget(none_lbl)
            timeline_widget = self.day_timeline_widgets[i]
            for child in timeline_widget.findChildren(QWidget):
                if child.objectName() == 'current_line':
                    continue
                child.setParent(None)
            manual_timed = [e for e in manual_events if not e.get('all_day')]
            scheduled_timed = [e for e in scheduled_events if not e.get('all_day')]
            combined_events = scheduled_timed + manual_timed
            if combined_events:
                def _timeKey(ev: Dict[str, Any]) -> int:
                    """Return the minute offset used to sort timed events."""
                    t = ev.get('time') or '00:00'
                    try:
                        hh, mm = map(int, t.split(':'))
                        return hh*60 + mm
                    except Exception:
                        return 0
                combined_events.sort(key=_timeKey)
                for ev in combined_events:
                    start = ev.get('time') or '00:00'
                    end = ev.get('end_time') or start
                    name = ev.get('name')
                    summary = self._formatRuleSummary(ev.get('rule'))
                    try:
                        sh, sm = map(int, start.split(':'))
                        eh, em = map(int, end.split(':'))
                        start_min = max(0, min(24*60, sh*60 + sm))
                        end_min = max(0, min(24*60, eh*60 + em))
                    except Exception:
                        start_min = 0
                        end_min = 0
                    if end_min <= start_min:
                        end_min = start_min + 30
                    y = int((start_min / 60.0) * self.HOUR_HEIGHT)
                    height_px = max(18, int(((end_min - start_min) / 60.0) * self.HOUR_HEIGHT))
                    payload: Dict[str, Any] = {
                        'date': date,
                        'event': ev,
                        'event_obj': ev.get('event_obj'),
                        'scheduled_ref': ev.get('scheduled_ref'),
                        'source': ev.get('source', 'manual'),
                        'clickable': ev.get('clickable', ev.get('source', 'manual') == 'manual'),
                    }
                    ev_widget = EventLabel(payload, self, timeline_widget)
                    ev_widget.setText(f"{start} — {end}  {name}{summary}")
                    styles = _eventColorStyles(ev.get('color'))
                    ev_widget.setStyleSheet(
                        f"background: {styles['background']}; border-left: 4px solid {styles['border']}; border-radius:6px; padding:6px; color:#111;"
                    )
                    ev_widget.setWordWrap(True)
                    ev_widget.setGeometry(4, y, max(80, timeline_widget.width() - 8), height_px)
                    ev_widget.show()
        
        QTimer.singleShot(50, self._relayoutEventWidgets)

    def prevWeek(self) -> None:
        """Navigate one week backward."""
        self.current_monday -= timedelta(days=7)
        self.updateWeek()

    def nextWeek(self) -> None:
        """Navigate one week forward."""
        self.current_monday += timedelta(days=7)
        self.updateWeek()

    def goToToday(self) -> None:
        """Jump to the current week."""
        self.current_monday = _getMonday(_getTodayUtc1())
        self.updateWeek()

    def createEvent(self) -> None:
        """Open the dialog for creating a manual or scheduled event."""
        dialog = EventDialog(self.window)
        if dialog.exec_() != QDialog.Accepted:  # type: ignore[attr-defined]
            return

        event_data = dialog.getData()
        if event_data['all_day'] or self.data_handler is None:
            self._storeManualEvent(event_data)
            return

        try:
            event_obj = self._buildEventFromDialog(event_data)
        except ValueError as exc:
            QMessageBox.warning(self.window, "Invalid Event", str(exc))
            self._storeManualEvent(event_data)
            return

        self.data_handler.events.append(event_obj)
        try:
            self.data_handler.saveData()
        except Exception as exc:
            self.data_handler.events.pop()
            QMessageBox.critical(self.window, "Save Failed", f"Could not store event: {exc}")
            return

        rebuilt = self._rebuildSchedule(show_error=True)
        if not rebuilt:
            try:
                self.data_handler.events.remove(event_obj)
                self.data_handler.saveData()
            except Exception:
                pass
            self._storeManualEvent(event_data)
            return

        self.updateWeek()

    def _updateCurrentLines(self) -> None:
         """Update the current time indicator line."""
         now = _getNowUtc1()
         today = now.date()
         current_min = now.hour * 60 + now.minute
         if not self.day_timeline_widgets:
             return

         ratio = current_min / (24.0 * 60.0)
         default_timeline_height = self.HOUR_HEIGHT * 24

         for idx in range(7):
             day_date = (self.current_monday + timedelta(days=idx)).date()
             line = self.day_current_lines[idx]
             tl = self.day_timeline_widgets[idx]
             tl_height = tl.height() if tl.height() > 0 else default_timeline_height
             y_tl = int(ratio * tl_height)

             if day_date == today:
                 line.setGeometry(0, y_tl, tl.width(), 2)
                 line.raise_()
                 line.show()

                 spacer = getattr(self, '_time_spacer', None)
                 top_in_time = spacer.height() if spacer is not None else self.ALLDAY_AREA_HEIGHT
                 time_widget_height = self.time_widget.height() - top_in_time
                 if time_widget_height <= 0:
                     time_widget_height = default_timeline_height
                 y_left = top_in_time + int(ratio * time_widget_height)
                 self._left_time_line.setGeometry(0, y_left, self.time_widget.width(), 2)
                 self._left_time_line.raise_()
                 self._left_time_line.show()
             else:
                 line.hide()

    def _setupBackgroundRefresh(self) -> None:
        """Start background polling for persisted event changes."""
        if self.data_handler is None:
            return
        interval_ms = int(max(1, CHECK_INTERVAL.total_seconds()) * 1000)
        self._events_mtime = self._currentEventsMtime()
        self._data_watch_timer = QTimer()
        self._data_watch_timer.setInterval(interval_ms)
        self._data_watch_timer.timeout.connect(self._backgroundRefreshTick)
        self._data_watch_timer.start()

    @staticmethod
    def _currentEventsMtime() -> Optional[float]:
        """Return the modification timestamp for the events file."""
        try:
            return os.path.getmtime(DataPaths.EVENTS.value)
        except OSError:
            return None

    def _backgroundRefreshTick(self) -> None:
        """Reload data when the underlying pickles change on disk."""
        if self.data_handler is None:
            return
        current_mtime = self._currentEventsMtime()
        if current_mtime is None:
            return
        if self._events_mtime is not None and current_mtime <= self._events_mtime:
            return
        self._events_mtime = current_mtime
        try:
            self.data_handler.loadData()
        except Exception as exc:
            print(f"Warning: background refresh failed: {exc}")
            return
        self._rebuildSchedule(show_error=False)
        self.updateWeek()
    
    def onEventClick(self, payload: Dict[str, Any]) -> None:
        """Route click events to the correct handler by source type."""
        source = payload.get('source')
        if source == 'manual':
            self._handleManualEventClick(payload)
        elif source == 'scheduled':
            self._handleScheduledEventClick(payload)

    def _handleManualEventClick(self, payload: Dict[str, Any]) -> None:
        """Open the editor dialog for a manual UI-created event."""
        date = payload.get('date')
        event_ref = payload.get('event')
        if not date or not isinstance(event_ref, dict):
            return

        event_ref_dict = cast(Dict[str, Any], event_ref)

        dialog = EventDialog(
            self.window,
            initial_data=self._buildManualEventDialogData(date, event_ref_dict),
            allow_delete=True,
        )
        result = dialog.exec_()

        if dialog.delete_requested:
            self._removeManualEvent(date, event_ref_dict)
            return

        if result != QDialog.Accepted:  # type: ignore[attr-defined]
            return

        updated = dialog.getData()
        self._applyManualEventUpdate(date, event_ref_dict, updated)

    def _buildManualEventDialogData(self, date: str, event_ref: Dict[str, Any]) -> Dict[str, Any]:
        """Return the dialog payload for a manual event reference."""
        return {
            'name': event_ref.get('name', ''),
            'date': date,
            'all_day': event_ref.get('all_day', False),
            'start_time': event_ref.get('time'),
            'end_time': event_ref.get('end_time'),
            'rule': event_ref.get('rule'),
            'color': _normalizeColorValue(event_ref.get('color')),
        }

    def _applyManualEventUpdate(
        self,
        original_date: str,
        original_event: Dict[str, Any],
        updated: Dict[str, Any],
    ) -> None:
        """Persist user edits made to a manual event."""
        new_record: Dict[str, Any] = {
            'name': updated['name'],
            'time': updated['start_time'],
            'end_time': updated['end_time'],
            'all_day': updated['all_day'],
            'rule': updated.get('rule'),
            'color': _normalizeColorValue(updated.get('color')),
            'source': 'manual',
            'clickable': True,
            'date': updated['date'],
        }

        if updated['date'] != original_date:
            bucket = self.events.get(original_date, [])
            if original_event in bucket:
                bucket.remove(original_event)
                if not bucket:
                    self.events.pop(original_date, None)
            self.events.setdefault(updated['date'], []).append(new_record)
        else:
            original_event.clear()
            original_event.update(new_record)

        self._saveCalendarState()
        self.updateWeek()

    def _removeManualEvent(self, date: str, event_ref: Dict[str, Any]) -> None:
        """Delete a manual event from the calendar cache."""
        try:
            evs = self.events.get(date, [])
            if event_ref in evs:
                evs.remove(event_ref)
                if not evs:
                    self.events.pop(date, None)
        except Exception:
            pass
        self._saveCalendarState()
        self.updateWeek()

    def _handleScheduledEventClick(self, payload: Dict[str, Any]) -> None:
        """Open the editor dialog for an auto-scheduled event."""
        if self.data_handler is None:
            QMessageBox.information(self.window, "Unavailable", "Editing scheduled events requires persistent storage.")
            return

        event_obj = payload.get('event_obj')
        event_meta = payload.get('event')
        if not isinstance(event_obj, Event):
            return

        dialog = EventDialog(
            self.window,
            initial_data=self._buildScheduledDialogData(event_obj, event_meta),
            allow_delete=True,
            allow_all_day=False,
        )
        result = dialog.exec_()

        if dialog.delete_requested:
            self._deletePlannedEvent(event_obj)
            return

        if result != QDialog.Accepted:  # type: ignore[attr-defined]
            return

        event_data = dialog.getData()
        try:
            updated_event = self._buildEventFromDialog(event_data)
        except ValueError as exc:
            QMessageBox.warning(self.window, "Invalid Event", str(exc))
            return

        self._applyEventUpdates(event_obj, updated_event)
        try:
            self.data_handler.saveData()
        except Exception as exc:
            QMessageBox.critical(self.window, "Save Failed", f"Could not update event: {exc}")
            return

        self._rebuildSchedule(show_error=True)
        self.updateWeek()

    def _buildScheduledDialogData(self, event_obj: Event, event_meta: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Return dialog-ready data for a scheduled Event object."""
        start_dt = event_obj.startDate
        end_dt = start_dt + (event_obj.duration or timedelta(hours=1))
        if event_meta:
            scheduled_start = event_meta.get('scheduled_start')
            scheduled_end = event_meta.get('scheduled_end')
            if isinstance(scheduled_start, datetime):
                start_dt = scheduled_start
            if isinstance(scheduled_end, datetime):
                end_dt = scheduled_end

        return {
            'name': event_obj.name,
            'date': start_dt.strftime("%Y-%m-%d"),
            'all_day': False,
            'start_time': start_dt.strftime("%H:%M"),
            'end_time': end_dt.strftime("%H:%M"),
            'rule': self._serializeRule(event_obj.rule),
            'color': _normalizeColorValue(event_meta.get('color') if event_meta else getattr(event_obj, 'color', None)),
            'iterations_remaining': event_obj.iterationsRemaining,
            'time_remaining': event_obj.timeRemaining,
        }

    def _deletePlannedEvent(self, event_obj: Event) -> None:
        """Remove a persisted planned event and refresh the schedule."""
        try:
            if self.data_handler and event_obj in self.data_handler.events:
                self.data_handler.events.remove(event_obj)
                self.data_handler.saveData()
        except Exception as exc:
            QMessageBox.critical(self.window, "Delete Failed", f"Could not delete event: {exc}")
            return
        self._rebuildSchedule(show_error=True)
        self.updateWeek()

    @staticmethod
    def _applyEventUpdates(target: Event, source: Event) -> None:
        """Copy editable fields from one Event into another."""
        target.name = source.name
        target.startDate = source.startDate
        target.duration = source.duration
        target.rule = source.rule
        target.timeRemaining = source.timeRemaining
        target.iterationsRemaining = source.iterationsRemaining
        target.color = source.color

    def run(self) -> int:
        """Start the Qt event loop and persist state before exit."""
        self.window.show()
        result = self.app.exec()
        self._saveCalendarState()
        return result


def getCalendar(planning_handler: Optional[Any] = None, data_handler: Optional[DataHandler] = None) -> CalendarApp:
    """Create and return a CalendarApp instance."""
    return CalendarApp(planning_handler=planning_handler, data_handler=data_handler)