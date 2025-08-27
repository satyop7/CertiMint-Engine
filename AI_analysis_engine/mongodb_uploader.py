"""
MongoDB uploader for results
"""
import json
import os

def upload_to_mongodb(result_data):
    """Upload result to MongoDB and return document ID"""
    try:
        from pymongo import MongoClient
        
        # MongoDB connection string
        connection_string = "mongodb+srv://sambhranta1123:SbGgIK3dZBn9uc2r@cluster0.jjcc5or.mongodb.net/"
        
        client = MongoClient(connection_string)
        db = client['certimint']
        collection = db['assignments']
        
        # Insert or update result
        filter_query = {"assignment_id": result_data.get('assignment_id')}
        result = collection.replace_one(filter_query, result_data, upsert=True)
        
        # Get the document ID
        if result.upserted_id:
            doc_id = result.upserted_id
        else:
            # Find the existing document to get its ID
            doc = collection.find_one(filter_query)
            doc_id = doc['_id'] if doc else None
        
        client.close()
        return doc_id
        
    except ImportError:
        print("PyMongo not available - saving to local backup")
        # Fallback to local storage
        with open(f"result/backup_{result_data.get('assignment_id')}.json", 'w') as f:
            json.dump(result_data, f, indent=2)
        return None
        
    except Exception as e:
        print(f"Error uploading to MongoDB: {e}")
        # Fallback to local storage
        with open(f"result/backup_{result_data.get('assignment_id')}.json", 'w') as f:
            json.dump(result_data, f, indent=2)
        return None

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