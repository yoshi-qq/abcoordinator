# ABCoordinator

- **Purpose:** Lightweight PyQt5 calendar that merges manual events with a recurring-rule planner.
- **Tech Stack:** PyQt5 UI, custom PlanningHandler/DataHandler pipeline, pickle persistence in `data/`.
- **UI Highlights:** Scrollable week view, taller time blocks, live "now" line, keyboard navigation (←/→ + T/Home), create/edit dialogs for every entry.
- **Scheduling Engine:** FrequencyRule and ConditionRule expansion, overlap prevention, configurable working hours, all-day detection via day span.
- **Persistence:** Versioned pickles (`events`, `rules`, `instances`, `calendar_state`) created on demand with corruption-safe fallbacks.
- **Repository Map:** `classes/` domain models, `handler/` data + planner logic, `frontend/` UI shell, `scripts/` helpers, `tests/` automation, `__main__.py` launcher.
- **Setup:** `python -m venv .venv`, activate, `pip install -r requirements.txt`, run `python __main__.py` from project root.
- **Testing & Samples:** `python -m unittest tests/test_planning_handler.py`, `python test_calendar.py`, `python scripts/populate_sample_data.py` to reset curated fixtures.
- **Customization:** Tweak colors/sizing in `config/constants.py`, adjust `dayStartHour/dayEndHour`, extend populate script for domain-specific datasets.
- **Future Ideas:** ICS/CALDAV import, tag-based filters, visual capacity indicators, richer analytics panes.
