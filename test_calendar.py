"""Test script to verify calendar functionality."""
import sys
from pathlib import Path
from datetime import datetime, timedelta

project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from classes.eventTypes import Event
from handler.planningHandler import PlanningHandler

def create_test_events():
    """Create some test events for the calendar."""
    now = datetime.now()

    events = [
        Event(
            name="Morning Meeting",
            startDate=now.replace(hour=9, minute=0, second=0, microsecond=0),
            duration=timedelta(hours=1),
            iterationsRemaining=1
        ),
        Event(
            name="Lunch Break",
            startDate=now.replace(hour=12, minute=0, second=0, microsecond=0),
            duration=timedelta(hours=1),
            iterationsRemaining=1
        ),
        Event(
            name="Project Work",
            startDate=now.replace(hour=14, minute=0, second=0, microsecond=0),
            duration=timedelta(hours=2),
            iterationsRemaining=1
        ),
    ]

    return events

def main():
    """Test the calendar with some sample events."""
    print("Creating test events...")
    events = create_test_events()

    print("Creating planning handler...")
    planner = PlanningHandler(events)

    print("\nScheduled events:")
    for date, scheduled_events in planner.scheduledDays.items():
        print(f"\n{date.strftime('%Y-%m-%d')}:")
        for scheduled in sorted(scheduled_events, key=lambda e: e.scheduledTime):
            print(f"  {scheduled.scheduledTime.strftime('%H:%M')} - {scheduled.endTime.strftime('%H:%M')}: {scheduled.event.name}")

    print("\nLaunching calendar...")
    from frontend.Calendar import getCalendar

    calendar = getCalendar(planning_handler=planner)
    calendar.run()

if __name__ == "__main__":
    main()
