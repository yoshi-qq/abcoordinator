from uuid import UUID

from classes.timeUnits import TimeUnit


class Event:
	def __init__(self, uuid: UUID, name: str, startDate: int, duration: int, frequencyRuleId: UUID, conditionRuleId: UUID, timeRemaining: int, iterationsRemaining: int, deadline: int, allowedTags: str, tags: str) -> None:
		self.uuid = uuid
		self.name = name
		self.startDate = startDate
		self.duration = duration
		self.frequencyRuleId = frequencyRuleId
		self.conditionRuleId = conditionRuleId
		self.timeRemaining = timeRemaining
		self.iterationsRemaining = iterationsRemaining
		self.deadline = deadline
		self.allowedTags = allowedTags
		self.tags = tags

class FrequencyRule:
	def __init__(self, uuid: UUID, unit: TimeUnit, rate: float) -> None:
		self.uuid: UUID = uuid
		self.unit: TimeUnit = unit
		self.rate: float = rate

class ConditionRule:
	def __init__(self, uuid: UUID, reference: str, referenceFactor: float, unit: TimeUnit, unitFactor: float, number: int) -> None:
		self.uuid: UUID = uuid
		self.reference: str = reference
		self.referenceFactor: float = referenceFactor
		self.unit: TimeUnit = unit
		self.unitFactor: float = unitFactor
		self.number: int = number