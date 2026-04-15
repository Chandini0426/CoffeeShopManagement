from ultralytics import YOLO

class YOLODetector:
    def __init__(self, model_path="yolov8n.pt"):
        self.model = YOLO(model_path)

    def detect(self, frame):
        """
        Returns detections in format:
        [x1, y1, x2, y2, conf, cls]
        """
        results = self.model(frame, verbose=False)

        detections = []

        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0]
                conf = float(box.conf[0])
                cls = int(box.cls[0])

                detections.append([
                    int(x1), int(y1), int(x2), int(y2),
                    conf, cls
                ])

        return detections