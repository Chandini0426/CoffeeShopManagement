import supervision as sv
import numpy as np

class TrackerUtil:
    def __init__(self):
        self.tracker = sv.ByteTrack()

    def update(self, detections):
        """
        detections: list [x1,y1,x2,y2,conf,cls]
        """

        if len(detections) == 0:
            return []

        det_array = np.array(detections)

        # supervision expects:
        # xyxy, confidence, class_id
        xyxy = det_array[:, :4]
        confidence = det_array[:, 4]
        class_id = det_array[:, 5]

        sv_detections = sv.Detections(
            xyxy=xyxy,
            confidence=confidence,
            class_id=class_id
        )

        tracked = self.tracker.update_with_detections(sv_detections)

        return tracked