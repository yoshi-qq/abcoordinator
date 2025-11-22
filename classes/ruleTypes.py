from classes.timeUnits import TimeUnit


class Rule:
	def __init__(self) -> None:
		pass

class FrequencyRule(Rule):
	def __init__(self, unit: TimeUnit, rate: float) -> None:
		self.unit: TimeUnit = unit
		self.rate: float = rate
	def __str__(self) -> str:
		return f"Every {self.rate} {self.unit}(s)"

class ConditionRule(Rule):
	def __init__(self, reference: TimeUnit, referenceFactor: float, unit: TimeUnit, unitFactor: float, index: int) -> None:
		self.reference: TimeUnit = reference
		self.referenceFactor: float = referenceFactor
		self.unit: TimeUnit = unit
		self.unitFactor: float = unitFactor
		self.index: int = index
	def __str__(self) -> str:
		return f"After {self.referenceFactor} {self.reference}(s), every {self.unitFactor} {self.unit}(s), occurrence {self.index}"