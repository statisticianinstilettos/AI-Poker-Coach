from pymongo import MongoClient
import streamlit as st
from datetime import datetime
from bson import ObjectId

# Initialize MongoDB connection
@st.cache_resource
def init_connection():
    return MongoClient(st.secrets["MONGODB_URI"])

def get_database():
    client = init_connection()
    return client.poker_coach_db

# User operations
def create_user(username, password):
    """Create a new user"""
    db = get_database()
    users = db.users
    user_data = {
        "_id": ObjectId(),  # MongoDB's internal ID
        "username": username,
        "password": password,
        "created_at": datetime.utcnow()
    }
    result = users.insert_one(user_data)
    return result.inserted_id

def get_user_by_username(username):
    """Get user by their username"""
    db = get_database()
    return db.users.find_one({"username": username})

# Chat operations
def save_chat(username, mode, messages):
    """Save chat with username reference"""
    db = get_database()
    chats = db.chats
    chat_data = {
        "_id": ObjectId(),  # MongoDB's internal ID
        "username": username,
        "mode": mode,
        "messages": messages,
        "timestamp": datetime.utcnow()
    }
    return chats.insert_one(chat_data)

def get_user_chats(username):
    """Get chats by username"""
    db = get_database()
    return list(db.chats.find({"username": username}).sort("timestamp", -1))

# Tournament results operations
def save_tournament_result(username, tournament_data):
    """Save tournament result with username reference"""
    db = get_database()
    tournaments = db.tournaments
    tournament_data.update({
        "_id": ObjectId(),  # MongoDB's internal ID
        "username": username,
        "timestamp": datetime.utcnow()
    })
    return tournaments.insert_one(tournament_data)

def get_user_tournament_results(username):
    """Get tournament results by username"""
    db = get_database()
    return list(db.tournaments.find({"username": username}).sort([
        ("tournament_date", -1),  # Sort by date first (most recent first)
        ("timestamp", -1)  # Then by timestamp
    ]))

def get_user_stats(username):
    """Get user stats by username"""
    db = get_database()
    tournaments = db.tournaments
    pipeline = [
        {"$match": {"username": username}},
        {"$group": {
            "_id": None,
            "total_tournaments": {"$sum": 1},
            "total_profit": {"$sum": {"$subtract": ["$prize_won", "$total_investment"]}},
            "total_investment": {"$sum": "$total_investment"},
            "itm_finishes": {"$sum": {"$cond": [{"$gt": ["$prize_won", 0]}, 1, 0]}}
        }}
    ]
    stats = list(tournaments.aggregate(pipeline))
    if stats:
        stats = stats[0]
        stats["roi"] = (stats["total_profit"] / stats["total_investment"] * 100) if stats["total_investment"] > 0 else 0
        stats["itm_percentage"] = (stats["itm_finishes"] / stats["total_tournaments"] * 100) if stats["total_tournaments"] > 0 else 0
        return stats
    return None 