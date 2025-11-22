import tkinter as tk
from tkinter import simpledialog, messagebox
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from config.constants import WINDOW_HEIGHT, WINDOW_WIDTH, BG_TOP_FRAME, BTN_FG, BTN_BG_CREATE, BTN_BG_PRIMARY, BTN_BG_TODAY, DAY_LABEL_BG_EVEN, DAY_LABEL_BG_ODD, DAY_LABEL_FG, DAY_LABEL_FONT, DAY_LABEL_HEIGHT, DAY_LABEL_WIDTH

class CalendarApp:
    def __init__(self, parent: tk.Tk) -> None:
        self.parent: tk.Tk = parent
        self.parent.title("ABCoordinator")
        self.parent.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.current_monday: datetime = self.get_monday(datetime.today())
        self.events: Dict[str, List[str]] = {}

        top_frame: tk.Frame = tk.Frame(parent, bg=BG_TOP_FRAME)
        top_frame.pack(fill="x", pady=10)

        self.prev_btn = tk.Button(top_frame, text="<< Prev", command=self.prev_week, bg=BTN_BG_PRIMARY, fg=BTN_FG)
        self.prev_btn.pack(side="left", padx=5, ipadx=10, ipady=5)

        self.today_btn = tk.Button(top_frame, text="Today", command=self.go_to_today, bg=BTN_BG_TODAY, fg=BTN_FG)
        self.today_btn.pack(side="left", padx=5, ipadx=10, ipady=5)

        self.next_btn = tk.Button(top_frame, text="Next >>", command=self.next_week, bg=BTN_BG_PRIMARY, fg=BTN_FG)
        self.next_btn.pack(side="left", padx=5, ipadx=10, ipady=5)

        self.create_btn = tk.Button(top_frame, text="Create Event", command=self.create_event, bg=BTN_BG_CREATE, fg=BTN_FG)
        self.create_btn.pack(side="right", padx=10, ipadx=10, ipady=5)

        self.week_frame: tk.Frame = tk.Frame(parent)
        self.week_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.day_labels: List[tk.Label] = []
        for i in range(7):
            lbl = tk.Label(
                self.week_frame,
                text="",
                borderwidth=2,
                relief="ridge",
                width=DAY_LABEL_WIDTH,
                height=DAY_LABEL_HEIGHT,
                bg=DAY_LABEL_BG_ODD,
                fg=DAY_LABEL_FG,
                anchor="n",
                justify="center",
                font=DAY_LABEL_FONT
            )
            lbl.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            self.day_labels.append(lbl)
            self.week_frame.grid_columnconfigure(i, weight=1)
        self.update_week()

    def get_monday(self, date: datetime) -> datetime:
        return date - timedelta(days=date.weekday())

    def update_week(self) -> None:
        for i in range(7):
            day = self.current_monday + timedelta(days=i)
            day_str = day.strftime("%A\n%d %b %Y")
            events_text = "\n".join(self.events.get(day.strftime("%Y-%m-%d"), []))
            bg_color = DAY_LABEL_BG_EVEN if i % 2 == 0 else DAY_LABEL_BG_ODD
            self.day_labels[i].config(text=f"{day_str}\n{events_text}", bg=bg_color)

    def prev_week(self) -> None:
        self.current_monday -= timedelta(days=7)
        self.update_week()

    def next_week(self) -> None:
        self.current_monday += timedelta(days=7)
        self.update_week()

    def go_to_today(self) -> None:
        self.current_monday = self.get_monday(datetime.today())
        self.update_week()

    def create_event(self) -> None:
        event_date_str: Optional[str] = simpledialog.askstring("Event Date", "Enter date (YYYY-MM-DD):")
        if not event_date_str:
            return
        try:
            datetime.strptime(event_date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Invalid date format")
            return
        event_name: Optional[str] = simpledialog.askstring("Event Name", "Enter event name:")
        if not event_name:
            return
        self.events.setdefault(event_date_str, []).append(event_name.strip())
        self.update_week()

    def run(self) -> None:
        self.parent.mainloop()

calendar = CalendarApp(tk.Tk())