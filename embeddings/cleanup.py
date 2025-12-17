from backend.services.qdrant_service import qdrant_service

def wipe_collection():
    client = qdrant_service.client
    client.delete_collection(qdrant_service.collection_name)
    print("Collection deleted")

if __name__ == "__main__":
    wipe_collection()
