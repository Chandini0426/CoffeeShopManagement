import numpy as np
import cv2

class ROIFilter:
    def __init__(self, polygon_points):
        """
        polygon_points: list of (x, y)
        Example: [(100,100), (500,100), (500,400), (100,400)]
        """
        self.polygon = np.array(polygon_points, np.int32)

    def apply_mask(self, frame):
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)

        cv2.fillPoly(mask, [self.polygon], 255)

        filtered = cv2.bitwise_and(frame, frame, mask=mask)
        return filtered

    def draw_zone(self, frame):
        """Optional visualization"""
        cv2.polylines(frame, [self.polygon], True, (0, 255, 0), 2)
        return frame