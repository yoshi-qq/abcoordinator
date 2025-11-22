from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from config.constants import WINDOW_HEIGHT, WINDOW_WIDTH, BTN_BG_PRIMARY, BTN_BG_TODAY, BTN_BG_CREATE, DAY_LABEL_BG_EVEN, DAY_LABEL_BG_ODD
try:
    from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QInputDialog, QMessageBox, QScrollArea, QSizePolicy  # type: ignore[import]
    from PyQt5.QtCore import QTimer, QPoint  # type: ignore[import]
except Exception as exc:
    raise ImportError("PyQt5 is required. Install it with: python -m pip install --user PyQt5") from exc

def _get_monday(date: datetime) -> datetime:
    return date - timedelta(days=date.weekday())

class CalendarApp:
    def __init__(self) -> None:
        self._app: Any = QApplication.instance()
        if self._app is None:
            self._app = QApplication([])
        self.window: Any = QWidget()
        self.window.setWindowTitle("ABCoordinator")
        self.window.resize(WINDOW_WIDTH, WINDOW_HEIGHT + 200)
        self.current_monday: datetime = _get_monday(datetime.today())
        self.events: Dict[str, List[Dict[str, Any]]] = {}
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
        self.tz_offset_hours = 1
        time_widget: Any = QWidget()
        time_widget.setFixedWidth(92)
        self.time_widget = time_widget
        time_layout: Any = QVBoxLayout(time_widget)
        time_layout.setSpacing(6)
        time_layout.setContentsMargins(4, 4, 4, 4)
        spacer_top: Any = QWidget()
        spacer_top.setFixedHeight(ALLDAY_AREA_HEIGHT)
        self._time_spacer = spacer_top
        time_layout.addWidget(spacer_top)
        for h in range(24):
            tl = QLabel(f"{h:02d}:00")
            tl.setStyleSheet("color:#555; padding:6px; font-family:monospace;")
            tl.setMinimumHeight(self.HOUR_HEIGHT)
            time_layout.addWidget(tl)

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
            dw.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # type: ignore[attr-defined]
            top_container: Any = QWidget()
            top_container_layout: Any = QVBoxLayout(top_container)
            top_container_layout.setContentsMargins(0, 0, 0, 0)
            top_container.setFixedHeight(ALLDAY_AREA_HEIGHT)
            top_container_layout.addStretch(0)
            dl.addWidget(top_container)
            timed_container: Any = QWidget()
            timed_layout: Any = QVBoxLayout(timed_container)
            timed_layout.setContentsMargins(0, 0, 0, 0)
            timed_layout.setSpacing(6)
            timeline_widget: Any = QWidget()
            timeline_widget.setFixedHeight(self.HOUR_HEIGHT * 24)
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
            line_widget.setStyleSheet('background: rgba(220,20,60,0.25);')
            line_widget.setFixedHeight(1)
            line_widget.show()
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
        self._left_time_line = QWidget(self.time_widget)
        self._left_time_line.setStyleSheet('background: rgba(220,20,60,0.25);')
        self._left_time_line.setFixedHeight(1)
        self._left_time_line.show()
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_current_lines)
        self._timer.start(60 * 1000)
        QTimer.singleShot(0, self._update_current_lines)
        def _on_resize(event: Any) -> None:
            try:
                self._relayout_event_widgets()
            except Exception:
                pass
        self.window.resizeEvent = _on_resize

    def _relayout_event_widgets(self) -> None:
        for tl in self.day_timeline_widgets:
            w = tl.width()
            for child in tl.findChildren(QLabel):
                if child.objectName() == 'current_line':
                    continue
                geom = child.geometry()
                child.setGeometry(4, geom.y(), max(80, w - 8), geom.height())

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
                timed_events.sort(key=_time_key)
                for ev in timed_events:
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
                    ev_widget = QLabel(f"{start} — {end}  {name}", timeline_widget)
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
        default_date = datetime.today().strftime("%Y-%m-%d")
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
        self.update_week()

    def _update_current_lines(self) -> None:
         now = datetime.now()
         current_min = now.hour * 60 + now.minute
         if not self.day_timeline_widgets:
             return
         ref_tl = self.day_timeline_widgets[0]
         ref_h = ref_tl.height() if ref_tl.height() > 0 else (self.HOUR_HEIGHT * 24)
         y_tl = int((current_min / (24.0 * 60.0)) * ref_h)
         for idx, tl in enumerate(self.day_timeline_widgets):
             line = self.day_current_lines[idx]
             line.setGeometry(0, y_tl, tl.width(), 1)
             line.raise_()
             line.show()
         try:
             pt = ref_tl.mapTo(self.time_widget, QPoint(0, 0))
             top_in_time = pt.y()
         except Exception:
             spacer = getattr(self, '_time_spacer', None)
             top_in_time = spacer.height() if spacer is not None else self.ALLDAY_AREA_HEIGHT
         y_left = top_in_time + y_tl
         self._left_time_line.setGeometry(0, y_left, self.time_widget.width(), 1)
         self._left_time_line.raise_()
         self._left_time_line.show()

    def run(self) -> int:
        self.window.show()
        return self._app.exec()

def get_calendar() -> CalendarApp:
    return CalendarApp()