from .client import Client

class WorkoutClient(Client):
    
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def list_workouts(self):
        pass

    def upload_workout(self, workout_id, workout_data):
        pass

