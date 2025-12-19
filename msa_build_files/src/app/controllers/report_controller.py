# controllers/report_controller.py
from PySide6.QtCore import QObject, Signal
from datetime import date, timedelta

class ReportController(QObject):
    def __init__(self, container):
        self.container = container

    def generate_daily_summary(self, report_date=None):
       pass

    def generate_technician_report(self, technician_name, start_date, end_date):
        pass

    def generate_inventory_movement_report(self, start_date, end_date):
        pass