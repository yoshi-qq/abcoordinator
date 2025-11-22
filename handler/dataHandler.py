from classes.eventTypes import Event
from classes.ruleTypes import ConditionRule, Rule
from pickle import dump, load

from classes.timeUnits import TimeUnit


class DataHandler:
	def __init__(self) -> None:
		self.rules: list[Rule] = [ConditionRule('week', 1, 'day', 1, 1)]
		self.events: list[Event] = [Event()]
	def saveData(self) -> None:
		pass
	def loadData(self) -> None:
		pass