import pymongo
from datetime import datetime

# 1. Establish the connection
uri = "mongodb://localhost:27017"
client = pymongo.MongoClient(uri)

# 2. Select the database
db = client["coffee_shop"]

# 3. Select the collection
collection = db["activity_log"]

# Update active/idle time for a specific person ID in the database
def update_person_activity(person_id, status="active"):
    """
    Updates the active/idle time for a specific DeepSORT ID.
    """
    current_time = datetime.now()
    
    # Find the existing record for this person
    person_data = collection.find_one({"person_id": person_id})

    if not person_data:
        # First time seeing this person
        new_record = {
            "person_id": person_id,
            "first_seen": current_time,
            "last_seen": current_time,
            "total_active_seconds": 0,
            "status": status
        }
        collection.insert_one(new_record)
        print(f"Started tracking Person {person_id}")
    else:
        # Calculate duration since last seen
        last_seen = person_data["last_seen"]
        duration = (current_time - last_seen).total_seconds()
        
        # Update logic: increment active time if they are moving/present
        collection.update_one(
            {"person_id": person_id},
            {
                "$set": {
                    "last_seen": current_time,
                    "status": status
                },
                "$inc": {"total_active_seconds": duration}
            }
        )

# Fetch all activity records and convert to JSON-friendly format
def get_all_activity():
    """Fetches all records and converts them to a list of dicts"""
    # Fetch all records from the collection
    data = list(collection.find())
    
    for item in data:
        # 1. Convert ObjectId to string so JSON can read it
        item["_id"] = str(item["_id"])
        
        # 2. Format datetime objects to readable strings
        if "last_seen" in item:
            item["last_seen"] = item["last_seen"].strftime("%Y-%m-%d %H:%M:%S")
        if "first_seen" in item:
            item["first_seen"] = item["first_seen"].strftime("%Y-%m-%d %H:%M:%S")
            
    return data        

# --- DEEPSORT INTEGRATION EXAMPLE ---
# Inside your DeepSORT loop:
# for track in tracker.tracks:
#     if not track.is_confirmed() or track.time_since_update > 1:
#         continue
#     
#     person_id = track.track_id
#     update_person_activity(person_id, status="active")