from typing import Optional
from datetime import datetime
from classes.ruleTypes import Rule

class Event:
	def __init__(self, name: str, startDate: datetime, duration: float, rule: Optional[Rule], timeRemaining: float, iterationsRemaining: int, deadline: datetime, allowedTags: list[str], tags: list[str]) -> None:
		self.name = name
		self.startDate = startDate
		self.duration = duration
		self.rule = rule
		self.timeRemaining = timeRemaining
		self.iterationsRemaining = iterationsRemaining
		self.deadline = deadline
		self.allowedTags = allowedTags
		self.tags = tags

