from frontend.Calendar import get_calendar
from handler.dataHandler import DataHandler
from handler.planningHandler import PlanningHandler


def entryPointFunc():
  # Load data and create planning handler
  data_handler = DataHandler()
  
  # Create planning handler with loaded events
  planning_handler = None
  if data_handler.events:
    planning_handler = PlanningHandler(data_handler.events)
  
  # Create and run calendar with planning handler
  cal = get_calendar(planning_handler=planning_handler, data_handler=data_handler)
  cal.run()