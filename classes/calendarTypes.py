from datetime import datetime
from classes.eventTypes import Event

class EventInstance:
	def __init__(self, name: str, date: datetime, duration: float, event: Event) -> None:
		self.name = name
		self.date = date
		self.duration = duration
		self.event = event