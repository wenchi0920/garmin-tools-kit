import pytest
from client.workout_parser import WorkoutDSLParser

def test_yasso_800_parsing():
    dsl = {
        "workouts": {
            "Yasso 800": [
                {"warmup": "15min @H(z2)"},
                {"repeat(10)": [
                    {"interval": "800m @P(4:20-4:30)"},
                    {"recovery": "3:30 @H(z1)"}
                ]},
                {"cooldown": "10min"}
            ]
        }
    }
    parser = WorkoutDSLParser(dsl)
    workouts = parser.get_all_workouts()
    
    assert len(workouts) == 1
    workout = workouts[0]
    assert workout["workoutName"] == "Yasso 800"
    
    # Garmin Structure: WorkoutModel -> workoutSegments -> workoutSteps
    steps = workout["workoutSegments"][0]["workoutSteps"]
    # warmup (1) + repeat_group (1) + cooldown (1) = 3
    assert len(steps) == 3
    
    # Verify Repeat Group
    repeat_step = steps[1]
    assert repeat_step["stepType"]["stepTypeKey"] == "repeat"
    assert repeat_step["numberOfIterations"] == 10
    assert len(repeat_step["workoutSteps"]) == 2

def test_variable_definitions():
    dsl = {
        "definitions": {
            "TargetPace": "4:00-4:10",
            "EasyHR": "z1"
        },
        "workouts": {
            "Variable Test": [
                {"interval": "1km @P($TargetPace)"}
            ]
        }
    }
    parser = WorkoutDSLParser(dsl)
    workouts = parser.get_all_workouts()
    step = workouts[0]["workoutSegments"][0]["workoutSteps"][0]
    
    # 4:00 min/km = 1000 / 240 = 4.166... m/s
    # 4:10 min/km = 1000 / 250 = 4.0 m/s
    assert step["targetValueOne"] == pytest.approx(4.0)
    assert step["targetValueTwo"] == pytest.approx(4.166, rel=1e-3)
