from typing import Optional
from datetime import datetime, timedelta
from classes.ruleTypes import Rule

class Event:
	def __init__(self, name: str, startDate: datetime, duration: Optional[timedelta] = None, rule: Optional[Rule] = None, timeRemaining: Optional[float] = None, iterationsRemaining: Optional[int] = None, deadline: Optional[datetime] = None, allowedTags: Optional[list[str]] = None, tags: Optional[list[str]] = None) -> None:
		self.name = name
		self.startDate = startDate
		self.duration = duration
		self.rule = rule
		self.timeRemaining = timeRemaining
		self.iterationsRemaining = iterationsRemaining
		self.deadline = deadline
		self.allowedTags = allowedTags if allowedTags else []
		self.tags = tags if tags else []

