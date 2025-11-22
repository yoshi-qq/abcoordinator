from typing import Any, Dict, List, Optional, cast
from datetime import datetime, timedelta, timezone
import pickle
import os
from config.constants import WINDOW_HEIGHT, WINDOW_WIDTH, BTN_BG_PRIMARY, BTN_BG_TODAY, BTN_BG_CREATE, DAY_LABEL_BG_EVEN, DAY_LABEL_BG_ODD, DataPaths
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

# UTC+1 timezone
UTC_PLUS_1 = timezone(timedelta(hours=1))

def _get_now_utc1() -> datetime:
    """Get current time in UTC+1 timezone."""
    # Get UTC time and convert to UTC+1
    utc_now = datetime.now(timezone.utc)
    utc1_now = utc_now.astimezone(UTC_PLUS_1)
    # Return as naive datetime for consistency with rest of code
    return utc1_now.replace(tzinfo=None)

def _get_today_utc1() -> datetime:
    """Get today's date in UTC+1 timezone."""
    return _get_now_utc1().replace(hour=0, minute=0, second=0, microsecond=0)

def _get_monday(date: datetime) -> datetime:
    return date - timedelta(days=date.weekday())

class EventLabel(QLabel):
    def __init__(self, payload: Dict[str, Any], owner: Any, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._payload = payload
        self._owner = owner

    def mousePressEvent(self, ev: Any) -> None:
        if not self._payload.get('clickable', True):
            return
        try:
            self._owner.on_event_click(self._payload)
        except Exception:
            pass


class EventDialog(QDialog):
    """Dialog for creating an event with optional scheduling rules."""

    _TIME_UNITS = ["second", "minute", "hour", "day", "week", "month", "year"]

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Create Event")
        self.setModal(True)
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        form_layout.addRow("Name", self.name_edit)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        today = _get_today_utc1()
        self.date_edit.setDate(QDate(today.year, today.month, today.day))
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        form_layout.addRow("Date", self.date_edit)

        self.all_day_checkbox = QCheckBox("All-day event")
        self.all_day_checkbox.toggled.connect(self._on_all_day_toggled)
        form_layout.addRow("Duration", self.all_day_checkbox)

        self.start_time_edit = QTimeEdit()
        self.start_time_edit.setDisplayFormat("HH:mm")
        self.start_time_edit.setTime(QTime(9, 0))
        form_layout.addRow("Start", self.start_time_edit)

        self.end_time_edit = QTimeEdit()
        self.end_time_edit.setDisplayFormat("HH:mm")
        self.end_time_edit.setTime(QTime(10, 0))
        form_layout.addRow("End", self.end_time_edit)

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
        self.rule_combo.currentIndexChanged.connect(self._on_rule_changed)
        layout.addWidget(self.rule_combo)

        self.rule_stack = QStackedWidget()
        self.rule_stack.addWidget(QWidget())  # None
        self.rule_stack.addWidget(self._build_frequency_page())
        self.rule_stack.addWidget(self._build_condition_page())
        layout.addWidget(self.rule_stack)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)  # type: ignore[attr-defined]
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _build_frequency_page(self) -> QWidget:
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

    def _build_condition_page(self) -> QWidget:
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

    def _on_all_day_toggled(self, checked: bool) -> None:
        self.start_time_edit.setEnabled(not checked)
        self.end_time_edit.setEnabled(not checked)

    def _on_rule_changed(self, index: int) -> None:
        self.rule_stack.setCurrentIndex(index)

    def _on_accept(self) -> None:
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

    def get_data(self) -> Dict[str, Any]:
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
            "iterations_remaining": int(self.iterations_spin.value()) or None,
            "time_remaining": float(self.time_remaining_spin.value()) if self.time_remaining_spin.value() > 0 else None,
        }

