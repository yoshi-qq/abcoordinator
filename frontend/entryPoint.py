from frontend.Calendar import get_calendar


def entryPointFunc():
  cal = get_calendar()
  cal.run()