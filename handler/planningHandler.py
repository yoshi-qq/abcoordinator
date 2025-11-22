from datetime import datetime, timedelta
from classes.eventTypes import Event
from classes.ruleTypes import FrequencyRule, ConditionRule
from classes.timeUnits import TimeUnit
from config.constants import CUTOFF_DISTANCE

class ScheduledEvent:
	"""Represents an event scheduled at a specific time within a day."""
	def __init__(self, event: Event, scheduledTime: datetime) -> None:
		self.event = event
		self.scheduledTime = scheduledTime
		self.endTime = scheduledTime + (event.duration if event.duration is not None else timedelta(0))

	def __repr__(self) -> str:
		return f"ScheduledEvent({self.event.name} at {self.scheduledTime.time()})"

def delta(unit: TimeUnit, factor: float) -> timedelta:
	match unit:
		case 'day':
			return timedelta(days=factor)
		case 'week':
			return timedelta(weeks=factor)
		case 'hour':
			return timedelta(hours=factor)
		case 'minute':
			return timedelta(minutes=factor)
		case 'second':
			return timedelta(seconds=factor)
		case 'month':
			return timedelta(days=30 * factor) # TODO: Improve month handling
		case 'year':
			return timedelta(days=365 * factor) # TODO: Improve year handling

def getSum(events: list[Event]) -> timedelta:
	"""
	Calculate the total duration of all events in a list.

	Args:
		events: List of Event objects

	Returns:
		Total duration as a timedelta object
	"""
	total: timedelta = timedelta(0)
	for event in events:
		if event.duration is not None:
			total += event.duration
	return total

def findEarliestSlot(scheduledEvents: list[ScheduledEvent], duration: timedelta, dayStart: datetime, dayEnd: datetime) -> datetime | None:
	"""
	Find the earliest available time slot for an event with given duration.

	Args:
		scheduledEvents: List of already scheduled events
		duration: Duration of the event to be scheduled
		dayStart: Start time of the working day
		dayEnd: End time of the working day

	Returns:
		Datetime of the earliest available slot, or None if no slot is available
	"""
	if not scheduledEvents:
		return dayStart

	# Sort events by scheduled time
	sortedEvents = sorted(scheduledEvents, key=lambda e: e.scheduledTime)

	# Check if there's space before the first event
	if sortedEvents[0].scheduledTime - dayStart >= duration:
		return dayStart

	# Check gaps between consecutive events
	for i in range(len(sortedEvents) - 1):
		gapStart = sortedEvents[i].endTime
		gapEnd = sortedEvents[i + 1].scheduledTime
		if gapEnd - gapStart >= duration:
			return gapStart

	# Check if there's space after the last event
	lastEventEnd = sortedEvents[-1].endTime
	if dayEnd - lastEventEnd >= duration:
		return lastEventEnd

	return None

