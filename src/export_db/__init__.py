"""
Firestore Data Export Utility

This module provides functionality to export Firestore collection data to a JSON file,
which can be used to seed the Firestore emulator for development and testing purposes.

The exported data is serialized in a format compatible with the emulator seeding process,
handling special Firestore data types (like timestamps) appropriately.

Usage:
    1. Execute this script to export production Firestore data to JSON format
    2. Copy the generated firestore-data.json file to the emulator seeds directory:
       C:\\Users\\quokka\\Documents\\Engineering Fun\\muni_fullstack\\packages\\functions\\lib\\src\\emulators
    3. Seed the emulator with the exported data by running:
       npm run seed-emulators

Note:
    Ensure you have the necessary Firebase credentials configured before running this script.
"""

import json
from utils.credentials import initialize_firestore

db = initialize_firestore()

def convert_to_serializable(obj):
    """
    Converts Firestore document data to JSON-serializable format.
    
    Handles special cases including:
    - Firestore timestamps (converted to a custom format with seconds and nanoseconds)
    - Nested dictionaries and lists (recursively processed)
    - Basic data types (strings, numbers, booleans, None)
    
    Args:
        obj: Any data type from a Firestore document
        
    Returns:
        JSON-serializable version of the input object
        
    Raises:
        Exception: If conversion fails, with debug information about the problematic object
    """
    try:
        # Log non-standard types for debugging purposes
        if not isinstance(obj, (str, int, float, bool, dict, list, type(None))):
            print(f"Converting type: {type(obj)}, value: {obj}")
            
        if hasattr(obj, '_seconds'):  # Handle Firestore timestamp
            return {
                "__type__": "timestamp",
                "seconds": obj._seconds,
                "nanoseconds": obj._nanoseconds
            }
        elif isinstance(obj, dict):  # Process nested dictionaries
            return {k: convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):  # Process nested lists
            return [convert_to_serializable(v) for v in obj]
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            # Fallback for unsupported types
            return str(obj)
    except Exception as e:
        print(f"Error converting object: {type(obj)}, Error: {str(e)}")
        raise

def get_all_data():
    """
    Retrieves and exports all collections from Firestore to a JSON file.
    
    Processes each collection and document, converting all data to a serializable format.
    The resulting JSON structure maintains the Firestore hierarchy:
    {
        "collection_name": {
            "document_id": {
                // document data
            }
        }
    }
    
    Raises:
        Exception: If there's an error processing any document, with details about the failed document
    """
    collections = db.collections()
    result = {}

    for collection in collections:
        collection_name = collection.id
        print(f"Processing collection: {collection_name}")
        result[collection_name] = {}

        docs = collection.stream()
        for doc in docs:
            try:
                data = doc.to_dict()
                result[collection_name][doc.id] = convert_to_serializable(data)
            except Exception as e:
                print(f"Error processing document {doc.id}: {str(e)}")
                raise

    # Export the processed data to JSON file
    with open("export_db/firestore-data.json", "w") as json_file:
        json.dump(result, json_file, indent=4)

# Execute the export process
get_all_data()
print("Firestore data exported to export_db/firestore-data.json")
