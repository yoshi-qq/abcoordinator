from classes.timeUnits import TimeUnit


class Rule:
  def __init__(self) -> None:
    pass

class FrequencyRule(Rule):
	def __init__(self, unit: TimeUnit, rate: float) -> None:
		self.unit: TimeUnit = unit
		self.rate: float = rate

class ConditionRule(Rule):
	def __init__(self, reference: TimeUnit, referenceFactor: float, unit: TimeUnit, unitFactor: float, index: int) -> None:
		self.reference: str = reference
		self.referenceFactor: float = referenceFactor
		self.unit: TimeUnit = unit
		self.unitFactor: float = unitFactor
		self.index: int = index