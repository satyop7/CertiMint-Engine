"""
MongoDB uploader for results
"""
import json
import os

def upload_to_mongodb(result_data):
    """Upload result to MongoDB"""
    try:
        from pymongo import MongoClient
        
        # MongoDB connection string
        connection_string = "your connection string here"
        
        client = MongoClient(connection_string)
        db = client['certimint']
        collection = db['assignments']
        
        # Insert or update result
        filter_query = {"assignment_id": result_data.get('assignment_id')}
        collection.replace_one(filter_query, result_data, upsert=True)
        
        print(f"Result uploaded to MongoDB: {result_data.get('assignment_id')}")
        client.close()
        
    except ImportError:
        print("PyMongo not available - saving to local backup")
        # Fallback to local storage
        with open(f"result/backup_{result_data.get('assignment_id')}.json", 'w') as f:
            json.dump(result_data, f, indent=2)
        print("Result saved to local backup file")
        
    except Exception as e:
        print(f"Error uploading to MongoDB: {e}")
        # Fallback to local storage
        with open(f"result/backup_{result_data.get('assignment_id')}.json", 'w') as f:
            json.dump(result_data, f, indent=2)
        print("Result saved to local backup file")

def clear_data_directory():
    """Clear all files from data directory except info.json"""
    data_dir = "data"
    
    if not os.path.exists(data_dir):
        return
    
    for filename in os.listdir(data_dir):
        if filename != "info.json":
            file_path = os.path.join(data_dir, filename)
            try:
                os.remove(file_path)
                print(f"Removed: {file_path}")
            except Exception as e:
                print(f"Error removing {file_path}: {e}")