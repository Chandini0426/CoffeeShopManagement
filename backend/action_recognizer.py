import numpy as np
import time

class ActionRecognizer:
    def __init__(self):
        self.worker_states = {}
        # Adjust these based on your camera's frame rate
        self.idle_buffer_time = 10    # 10 seconds of no movement = Waiting
        self.idle_threshold_time = 30 # 30 seconds of no movement = Idle

    def calculate_distance(self, p1, p2):
        return np.linalg.norm(np.array(p1) - np.array(p2))

    def calculate_angle(self, a, b, c):
        a, b, c = np.array(a), np.array(b), np.array(c)
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(radians * 180.0 / np.pi)
        return 360 - angle if angle > 180 else angle

    def determine_action(self, worker_id, pose_landmarks, current_position, frame_shape):
        
        current_time = time.time()
        h, w = frame_shape

        if worker_id not in self.worker_states:
            self.worker_states[worker_id] = {
                "last_position": current_position,
                "idle_start_time": current_time,
                "action_history": []
            }

        state = self.worker_states[worker_id]
        
        # Get Landmarks (Right Side)
        r_wrist = [pose_landmarks.landmark[16].x * w, pose_landmarks.landmark[16].y * h]
        r_elbow = [pose_landmarks.landmark[14].x * w, pose_landmarks.landmark[14].y * h]
        r_shoulder = [pose_landmarks.landmark[12].x * w, pose_landmarks.landmark[12].y * h]

        # Get Landmarks (Left Side) - Workers use both hands!
        l_wrist = [pose_landmarks.landmark[15].x * w, pose_landmarks.landmark[15].y * h]
        l_elbow = [pose_landmarks.landmark[13].x * w, pose_landmarks.landmark[13].y * h]
        l_shoulder = [pose_landmarks.landmark[11].x * w, pose_landmarks.landmark[11].y * h]

        # Calculate metrics
        displacement = self.calculate_distance(state["last_position"], current_position)
        r_angle = self.calculate_angle(r_shoulder, r_elbow, r_wrist)
        l_angle = self.calculate_angle(l_shoulder, l_elbow, l_wrist)
        
        # Logic Priority Tree
        action = "Active"
        color = (0, 255, 0)

        # 1. Movement Logic
        if displacement > 10:
            action = "Moving"
            color = (255, 255, 0)
            state["idle_start_time"] = current_time # Reset idle timer when moving
        
        # 2. Work Logic (Arms bent = Working at counter)
        elif r_angle < 140 or l_angle < 140:
            action = "Working" # Brewing/Preparing
            color = (0, 255, 0)
            state["idle_start_time"] = current_time
            
        # 3. Idle/Waiting Logic
        else:
            idle_duration = current_time - state["idle_start_time"]
            if idle_duration > self.idle_threshold_time:
                action = "Idle"
                color = (0, 0, 255)
            elif idle_duration > self.idle_buffer_time:
                action = "Waiting"
                color = (0, 255, 255)

        state["last_position"] = current_position
        return action, color, min(r_angle, l_angle)