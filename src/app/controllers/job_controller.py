# controllers/job_controller.py
from PySide6.QtCore import QObject, Signal

class JobController(QObject):
    def __init__(self, container):
        self.container = container

    def create_job(self, job_data):
        pass

    def update_job_status(self, job_id, new_status):
        pass

    def get_jobs_by_status(self, status):
        pass

    def assign_technician(self, job_id, technician_name):
        pass