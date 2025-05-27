from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import logging
from urllib.parse import quote_plus
import os

# Globals to hold MongoDB connection
client = None
db = None

def connect_db():
    """
    Connects to MongoDB using credentials from environment variables.
    Initializes the `client` and `db` globals for use by other functions.
    Logs success or failure for visibility in production.
    """
    global client, db
    try:
        # Retrieve MongoDB username and password from environment variables
        username = os.getenv("MONGODB_USERNAME")
        password = os.getenv("MONGODB_PASSWORD")

        if not username or not password:
            raise ValueError("MongoDB credentials are missing in environment variables.")

        # Encode special characters in credentials
        encoded_username = quote_plus(username)
        encoded_password = quote_plus(password)

        # Build the MongoDB connection URI
        mongo_uri = (
            f"mongodb+srv://{encoded_username}:{encoded_password}@"
            "chapo-bot3.odmsslj.mongodb.net/chapo_db"
            "?retryWrites=true&w=majority&appName=Chapo-bot3"
        )

        # Create MongoClient and get default DB (from URI path: /chapo_db)
        client = MongoClient(mongo_uri, tls=True)
        db = client.get_default_database()

        if db is None:
            raise ValueError(
                "❌ No default database found in URI. Make sure your URI ends with /chapo_db"
            )

        logging.info("✅ MongoDB connection established.")
    except Exception as e:
        logging.error(f"❌ MongoDB startup error: {e}")
        # Optional: raise to fail-fast, or just log and let the program continue
        # raise

def save_interaction(log: dict) -> bool:
    """
    Saves a user interaction (log) to the MongoDB 'logs' collection.
    Adds a UTC timestamp to each log entry.
    Returns True on success, False on failure (e.g. no DB, connection error).
    """
    if db is None:
        logging.warning("⚠️ Cannot save interaction: No database connection.")
        return False
    try:
        log["timestamp"] = datetime.utcnow()
        db.logs.insert_one(log)
        logging.info("📝 Interaction saved to DB.")
        return True
    except PyMongoError as e:
        logging.error(f"❌ Failed to save interaction: {e}")
        return False

def get_interactions(session_id=None, limit=10):
    """
    Retrieves the most recent interactions (logs) from the 'logs' collection.
    Optionally filters by session_id and limits the result count.
    Returns a list of interaction dictionaries.
    """
    if db is None:
        logging.warning("⚠️ Cannot retrieve interactions: No database connection.")
        return []
    try:
        query = {}
        if session_id:
            query["session_id"] = session_id

        interactions = db.logs.find(query).sort("timestamp", -1).limit(limit)
        return list(interactions)
    except PyMongoError as e:
        logging.error(f"❌ Failed to retrieve interactions: {e}")
        return []

def get_interaction_by_timestamp(session_id, timestamp):
    """
    Retrieves a single interaction log by session_id and exact timestamp.
    Returns the interaction document if found, else None.
    """
    if db is None:
        logging.warning("⚠️ Cannot retrieve interaction: No database connection.")
        return None
    try:
        query = {
            "session_id": session_id,
            "timestamp": timestamp
        }
        interaction = db.logs.find_one(query)
        return interaction
    except PyMongoError as e:
        logging.error(f"❌ Failed to retrieve interaction by timestamp: {e}")
        return None

def log_evaluation_metric(log: dict) -> bool:
    """
    Logs evaluation metrics to the 'evaluation_metrics' collection in MongoDB.
    Each log gets a UTC timestamp.
    Prints summary to console for monitoring/debugging.
    Returns True if saved, False on error.
    """
    try:
        if db is None:
            logging.warning("⚠️ Cannot log evaluation metric: No database connection.")
            return False
        
        # Ensure the 'evaluation_metrics' collection exists
        evaluation_metrics = db['evaluation_metrics']
        
        log["timestamp"] = datetime.utcnow()
        result = evaluation_metrics.insert_one(log)
        
        # Print out the logged metrics for quick CLI debugging
        print("\n📊 Evaluation metric saved to MongoDB:")
        print(f"  ID: {result.inserted_id}")
        print(f"  User Input: {log['user_input']}")
        print(f"  True Intent: {log['true_intent']}")
        print(f"  Predicted Intent: {log['predicted_intent']}")
        print(f"  Accuracy: {log['accuracy']:.2f}")
        print(f"  Precision: {log['precision']:.2f}")
        print(f"  Recall: {log['recall']:.2f}")
        
        logging.info(f"📊 Evaluation metric saved with ID: {result.inserted_id}")
        return True
        
    except PyMongoError as e:
        print(f"❌ Error logging evaluation metric: {e}")
        logging.error(f"❌ Failed to log evaluation metric: {e}")
        return False
