import numpy as np
import time

class ActionRecognizer:
    def __init__(self):
        self.worker_states = {}
        self.idle_threshold_time = 30  # seconds

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
            }

        state = self.worker_states[worker_id]

        # Landmarks
        r_wrist = [pose_landmarks.landmark[16].x * w, pose_landmarks.landmark[16].y * h]
        r_elbow = [pose_landmarks.landmark[14].x * w, pose_landmarks.landmark[14].y * h]
        r_shoulder = [pose_landmarks.landmark[12].x * w, pose_landmarks.landmark[12].y * h]

        l_wrist = [pose_landmarks.landmark[15].x * w, pose_landmarks.landmark[15].y * h]
        l_elbow = [pose_landmarks.landmark[13].x * w, pose_landmarks.landmark[13].y * h]
        l_shoulder = [pose_landmarks.landmark[11].x * w, pose_landmarks.landmark[11].y * h]

        # Metrics
        displacement = self.calculate_distance(state["last_position"], current_position)
        r_angle = self.calculate_angle(r_shoulder, r_elbow, r_wrist)
        l_angle = self.calculate_angle(l_shoulder, l_elbow, l_wrist)

        # 🔥 SIMPLE LOGIC
        if displacement > 10 or r_angle < 140 or l_angle < 140:
            action = "Active"
            state["idle_start_time"] = current_time
        else:
            idle_time = current_time - state["idle_start_time"]
            if idle_time > self.idle_threshold_time:
                action = "Idle"
            else:
                action = "Active"  # short pause still considered active

        state["last_position"] = current_position
        return action, (0, 255, 0) if action == "Active" else (0, 0, 255)