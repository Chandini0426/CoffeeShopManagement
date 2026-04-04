# Results Folder

## Purpose
The results folder stores all output files generated after processing input video files through the Coffee Management System's video analysis pipeline.

## Output Contents

### Processed Videos
- Annotated video files with detected actions
- Video format: MP4, AVI, or other supported formats
- Resolution: Maintains original input resolution

### Detection Results
- Frame-by-frame action detection data
- JSON files containing:
  - Timestamp of detected action
  - Action type/label
  - Confidence score
  - Bounding box coordinates

### Tracking Data
- Object tracking results across video frames
- Track IDs for continuous object identification
- Movement trajectories and paths

### Statistics
- Processing metrics and timestamps
- Performance analytics
- Action frequency reports
- Detection accuracy metrics

## File Structure

```
results/
├── video_outputs/
│   ├── processed_video_1.mp4
│   └── processed_video_2.mp4
├── detections/
│   ├── detection_results_1.json
│   └── detection_results_2.json
├── tracking/
│   ├── tracks_1.json
│   └── tracks_2.json
└── reports/
    └── analysis_report.json
```

## Processing Pipeline

1. **Input** → Video file from uploads folder
2. **Detection** → YOLOv8 model identifies actions
3. **Tracking** → Deep SORT tracks detected objects
4. **Output** → Results saved to this folder
5. **Storage** → Results available for download/analysis

## Output Format

### JSON Structure
```json
{
  "video_info": {
    "filename": "input_video.mp4",
    "duration": 120.5,
    "fps": 30
  },
  "detections": [
    {
      "frame": 0,
      "timestamp": 0.0,
      "action": "pouring",
      "confidence": 0.95,
      "bbox": [100, 150, 250, 300]
    }
  ],
  "tracks": [
    {
      "track_id": 1,
      "action": "serving",
      "frames": [10, 20, 30]
    }
  ]
}
```

## Notes
- Results are automatically generated during video processing
- Files are timestamped for easy identification
- Results can be downloaded for further analysis
- Storage is managed by the system cleanup process
