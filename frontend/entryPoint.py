from frontend.Calendar import getCalendar
from handler.dataHandler import DataHandler
from handler.planningHandler import PlanningHandler


def entryPointFunc():
    """Launch the calendar UI using the persisted dataset."""
    data_handler = DataHandler()
    planning_handler = None
    if data_handler.events:
        planning_handler = PlanningHandler(data_handler.events)
    calendar = getCalendar(planning_handler=planning_handler, data_handler=data_handler)
    calendar.run()