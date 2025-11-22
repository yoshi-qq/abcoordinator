from classes.calendarTypes import EventInstance
from classes.eventTypes import Event
from classes.ruleTypes import Rule
from pickle import dump, load
import os

from config.constants import DataPaths

class DataHandler:
	def __init__(self) -> None:
		self.rules: list[Rule] = []
		self.events: list[Event] = []
		self.instances: list[EventInstance] = []

		self.loadData()

	def saveData(self) -> None:
		with open(DataPaths.EVENTS.value, 'wb') as f:
			dump(self.events, f)
		with open(DataPaths.RULES.value, 'wb') as f:
			dump(self.rules, f)
		with open(DataPaths.INSTANCES.value, 'wb') as f:
			dump(self.instances, f)
	def loadData(self) -> None:
		if os.path.isfile(DataPaths.EVENTS.value):
			with open(DataPaths.EVENTS.value, 'rb') as f:
				self.rules = load(f)
		if os.path.isfile(DataPaths.RULES.value):
			with open(DataPaths.RULES.value, 'rb') as f:
				self.events = load(f)
		if os.path.isfile(DataPaths.INSTANCES.value):
			with open(DataPaths.INSTANCES.value, 'rb') as f:
				self.instances = load(f)