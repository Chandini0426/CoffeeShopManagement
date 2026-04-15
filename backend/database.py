import pymongo
from datetime import datetime

# 1. Connect to MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017")

# 2. Database
db = client["coffee_shop"]

# 3. Collections (IMPORTANT separation)
activity_collection = db["activity_log"]
video_collection = db["video_status"]


# ---------------------------------------------------
# ✅ UPDATE PERSON ACTIVITY (BEST METHOD - USING $inc)
# ---------------------------------------------------
def update_person_activity(person_id, action, fps, video_name):
    """
    Updates active/idle time using frame-based accumulation.
    """

    current_time = datetime.now()

    # Decide field
    status_key = "idle_seconds" if action.lower() == "idle" else "active_seconds"

    activity_collection.update_one(
        {
            "person_id": person_id,
            "video_name": video_name
        },
        {
            "$inc": {
                status_key: 1 / fps   # 🔥 adds small time per frame
            },
            "$set": {
                "last_seen": current_time,
                "current_action": action
            },
            "$setOnInsert": {
                "first_seen": current_time
            }
        },
        upsert=True
    )


# ---------------------------------------------------
# ✅ GET ALL ACTIVITY DATA
# ---------------------------------------------------
def get_all_activity():
    data = list(activity_collection.find())

    for item in data:
        item["_id"] = str(item["_id"])

        if "last_seen" in item:
            item["last_seen"] = item["last_seen"].strftime("%Y-%m-%d %H:%M:%S")

        if "first_seen" in item:
            item["first_seen"] = item["first_seen"].strftime("%Y-%m-%d %H:%M:%S")

    return data


# ---------------------------------------------------
# ✅ VIDEO STATUS TRACKING (Progress)
# ---------------------------------------------------
def create_video_record(video_name):
    video_collection.update_one(
        {"video_name": video_name},
        {
            "$set": {
                "progress": 0,
                "status": "processing"
            }
        },
        upsert=True
    )


def update_video_progress(video_name, progress):
    result = video_collection.update_one(
        {"video_name": video_name},
        {"$set": {"progress": progress}}
    )

    # 🔥 DEBUG PRINT
    print("📊 update_video_progress → Matched:", result.matched_count,
          "Modified:", result.modified_count)


def mark_video_completed(video_name):
    result = video_collection.update_one(
        {"video_name": video_name},
        {
            "$set": {
                "progress": 100,
                "status": "completed"
            }
        }
    )

    # 🔥 DEBUG PRINT
    print("✅ mark_video_completed → Matched:", result.matched_count,
          "Modified:", result.modified_count)

def get_video_status(video_name):
    return video_collection.find_one(
        {"video_name": video_name},
        {"_id": 0}
    )