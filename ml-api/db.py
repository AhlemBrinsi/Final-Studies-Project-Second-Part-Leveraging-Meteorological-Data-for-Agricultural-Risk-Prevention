from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Connect to MongoDB Atlas
client = MongoClient(os.getenv("MONGODB_URI"))

# Choose database and collections
db = client['dashboard']
weather_col = db['weather_predictions']
recommendation_col = db['recommendations']
