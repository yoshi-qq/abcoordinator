from uuid import UUID


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