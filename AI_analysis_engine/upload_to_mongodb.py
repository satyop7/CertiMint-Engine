"""
MongoDB upload script
"""
import json
import os
import datetime

def upload_result():
    """Upload result to MongoDB"""
    try:
        from pymongo import MongoClient
        
        # MongoDB connection string
        connection_string = 'mongodb+srv://sambhranta1123:SbGgIK3dZBn9uc2r@cluster0.jjcc5or.mongodb.net/'
        db_name = 'certimint'
        collection_name = 'assignments'
        
        result_file = 'result/result.json'
        
        # Connect to MongoDB
        print('Connecting to MongoDB...')
        client = MongoClient(connection_string)
        db = client[db_name]
        collection = db[collection_name]
        
        # Load result JSON
        if os.path.exists(result_file):
            with open(result_file, 'r') as f:
                result_data = json.load(f)
            
            # Add upload timestamp
            result_data['upload_timestamp'] = datetime.datetime.now().isoformat()
            
            # Insert document into MongoDB
            print('Uploading result to MongoDB...')
            insert_result = collection.insert_one(result_data)
            
            print(f'✓ Successfully uploaded result to MongoDB (Document ID: {insert_result.inserted_id})')
        else:
            print(f'Error: Result file not found: {result_file}')
            # Try alternative file names
            for alt_file in ['result/result_1.json', 'result/result_2.json']:
                if os.path.exists(alt_file):
                    print(f'Found alternative result file: {alt_file}')
                    with open(alt_file, 'r') as f:
                        result_data = json.load(f)
                    result_data['upload_timestamp'] = datetime.datetime.now().isoformat()
                    insert_result = collection.insert_one(result_data)
                    print(f'✓ Successfully uploaded result to MongoDB (Document ID: {insert_result.inserted_id})')
                    break
        
        client.close()
        
    except ImportError:
        print("PyMongo not available")
    except Exception as e:
        print(f'Error uploading to MongoDB: {e}')

def clear_data_directory():
    """Clear data directory except info.json"""
    data_dir = "data"
    
    for filename in os.listdir(data_dir):
        if filename != "info.json":
            file_path = os.path.join(data_dir, filename)
            try:
                os.remove(file_path)
                print(f"Removed: {file_path}")
            except Exception as e:
                print(f"Error removing {file_path}: {e}")

if __name__ == "__main__":
    upload_result()
    clear_data_directory()