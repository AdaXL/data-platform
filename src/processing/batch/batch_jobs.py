class BatchJob:
    def __init__(self):
        self.status = "Not Started"

    def run_job(self):
        self.status = "Running"
        # Logic for running the batch job
        self.status = "Completed"

    def get_status(self):
        return self.status
