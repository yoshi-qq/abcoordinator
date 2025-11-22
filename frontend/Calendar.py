from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta, timezone
import pickle
import os
from config.constants import WINDOW_HEIGHT, WINDOW_WIDTH, BTN_BG_PRIMARY, BTN_BG_TODAY, BTN_BG_CREATE, DAY_LABEL_BG_EVEN, DAY_LABEL_BG_ODD, DataPaths
try:
    from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QInputDialog, QMessageBox, QScrollArea, QSizePolicy  # type: ignore[import]
    from PyQt5.QtCore import QTimer, Qt  # type: ignore[import]
except Exception as exc:
    raise ImportError("PyQt5 is required. Install it with: python -m pip install --user PyQt5") from exc

try:
    from handler.planningHandler import PlanningHandler, ScheduledEvent
except ImportError:
    PlanningHandler = None  # type: ignore[misc,assignment]
    ScheduledEvent = None  # type: ignore[misc,assignment]

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
    def __init__(self, date: str, idx: int, owner: Any, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._date = date
        self._idx = idx
        self._owner = owner
        return
    def mousePressEvent(self, ev: Any) -> None:
        try:
            self._owner.on_event_click(self._date, self._idx)
        except Exception:
            pass

class CalendarApp:
    def __init__(self, planning_handler: Optional[Any] = None) -> None:
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
        self.planning_handler: Optional[Any] = planning_handler
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
        # Display hours in UTC+1 (shift by 1 hour)
        for h in range(24):
            # Convert UTC hour to UTC+1 hour
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
        self.update_week()
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
        
        # Load saved calendar state (user-created events)
        self._load_calendar_state()

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
        if self.planning_handler is None:
            return
        
        for date_key, scheduled_events in self.planning_handler.scheduledDays.items():
            date_str = date_key.strftime("%Y-%m-%d")
            for scheduled in scheduled_events:
                event = scheduled.event
                # Convert scheduled time to UTC+1 if needed
                scheduled_time = scheduled.scheduledTime
                end_time = scheduled.endTime
                
                # If the times don't have timezone info, they might be in UTC
                # Convert them to UTC+1 by adding 1 hour
                if scheduled_time.tzinfo is None:
                    # Check if we need to adjust - compare with current UTC+1 time
                    # If the scheduled time seems to be in UTC, add 1 hour
                    scheduled_time = scheduled_time + timedelta(hours=1)
                    end_time = end_time + timedelta(hours=1)
                
                start_time_str = scheduled_time.strftime("%H:%M")
                end_time_str = end_time.strftime("%H:%M")
                
                ev_dict: Dict[str, Any] = {
                    'name': event.name,
                    'time': start_time_str,
                    'end_time': end_time_str,
                    'all_day': False
                }
                
                self.events.setdefault(date_str, []).append(ev_dict)
    
    def _load_calendar_state(self) -> None:
        """Load saved calendar state from pickle file."""
        try:
            if os.path.exists(DataPaths.CALENDAR_STATE.value):
                with open(DataPaths.CALENDAR_STATE.value, 'rb') as f:
                    saved_events = pickle.load(f)
                    # Merge saved events with existing events
                    for date_str, event_list in saved_events.items():
                        if date_str not in self.events:
                            self.events[date_str] = event_list
                        else:
                            # Add saved events that aren't already in the list
                            for saved_ev in event_list:
                                if saved_ev not in self.events[date_str]:
                                    self.events[date_str].append(saved_ev)
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
            events = self.events.get(date, [])
            allday_events = [e for e in events if e.get('all_day')]
            if allday_events:
                for ev in allday_events:
                    lbl = QLabel(f"• {ev.get('name')}")
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
            timed_events = [e for e in events if not e.get('all_day')]
            if timed_events:
                def _time_key(ev: Dict[str, Any]) -> int:
                    t = ev.get('time') or '00:00'
                    try:
                        hh, mm = map(int, t.split(':'))
                        return hh*60 + mm
                    except Exception:
                        return 0
                # sort the original events list indices by start time
                indexed = [(idx, e) for idx, e in enumerate(events) if not e.get('all_day')]
                indexed.sort(key=lambda ie: _time_key(ie[1]))
                for ev_idx, ev in indexed:
                    start = ev.get('time') or '00:00'
                    end = ev.get('end_time') or start
                    name = ev.get('name')
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
                    ev_widget = EventLabel(date, ev_idx, self, timeline_widget)
                    ev_widget.setText(f"{start} — {end}  {name}")
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
        default_date = _get_today_utc1().strftime("%Y-%m-%d")
        date_str, ok = QInputDialog.getText(self.window, "Event Date", "Enter date (YYYY-MM-DD):", text=default_date)  # type: ignore[arg-type]
        if not ok or not date_str:
            return
        date_str = date_str.strip()
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            QMessageBox.warning(self.window, "Error", "Invalid date format")  # type: ignore[arg-type]
            return

        choice, ok_choice = QInputDialog.getItem(self.window, "All-day?", "Is this an all-day event?", ["No", "Yes"], 0, False)  # type: ignore[arg-type]
        if not ok_choice:
            return
        is_all = (choice == "Yes")

        time_val: Optional[str] = None
        end_time: Optional[str] = None
        if not is_all:
            time_val, ok_time = QInputDialog.getText(self.window, "Start Time", "Enter start time (HH:MM, 24h):", text="09:00")  # type: ignore[arg-type]
            if not ok_time or not time_val:
                return
            time_val = time_val.strip()
            try:
                datetime.strptime(time_val, "%H:%M")
            except ValueError:
                QMessageBox.warning(self.window, "Error", "Invalid time format; use HH:MM (24h)")  # type: ignore[arg-type]
                return
            end_time, ok_end = QInputDialog.getText(self.window, "End Time", "Enter end time (HH:MM, 24h):", text="10:00")  # type: ignore[arg-type]
            if not ok_end or not end_time:
                return
            end_time = end_time.strip()
            try:
                datetime.strptime(end_time, "%H:%M")
            except ValueError:
                QMessageBox.warning(self.window, "Error", "Invalid time format; use HH:MM (24h)")  # type: ignore[arg-type]
                return
            try:
                sh, sm = map(int, time_val.split(':'))
                eh, em = map(int, end_time.split(':'))
                if eh*60 + em <= sh*60 + sm:
                    QMessageBox.warning(self.window, "Error", "End time must be after start time")  # type: ignore[arg-type]
                    return
            except Exception:
                pass

        name, ok_name = QInputDialog.getText(self.window, "Event Name", "Enter event name:")  # type: ignore[arg-type]
        if not ok_name or not name:
            return

        ev: Dict[str, Any] = {'name': name.strip(), 'time': time_val, 'end_time': end_time, 'all_day': is_all}
        self.events.setdefault(date_str, []).append(ev)
        self._save_calendar_state()
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
    
    def on_event_click(self, date: str, ev_idx: int) -> None:
        evs = self.events.get(date, [])
        if ev_idx < 0 or ev_idx >= len(evs):
            return
        ev = evs[ev_idx]
        choice, ok = QInputDialog.getItem(self.window, "Delete?", f"Delete event: {ev.get('name')}?", ["No", "Yes"], 0, False)  # type: ignore[arg-type]
        if not ok or choice != "Yes":
            return
        try:
            evs.pop(ev_idx)
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


def get_calendar(planning_handler: Optional[Any] = None) -> CalendarApp:
    """Create and return a CalendarApp instance.

    Args:
        planning_handler: Optional PlanningHandler instance to load events from

    Returns:
        CalendarApp instance
    """
    return CalendarApp(planning_handler=planning_handler)