class CalendarApp:
    def __init__(self, planning_handler: Optional[Any] = None, data_handler: Optional[DataHandler] = None) -> None:
        self.app: Any = QApplication.instance()
        if self.app is None:
            self.app = QApplication([])
        self.window: Any = QWidget()
        self.window.setWindowTitle("ABCoordinator")
        self.window.resize(WINDOW_WIDTH, WINDOW_HEIGHT + 200)
        # Install resize event handler
        self.window.resizeEvent = self._on_window_resize
        self.current_monday: datetime = _get_monday(_get_today_utc1())
        self.events: Dict[str, List[Dict[str, Any]]] = {}
        self.scheduled_events: Dict[str, List[Dict[str, Any]]] = {}
        self.planning_handler: Optional[Any] = planning_handler
        self.data_handler: Optional[DataHandler] = data_handler
        root_layout: Any = QVBoxLayout(self.window)
        top_bar: Any = QHBoxLayout()
        root_layout.addLayout(top_bar)
        self.header: Any = QLabel(self._week_range_text())
        self.header.setStyleSheet("font-weight:700; font-size:16px; margin:6px 0;")
        top_bar.addWidget(self.header)
        top_bar.addStretch(1)
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
        middle_layout: Any = QHBoxLayout()
        root_layout.addLayout(middle_layout)
        ALLDAY_AREA_HEIGHT = 200
        HOUR_HEIGHT = 40
        self.HOUR_HEIGHT = HOUR_HEIGHT
        self.ALLDAY_AREA_HEIGHT = ALLDAY_AREA_HEIGHT
        time_widget: Any = QWidget()
        time_widget.setMinimumWidth(92)
        time_widget.setMaximumWidth(92)
        self.time_widget = time_widget
        time_layout: Any = QVBoxLayout(time_widget)
        time_layout.setSpacing(6)
        time_layout.setContentsMargins(4, 4, 4, 4)
        spacer_top: Any = QWidget()
        spacer_top.setMinimumHeight(ALLDAY_AREA_HEIGHT)
        spacer_top.setMaximumHeight(ALLDAY_AREA_HEIGHT)
        self._time_spacer = spacer_top
        time_layout.addWidget(spacer_top)
        for h in range(24):
            utc1_hour = (h + 1) % 24
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
        self.day_timeline_widgets: List[Any] = []
        self.day_current_lines: List[Any] = []
        for i in range(7):
            dw: Any = QWidget()
            dl: Any = QVBoxLayout(dw)
            dl.setContentsMargins(6, 6, 6, 6)
            top_container: Any = QWidget()
            top_container_layout: Any = QVBoxLayout(top_container)
            top_container_layout.setContentsMargins(0, 0, 0, 0)
            top_container.setMinimumHeight(ALLDAY_AREA_HEIGHT)
            top_container.setMaximumHeight(ALLDAY_AREA_HEIGHT)
            top_container_layout.addStretch(0)
            dl.addWidget(top_container)
            timed_container: Any = QWidget()
            timed_layout: Any = QVBoxLayout(timed_container)
            timed_layout.setContentsMargins(0, 0, 0, 0)
            timed_layout.setSpacing(6)
            timeline_widget: Any = QWidget()
            timeline_widget.setMinimumHeight(self.HOUR_HEIGHT * 24)
            timeline_widget.setMaximumHeight(self.HOUR_HEIGHT * 24)
            timed_layout.addWidget(timeline_widget)
            dl.addWidget(timed_container)
            dw.setStyleSheet(f'background:{DAY_LABEL_BG_EVEN if i%2==0 else DAY_LABEL_BG_ODD}; border-radius:8px; padding:6px;')
            dw.setMinimumWidth(160)
            week_layout.addWidget(dw, 1)
            self.day_widgets.append(dw)
            self.day_all_day_containers.append(top_container_layout)
            self.day_timed_containers.append(timed_layout)
            self.day_timeline_widgets.append(timeline_widget)
            line_widget = QWidget(timeline_widget)
            line_widget.setObjectName('current_line')
            line_widget.setStyleSheet('background: #E53935; border: none;')
            line_widget.setFixedHeight(2)
            line_widget.hide()  # Initially hidden, will show only for today
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
        self._left_time_line = QWidget(self.time_widget)
        self._left_time_line.setStyleSheet('background: #E53935; border: none;')
        self._left_time_line.setFixedHeight(2)
        self._left_time_line.hide()  # Initially hidden
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_current_lines)
        self._timer.start(60 * 1000)
        QTimer.singleShot(0, self._update_current_lines)

        # Load events from planning handler if provided
        if self.planning_handler is not None:
            self._load_events_from_handler()
        elif self.data_handler is not None and self.data_handler.events:
            self._rebuild_schedule(show_error=False)

        # Load saved calendar state (user-created events)
        self._load_calendar_state()

        self.update_week()

    @staticmethod
    def _format_number(value: Any) -> str:
        try:
            number = float(value)
            if number.is_integer():
                return str(int(number))
            return f"{number:.2f}".rstrip('0').rstrip('.')
        except (TypeError, ValueError):
            return str(value)

    @classmethod
    def _format_rule_summary(cls, rule: Optional[Dict[str, Any]]) -> str:
        if not rule:
            return ""
        rtype = rule.get("type")
        if rtype == "frequency":
            rate = cls._format_number(rule.get("rate", 1))
            unit = rule.get("unit", "")
            return f"  · Every {rate} {unit}(s)"
        if rtype == "condition":
            ref_factor = cls._format_number(rule.get("reference_factor", 1))
            ref_unit = rule.get("reference_unit", "")
            unit_factor = cls._format_number(rule.get("unit_factor", 1))
            unit = rule.get("unit", "")
            index = rule.get("index", 1)
            return (
                f"  · After {ref_factor} {ref_unit}(s), every {unit_factor} {unit}(s), occurrence {index}"
            )
        return ""

    @staticmethod
    def _serialize_rule(rule: Optional[Rule]) -> Optional[Dict[str, Any]]:
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
    def _build_rule_object(rule_data: Optional[Dict[str, Any]]) -> Optional[Rule]:
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

    def _build_event_from_dialog(self, event_data: Dict[str, Any]) -> Event:
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

        rule_obj = self._build_rule_object(event_data.get('rule'))
        time_remaining = event_data.get('time_remaining')
        if time_remaining is None or time_remaining <= 0:
            time_remaining = duration.total_seconds() / 3600.0
        iterations_remaining = event_data.get('iterations_remaining')

        return Event(
            name=event_data['name'],
            startDate=start_dt,
            duration=duration,
            rule=rule_obj,
            timeRemaining=time_remaining,
            iterationsRemaining=iterations_remaining,
        )

    def _on_window_resize(self, event: Any) -> None:
        """Handle window resize events."""
        # Call default resize behavior
        QWidget.resizeEvent(self.window, event)
        # Update event widget positions
        QTimer.singleShot(0, self._relayout_event_widgets)

    def _relayout_event_widgets(self) -> None:
        """Reposition event widgets when timeline width changes."""
        for tl in self.day_timeline_widgets:
            w = tl.width()
            for child in tl.findChildren(QLabel):
                geom = child.geometry()
                try:
                    child.setGeometry(4, geom.y(), max(80, w - 8), geom.height())
                except Exception:
                    pass

    def _load_events_from_handler(self) -> None:
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
                if scheduled_time.tzinfo is None:
                    scheduled_time = scheduled_time + timedelta(hours=1)
                    end_time = end_time + timedelta(hours=1)
                start_time_str = scheduled_time.strftime("%H:%M")
                end_time_str = end_time.strftime("%H:%M")
                ev_dict: Dict[str, Any] = {
                    'name': event.name,
                    'time': start_time_str,
                    'end_time': end_time_str,
                    'all_day': False,
                    'rule': self._serialize_rule(event.rule),
                    'source': 'scheduled',
                    'clickable': False,
                    'date': date_str,
                }
                self.scheduled_events.setdefault(date_str, []).append(ev_dict)

    def _rebuild_schedule(self, show_error: bool = True) -> bool:
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
        self._load_events_from_handler()
        return True
    def _load_calendar_state(self) -> None:
        """Load saved calendar state from pickle file."""
        try:
            if os.path.exists(DataPaths.CALENDAR_STATE.value):
                with open(DataPaths.CALENDAR_STATE.value, 'rb') as f:
                    saved_events = pickle.load(f)
                    # Merge saved events with existing events
                    for date_str, event_list in saved_events.items():
                        normalized: List[Dict[str, Any]] = []
                        for saved_ev in event_list:
                            if not isinstance(saved_ev, dict):
                                continue
                            saved_dict: Dict[str, Any] = dict(cast(Dict[str, Any], saved_ev))
                            saved_dict.setdefault('source', 'manual')
                            saved_dict.setdefault('clickable', True)
                            saved_dict.setdefault('date', date_str)
                            normalized.append(saved_dict)
                        target = self.events.setdefault(date_str, [])
                        for saved_ev in normalized:
                            if saved_ev not in target:
                                target.append(saved_ev)
        except Exception as e:
            print(f"Warning: Could not load calendar state: {e}")
    
    def _save_calendar_state(self) -> None:
        """Save current calendar state to pickle file."""
        try:
            os.makedirs(os.path.dirname(DataPaths.CALENDAR_STATE.value), exist_ok=True)
            with open(DataPaths.CALENDAR_STATE.value, 'wb') as f:
                pickle.dump(self.events, f)
        except Exception as e:
            print(f"Warning: Could not save calendar state: {e}")

    def _store_manual_event(self, event_data: Dict[str, Any]) -> None:
        date_key = event_data['date']
        record: Dict[str, Any] = {
            'name': event_data['name'],
            'time': event_data['start_time'],
            'end_time': event_data['end_time'],
            'all_day': event_data['all_day'],
            'rule': event_data.get('rule'),
            'source': 'manual',
            'clickable': True,
            'date': date_key,
        }
        self.events.setdefault(date_key, []).append(record)
        self._save_calendar_state()
        self.update_week()
    
    def _week_range_text(self) -> str:
        start = self.current_monday
        end = self.current_monday + timedelta(days=6)
        return f"Week: {start.strftime('%d %b %Y')} — {end.strftime('%d %b %Y') }"
    def update_week(self) -> None:
        self.header.setText(self._week_range_text())
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
            date_lbl.setStyleSheet('font-size:12px; margin-bottom:6px;')
            all_layout.addWidget(date_lbl)
            allday_lbl = QLabel('<b>All-day</b>')
            all_layout.addWidget(allday_lbl)
            manual_events = self.events.get(date, [])
            scheduled_events = self.scheduled_events.get(date, [])
            allday_events = [e for e in manual_events if e.get('all_day')]
            if allday_events:
                for ev in allday_events:
                    summary = self._format_rule_summary(ev.get('rule'))
                    lbl = QLabel(f"• {ev.get('name')}{summary}")
                    lbl.setStyleSheet('font-weight:600;')
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
            combined_events = scheduled_events + manual_timed
            if combined_events:
                def _time_key(ev: Dict[str, Any]) -> int:
                    t = ev.get('time') or '00:00'
                    try:
                        hh, mm = map(int, t.split(':'))
                        return hh*60 + mm
                    except Exception:
                        return 0
                combined_events.sort(key=_time_key)
                for ev in combined_events:
                    start = ev.get('time') or '00:00'
                    end = ev.get('end_time') or start
                    name = ev.get('name')
                    summary = self._format_rule_summary(ev.get('rule'))
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
                        'source': ev.get('source', 'manual'),
                        'clickable': ev.get('source', 'manual') == 'manual',
                    }
                    ev_widget = EventLabel(payload, self, timeline_widget)
                    ev_widget.setText(f"{start} — {end}  {name}{summary}")
                    ev_widget.setStyleSheet("background: rgba(66,133,244,0.12); border-left: 4px solid rgba(66,133,244,0.28); border-radius:6px; padding:6px; color:#111;")
                    ev_widget.setWordWrap(True)
                    ev_widget.setGeometry(4, y, max(80, timeline_widget.width() - 8), height_px)
                    ev_widget.show()
            else:
                none_lbl2 = QLabel("(no timed events)")
                none_lbl2.setStyleSheet('color:#777;')
                none_lbl2.setParent(timeline_widget)
                none_lbl2.setGeometry(4, 4, max(80, timeline_widget.width() - 8), 20)
                none_lbl2.show()
        
        # Relayout event widgets after updating the week
        QTimer.singleShot(50, self._relayout_event_widgets)
    
    def prev_week(self) -> None:
        self.current_monday -= timedelta(days=7)
        self.update_week()
    def next_week(self) -> None:
        self.current_monday += timedelta(days=7)
        self.update_week()
    def go_to_today(self) -> None:
        self.current_monday = _get_monday(_get_today_utc1())
        self.update_week()
    def create_event(self) -> None:
        dialog = EventDialog(self.window)
        if dialog.exec_() != QDialog.Accepted:  # type: ignore[attr-defined]
            return

        event_data = dialog.get_data()
        if event_data['all_day'] or self.data_handler is None:
            self._store_manual_event(event_data)
            return

        try:
            event_obj = self._build_event_from_dialog(event_data)
        except ValueError as exc:
            QMessageBox.warning(self.window, "Invalid Event", str(exc))
            self._store_manual_event(event_data)
            return

        self.data_handler.events.append(event_obj)
        try:
            self.data_handler.saveData()
        except Exception as exc:
            self.data_handler.events.pop()
            QMessageBox.critical(self.window, "Save Failed", f"Could not store event: {exc}")
            return

        rebuilt = self._rebuild_schedule(show_error=True)
        if not rebuilt:
            # Roll back persisted event if scheduling failed
            try:
                self.data_handler.events.remove(event_obj)
                self.data_handler.saveData()
            except Exception:
                pass
            self._store_manual_event(event_data)
            return

        self.update_week()

    def _update_current_lines(self) -> None:
         """Update the current time indicator line."""
         now = _get_now_utc1()
         today = now.date()
         current_min = now.hour * 60 + now.minute
         if not self.day_timeline_widgets:
             return
         
         ref_tl = self.day_timeline_widgets[0]
         ref_h = ref_tl.height() if ref_tl.height() > 0 else (self.HOUR_HEIGHT * 24)
         y_tl = int((current_min / (24.0 * 60.0)) * ref_h)
         
         # Only show the line for today's column
         for idx in range(7):
             day_date = (self.current_monday + timedelta(days=idx)).date()
             line = self.day_current_lines[idx]
             tl = self.day_timeline_widgets[idx]
             
             if day_date == today:
                 # Show line for today
                 line.setGeometry(0, y_tl, tl.width(), 2)
                 line.raise_()
                 line.show()
                 
                 # Also show left time line
                 spacer = getattr(self, '_time_spacer', None)
                 top_in_time = spacer.height() if spacer is not None else self.ALLDAY_AREA_HEIGHT
                 y_left = top_in_time + y_tl
                 self._left_time_line.setGeometry(0, y_left, self.time_widget.width(), 2)
                 self._left_time_line.raise_()
                 self._left_time_line.show()
             else:
                 # Hide line for other days
                 line.hide()
    
    def on_event_click(self, payload: Dict[str, Any]) -> None:
        if payload.get('source') != 'manual':
            return
        date = payload.get('date')
        event_ref = payload.get('event')
        if not date or event_ref is None:
            return

        evs = self.events.get(date, [])
        if event_ref not in evs:
            return

        response = QMessageBox.question(
            self.window,
            "Delete Event",
            f"Delete event: {event_ref.get('name')}?",
        )
        if response != QMessageBox.StandardButton.Yes:
            return

        try:
            evs.remove(event_ref)
            if not evs:
                self.events.pop(date, None)
        except Exception:
            pass
        self._save_calendar_state()
        self.update_week()

    def run(self) -> int:
        self.window.show()
        result = self.app.exec()
        # Save state before closing
        self._save_calendar_state()
        return result


def get_calendar(planning_handler: Optional[Any] = None, data_handler: Optional[DataHandler] = None) -> CalendarApp:
    """Create and return a CalendarApp instance.

    Args:
        planning_handler: Optional PlanningHandler instance to load events from
        data_handler: Optional DataHandler used for persisting new events

    Returns:
        CalendarApp instance
    """
    return CalendarApp(planning_handler=planning_handler, data_handler=data_handler)