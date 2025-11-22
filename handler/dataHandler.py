from typing import Any, cast

from classes.calendarTypes import EventInstance
from classes.eventTypes import Event
from classes.ruleTypes import Rule
from pickle import dump, load
import os

from config.constants import DataPaths

DATA_VERSION = 1


class DataHandler:
	def __init__(self) -> None:
		self.rules: list[Rule] = []
		self.events: list[Event] = []
		self.instances: list[EventInstance] = []

		self.loadData()

	def saveData(self) -> None:
		self._write_payload(DataPaths.EVENTS.value, self.events)
		self._write_payload(DataPaths.RULES.value, self.rules)
		self._write_payload(DataPaths.INSTANCES.value, self.instances)

	def loadData(self) -> None:
		self.events = self._load_payload(DataPaths.EVENTS.value)
		self.rules = self._load_payload(DataPaths.RULES.value)
		self.instances = self._load_payload(DataPaths.INSTANCES.value)

	def _write_payload(self, path: str, payload: Any) -> None:
		directory = os.path.dirname(path)
		if directory:
			os.makedirs(directory, exist_ok=True)
		with open(path, 'wb') as handle:
			dump({'version': DATA_VERSION, 'payload': payload}, handle)

	def _load_payload(self, path: str) -> list[Any]:
		if not os.path.isfile(path):
			return []
		try:
			with open(path, 'rb') as handle:
				data = load(handle)
		except Exception as exc:
			print(f"Warning: Could not load {path}: {exc}. Resetting to empty list.")
			return []
		payload: Any = data
		if isinstance(data, dict) and 'payload' in data:
			payload = data.get('payload', []) # type: ignore
		if not isinstance(payload, list):
			print(f"Warning: Unexpected payload type in {path}; resetting to empty list.")
			return []
		return cast(list[Any], payload)