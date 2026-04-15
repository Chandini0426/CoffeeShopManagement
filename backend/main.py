import cv2
import os
import shutil
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from database import (
    update_video_progress,
    mark_video_completed,
    create_video_record,
    get_video_status,
    update_person_activity
)

from ultralytics import YOLO
import mediapipe as mp
from action_recognizer import ActionRecognizer

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
RESULT_DIR = "results"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

model = YOLO("yolov8n.pt")
recognizer = ActionRecognizer()

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=0,
    min_detection_confidence=0.5
)


# ---------------------------------------------------
# 🔥 VIDEO PROCESSING
# ---------------------------------------------------
def process_video_task(input_path: str, output_path: str, video_name: str):
    try:
        print("🔥 Processing started:", video_name)

        cap = cv2.VideoCapture(input_path)

        if not cap.isOpened():
            print("❌ Video not opened")
            return

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30

        # ✅ FIX: Proper VideoWriter
        out = cv2.VideoWriter(
            output_path,
            cv2.VideoWriter_fourcc(*'mp4v'),
            fps,
            (width, height)
        )

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
        processed_frames = 0

        frame_skip = 2
        POSE_INTERVAL = 5
        last_actions = {}

        results = model.track(
            input_path,
            persist=True,
            stream=True,
            classes=0,
            tracker="bytetrack.yaml"
        )

        for r in results:
            frame = r.orig_img
            processed_frames += 1

            if processed_frames % frame_skip != 0:
                out.write(frame)
                continue

            if r.boxes is not None and r.boxes.id is not None:
                boxes = r.boxes.xyxy.cpu().numpy()
                ids = r.boxes.id.cpu().numpy()

                for box, track_id in zip(boxes, ids):
                    x1, y1, x2, y2 = map(int, box)

                    action_text = "Detecting..."
                    color = (255, 255, 255)

                    if track_id in last_actions:
                        action_text, color = last_actions[track_id]

                    if processed_frames % POSE_INTERVAL == 0:
                        person_crop = frame[y1:y2, x1:x2]

                        if person_crop.size != 0:
                            rgb = cv2.cvtColor(person_crop, cv2.COLOR_BGR2RGB)
                            result_pose = pose.process(rgb)

                            if result_pose.pose_landmarks:
                                action, color = recognizer.determine_action(
                                    int(track_id),
                                    result_pose.pose_landmarks,
                                    ((x1 + x2)//2, (y1 + y2)//2),
                                    (frame.shape[0], frame.shape[1])
                                )
                                action_text = action
                                last_actions[track_id] = (action_text, color)

                    update_person_activity(
                        person_id=int(track_id),
                        action=action_text,
                        fps=fps,
                        video_name=video_name
                    )

                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(
                        frame,
                        f"ID {int(track_id)} - {action_text}",
                        (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        color,
                        2
                    )

            # ✅ Progress
            progress = (processed_frames / total_frames) * 100
            update_video_progress(video_name, progress)

            out.write(frame)

        cap.release()
        out.release()

        print("🎉 Completed:", video_name)
        mark_video_completed(video_name)

    except Exception as e:
        print("❌ ERROR:", str(e))


# ---------------------------------------------------
# 🔥 UPLOAD API
# ---------------------------------------------------
@app.post("/upload-video/")
async def upload_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)):

    video_name = file.filename.strip()
    name_without_ext = os.path.splitext(video_name)[0]

    input_path = os.path.join(UPLOAD_DIR, video_name)
    output_path = os.path.join(RESULT_DIR, f"processed_{name_without_ext}.mp4")

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    create_video_record(video_name)

    background_tasks.add_task(
        process_video_task,
        input_path,
        output_path,
        video_name
    )

    return {
        "message": "Processing started",
        "filename": video_name
    }


# ---------------------------------------------------
# 🔥 GET VIDEO
# ---------------------------------------------------
from fastapi import Request, HTTPException
from fastapi.responses import StreamingResponse
import os

@app.get("/video/{filename}")
async def get_video(filename: str, request: Request):
    path = os.path.join(RESULT_DIR, filename)

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")

    file_size = os.path.getsize(path)
    range_header = request.headers.get("range")

    start = 0
    end = file_size - 1

    if range_header:
        bytes_range = range_header.replace("bytes=", "").split("-")
        start = int(bytes_range[0])
        if bytes_range[1]:
            end = int(bytes_range[1])

    chunk_size = end - start + 1

    def iterfile():
        with open(path, "rb") as f:
            f.seek(start)
            yield f.read(chunk_size)

    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(chunk_size),
        "Content-Type": "video/mp4",
    }

    return StreamingResponse(iterfile(), status_code=206, headers=headers)
# ---------------------------------------------------
# 🔥 STATUS API
# ---------------------------------------------------
@app.get("/video-status/{filename}")
async def video_status(filename: str):
    data = get_video_status(filename)

    if not data:
        return {"progress": 0, "status": "processing"}

    return {
        "progress": data.get("progress", 0),
        "status": data.get("status", "processing")
    }


# ---------------------------------------------------
# 🔥 DASHBOARD
# ---------------------------------------------------
@app.get("/dashboard/")
async def dashboard_data():
    from database import activity_collection

    data = list(activity_collection.find({}, {
        "_id": 0,
        "person_id": 1,
        "active_seconds": 1,
        "idle_seconds": 1
    }))

    return data