class PlanningHandler:
	"""
	Handles the planning and scheduling of events across multiple days.

	Args:
		events: List of Event objects to schedule
		dayStartHour: Hour of day when scheduling starts (default: 6)
		dayEndHour: Hour of day when scheduling ends (default: 22)
	"""
	def __init__(self, events: list[Event], dayStartHour: int = 6, dayEndHour: int = 22) -> None:
		self.days: dict[datetime, list[Event]] = {}
		self.scheduledDays: dict[datetime, list[ScheduledEvent]] = {}
		self.dayStartHour = dayStartHour
		self.dayEndHour = dayEndHour
		# assign events to days
		for event in events:
			self.placeEvent(event)
		# schedule each day individually
		for date, events in self.days.items():
			self.scheduledDays[date] = self.scheduleDay(date, events)

	def placeEvent(self, event: Event) -> None:
		"""
		Place an event into appropriate days based on its rule type.

		Args:
			event: The Event object to place
		"""
		if type(event.rule) == FrequencyRule:
			cont: bool = True
			iteration: int = 0
			while cont:
				cont = self.placeFrequencyEvent(event, event.rule, iteration)
				iteration += 1
				if event.iterationsRemaining and iteration >= event.iterationsRemaining:
					cont = False
		elif type(event.rule) == ConditionRule:
			cont: bool = True
			iteration: int = 0
			while cont:
				cont = self.placeConditionEvent(event, event.rule, iteration)
				iteration += 1
				if event.iterationsRemaining and iteration >= event.iterationsRemaining:
					cont = False
		else:
			if event.iterationsRemaining is not None:
				for _ in range(event.iterationsRemaining):
					self.placeAutonomousEvent(event)

	def placeFrequencyEvent(self, event: Event, rule: FrequencyRule, iteration: int = 0) -> bool:
		"""
		Place an event that repeats at a fixed frequency.

		Args:
			event: The Event object to place
			rule: The FrequencyRule defining the repetition pattern
			iteration: Current iteration number (default: 0)

		Returns:
			True if the event was placed successfully, False if beyond cutoff distance
		"""
		date: datetime = event.startDate + iteration*delta(rule.unit, rule.rate)
		if date > datetime.now() + CUTOFF_DISTANCE:
			return False
		if self.days.get(date) is None:
			self.days[date] = []
		self.days[date].append(event)
		return True

	def placeConditionEvent(self, event: Event, rule: ConditionRule, iteration: int = 0) -> bool:
		"""
		Place an event that repeats based on conditional rules.

		Args:
			event: The Event object to place
			rule: The ConditionRule defining the repetition pattern
			iteration: Current iteration number (default: 0)

		Returns:
			True if the event was placed successfully, False if beyond cutoff distance
		"""
		baseDate: datetime = event.startDate + iteration*delta(rule.reference, rule.referenceFactor)
		date: datetime = baseDate + (rule.index-1) * delta(rule.unit, rule.unitFactor)
		if date > datetime.now() + CUTOFF_DISTANCE:
			return False
		if self.days.get(date) is None:
			self.days[date] = []
		self.days[date].append(event)
		return True

	def placeAutonomousEvent(self, event: Event) -> None:
		"""
		Place an autonomous event in the earliest available day with capacity.

		Args:
			event: The Event object to place
		"""
		cont: bool = True
		currentDate: datetime = event.startDate.replace(hour=0, minute=0, second=0, microsecond=0)
		maxDays: int = 100  # Prevent infinite loops
		daysChecked: int = 0

		while cont and daysChecked < maxDays:
			if self.days.get(currentDate) is None:
				self.days[currentDate] = []

			availableHours: timedelta = timedelta(hours=(self.dayEndHour - self.dayStartHour))
			if getSum(self.days[currentDate]) + (event.duration if event.duration is not None else timedelta(0)) <= availableHours:
				self.days[currentDate].append(event)
				cont = False
			else:
				currentDate += timedelta(days=1)
				daysChecked += 1

		if cont:
			print(f"Could not place autonomous event {event.name} starting from {event.startDate}")

	def scheduleDay(self, date: datetime, events: list[Event]) -> list[ScheduledEvent]:
		"""Schedule events within a specific day, finding time slots for each."""
		dayStart: datetime = date.replace(hour=self.dayStartHour, minute=0, second=0, microsecond=0)
		dayEnd: datetime = date.replace(hour=self.dayEndHour, minute=0, second=0, microsecond=0)

		# Separate events with deadlines and without
		eventsWithDeadlines: list[Event] = [e for e in events if e.deadline is not None]
		eventsWithoutDeadlines: list[Event] = [e for e in events if e.deadline is None]

		# Sort by deadline (earliest first) and then by priority (if needed)
		eventsWithDeadlines.sort(key=lambda e: e.deadline if e.deadline is not None else datetime.max)

		scheduledEvents: list[ScheduledEvent] = []

		# Schedule events with deadlines first
		for event in eventsWithDeadlines:
			scheduled = self.scheduleEvent(event, scheduledEvents, dayStart, dayEnd)
			if scheduled:
				scheduledEvents.append(scheduled)

		# Then schedule events without deadlines
		for event in eventsWithoutDeadlines:
			scheduled = self.scheduleEvent(event, scheduledEvents, dayStart, dayEnd)
			if scheduled:
				scheduledEvents.append(scheduled)

		return scheduledEvents

	def scheduleEvent(self, event: Event, existingSchedule: list[ScheduledEvent], dayStart: datetime, dayEnd: datetime) -> ScheduledEvent | None:
		"""
		Find a time slot for an event and create a ScheduledEvent.

		Args:
			event: The Event object to schedule
			existingSchedule: List of already scheduled events for this day
			dayStart: Start time of the working day
			dayEnd: End time of the working day

		Returns:
			A ScheduledEvent object if a slot was found, None otherwise
		"""
		duration: timedelta = event.duration if event.duration is not None else timedelta(hours=1)		# If event has a specific start time preference, try that first
		if event.startDate.hour != 0 or event.startDate.minute != 0:
			preferredTime: datetime = event.startDate
			if self.isSlotAvailable(preferredTime, duration, existingSchedule):
				return ScheduledEvent(event, preferredTime)

		# Otherwise, find the earliest available slot
		scheduledTime: datetime | None = findEarliestSlot(existingSchedule, duration, dayStart, dayEnd)

		if scheduledTime is not None:
			return ScheduledEvent(event, scheduledTime)
		else:
			print(f"Warning: Could not find time slot for event '{event.name}' on {dayStart.date()}")
			return None

	def isSlotAvailable(self, startTime: datetime, duration: timedelta, existingSchedule: list[ScheduledEvent]) -> bool:
		"""
		Check if a time slot is available without conflicts.

		Args:
			startTime: Proposed start time for the event
			duration: Duration of the event
			existingSchedule: List of already scheduled events

		Returns:
			True if the slot is available, False if there's a conflict
		"""
		endTime: datetime = startTime + duration

		for scheduled in existingSchedule:
			# Check for overlap
			if not (endTime <= scheduled.scheduledTime or startTime >= scheduled.endTime):
				return False

		return True

	def getScheduledEvents(self, date: datetime) -> list[ScheduledEvent]:
		"""
		Get all scheduled events for a specific date.

		Args:
			date: The date to retrieve scheduled events for

		Returns:
			List of ScheduledEvent objects for the specified date
		"""
		dateKey: datetime = date.replace(hour=0, minute=0, second=0, microsecond=0)
		return self.scheduledDays.get(dateKey, [])

	def printSchedule(self, date: datetime) -> None:
		"""
		Print the schedule for a specific day in a formatted manner.

		Args:
			date: The date to print the schedule for
		"""
		dateKey: datetime = date.replace(hour=0, minute=0, second=0, microsecond=0)
		scheduledEvents: list[ScheduledEvent] = self.scheduledDays.get(dateKey, [])

		if not scheduledEvents:
			print(f"No events scheduled for {dateKey.date()}")
			return

		print(f"\nSchedule for {dateKey.date()}:")
		print("-" * 50)

		sortedEvents = sorted(scheduledEvents, key=lambda e: e.scheduledTime)
		for scheduled in sortedEvents:
			startTimeStr: str = scheduled.scheduledTime.strftime("%H:%M")
			endTimeStr: str = scheduled.endTime.strftime("%H:%M")
			print(f"{startTimeStr} - {endTimeStr}: {scheduled.event.name}")
		print("-" * 50)