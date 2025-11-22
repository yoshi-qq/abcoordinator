from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QCalendarWidget, QLabel
import sys

class CalendarApp(QWidget):
	def __init__(self) -> None:
		super.__init__()
		self.setWindowTitle("ABCoordinator")
		self.setGeometry(100, 100, 400, 350)

		self.layout = QVBoxLayout()

		self.calendar = QCalendarWidget(self)
		self.layout.addWidget(self.calendar)

		self.date_label = QLabel("Selected Date: None", self)
		self.layout.addWidget(self.date_label)

		self.calendar.selectionChanged.connect(self.on_date_changed)

		self.setLayout(self.layout)

	def run(self) -> None:
		app = QApplication(sys.argv)
		self.show()
		sys.exit(app.exec_())

app = CalendarApp()