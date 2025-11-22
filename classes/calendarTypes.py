from datetime import datetime


class EventInstance:
	def __init__(self, name: str, date: datetime, duration: float) -> None:
		self.name = name
		self.date = date
		self.duration = duration