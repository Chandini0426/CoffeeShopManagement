# Uploads Folder

## Purpose
The uploads folder is the designated location for storing input video files that need to be processed by the Coffee Management System's video analysis pipeline.

## Input File Types

### Supported Video Formats
- MP4
- AVI
- MOV
- MKV
- FLV
- WMV

### File Requirements
- **Minimum resolution:** 480p (720x480)
- **Recommended resolution:** 1080p (1920x1080)
- **Frame rate:** 24-60 FPS
- **Maximum file size:** 2GB per file
- **Codec:** H.264 or H.265 recommended

## Upload Process

1. **Place Video File** → Copy video to this folder
2. **Queue Processing** → System detects new files
3. **Auto-Process** → Backend starts analysis
4. **Generate Results** → Output saved to results folder
5. **Cleanup** → Original file managed per retention policy

## Folder Structure

```
uploads/
├── video_file_1.mp4
├── video_file_2.avi
├── sample_videos/
│   └── demo_video.mp4
└── archived/
    └── processed_videos/
```

## Upload Guidelines

### File Naming Convention
- Use descriptive names: `coffee_shop_20260404_morning.mp4`
- Avoid special characters except underscore and hyphen
- Include date for easy tracking

### Video Content
- Should contain coffee shop operational footage
- Clear visibility of activities and products
- Good lighting conditions recommended
- Audio not required (can be silent)

## Processing Status

### File Processing States
- **Pending** - Waiting in queue for processing
- **Processing** - Currently being analyzed
- **Completed** - Results generated and available
- **Error** - Processing failed, check logs for details

## Storage Management

### Retention Policy
- Uploads kept for **7 days** after processing
- Completed results archived separately
- Manual deletion available through API
- Automatic cleanup of failed uploads

### Space Requirements
- Monitor folder size regularly
- Clear old files to prevent storage issues
- Maximum recommended folder size: 10GB

## API Integration

### Upload via API
```bash
POST /api/upload
Content-Type: multipart/form-data

file: <video_file>
```

### Response
```json
{
  "status": "success",
  "file_id": "upload_12345",
  "filename": "coffee_shop_video.mp4",
  "timestamp": "2026-04-04T10:30:00Z",
  "processing_status": "queued"
}
```

## Notes
- Files are processed in FIFO (First In, First Out) order
- Processing time depends on video length and system load
- Check results folder for outputs after processing completes
- Use file IDs to track processing status
