import cv2
import numpy as np
import os
import shutil
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from datetime import datetime
from database import collection, get_all_activity

# --- 1. CORE AI IMPORTS & MONKEY PATCH ---
if not hasattr(np, 'dtypes'):
    class MockDTypes: StringDType = None
    np.dtypes = MockDTypes()

import mediapipe as mp
from ultralytics import YOLO
from tracker_utils import Tracker
from action_recognizer import ActionRecognizer

app = FastAPI()

# Enable CORS so your separate frontend can talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with your frontend URL
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
RESULT_DIR = "results"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

# --- 2. INITIALIZE MODELS (Global to keep them in memory) ---
model = YOLO('yolov8n.pt')
my_tracker = Tracker()
recognizer = ActionRecognizer()
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5)
mp_draw = mp.solutions.drawing_utils

# Process video file with detection, tracking, and action recognition
def process_video_task(input_path: str, output_path: str):
    """The heavy lifting function that processes the video file."""
    cap = cv2.VideoCapture(input_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        # Object Detection
        results = model(frame, verbose=False)[0]
        detections = [[*r[:5]] for r in results.boxes.data.tolist() if int(r[5]) == 0]

        # Tracking
        my_tracker.update(frame, detections)

        for track in my_tracker.tracks:
            track_id = track.track_id
            tx1, ty1, tx2, ty2 = map(int, track.bbox)
            tx1, ty1 = max(0, tx1), max(0, ty1)
            
            person_crop = frame[ty1:ty2, tx1:tx2]
            if person_crop.size == 0: continue

            person_rgb = cv2.cvtColor(person_crop, cv2.COLOR_BGR2RGB)
            pose_results = pose.process(person_rgb)

            if pose_results.pose_landmarks:
                center = ((tx1 + tx2) / 2, (ty1 + ty2) / 2)
                action, color, _ = recognizer.determine_action(
                    track_id, pose_results.pose_landmarks, center, frame.shape[:2]
                )

                # Update MongoDB
                status_key = "idle_seconds" if action.lower() == "idle" else "active_seconds"
                collection.update_one(
                    {"person_id": track_id},
                    {
                        "$inc": {status_key: 1/fps}, # Increment by actual time
                        "$set": {"last_seen": datetime.now(), "current_action": action}
                    },
                    upsert=True
                )

                # Drawing
                cv2.rectangle(frame, (tx1, ty1), (tx2, ty2), color, 2)
                cv2.putText(frame, f"ID {track_id}: {action}", (tx1, ty1-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        out.write(frame)

    cap.release()
    out.release()

# Handle video upload and start background processing task
@app.post("/upload-video/")
async def upload_video(file: UploadFile = File(...)):
    """Receives file from Frontend"""
    input_path = os.path.join(UPLOAD_DIR, file.filename)
    output_path = os.path.join(RESULT_DIR, f"processed_{file.filename}")
    
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Process the video
    process_video_task(input_path, output_path)
    
    return {"message": "Processing complete", "filename": f"processed_{file.filename}"}

# Retrieve all worker activity statistics from database
@app.get("/get-stats")
async def get_stats():
    """Returns the worker activity data as JSON"""
    try:
        data = get_all_activity()
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Retrieve activity statistics for a specific worker by ID
@app.get("/get-stats/{worker_id}")
async def get_worker_stats(worker_id: int):
    worker = collection.find_one({"person_id": worker_id})
    if worker:
        worker["_id"] = str(worker["_id"])
        return worker
    return {"error": "Worker not found"}