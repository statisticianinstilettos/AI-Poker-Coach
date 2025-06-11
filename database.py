from pymongo import MongoClient
import streamlit as st
from datetime import datetime
from bson import ObjectId
import os
import json
from src.utils.calculations import calculate_roi

# Initialize MongoDB connection - clean and simple
@st.cache_resource
def get_db():
    uri = st.secrets["MONGODB_URI"]
    client = MongoClient(uri)
    return client.poker_coach_db

# User operations
def create_user(username, password):
    """Create a new user"""
    db = get_db()
    users = db.users
    user_data = {
        "_id": ObjectId(),  # MongoDB's internal ID
        "username": username,
        "password": password,
        "created_at": datetime.utcnow()
    }
    try:
        result = users.insert_one(user_data)
        return result.inserted_id
    except Exception as e:
        st.error(f"Failed to create user: {str(e)}")
        return None

def get_user_by_username(username):
    """Get user by their username"""
    db = get_db()
    return db.users.find_one({"username": username})

# Chat operations
def save_chat(username, mode, messages):
    """Save chat with username reference"""
    db = get_db()
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
    db = get_db()
    return list(db.chats.find({"username": username}).sort("timestamp", -1))

# Tournament results operations
def save_tournament_result(username, tournament_data):
    """Save tournament result with username reference"""
    db = get_db()
    tournaments = db.tournaments
    tournament_data.update({
        "_id": ObjectId(),  # MongoDB's internal ID
        "username": username,
        "timestamp": datetime.utcnow()
    })
    return tournaments.insert_one(tournament_data)

def get_user_tournament_results(username):
    """Get tournament results by username"""
    db = get_db()
    return list(db.tournaments.find({"username": username}).sort([
        ("tournament_date", -1),  # Sort by date first (most recent first)
        ("timestamp", -1)  # Then by timestamp
    ]))

def get_user_stats(username):
    """Get user stats by username"""
    db = get_db()
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
        stats["roi"] = calculate_roi(stats["total_profit"], stats["total_investment"])
        stats["itm_percentage"] = (stats["itm_finishes"] / stats["total_tournaments"] * 100) if stats["total_tournaments"] > 0 else 0
        return stats
    return None

def delete_user_tournament_results(username):
    """Delete all tournament results for a specific user"""
    db = get_db()
    tournaments = db.tournaments
    result = tournaments.delete_many({"username": username})
    return result.deleted_count

def delete_single_tournament_result(tournament_id, username):
    """Delete a single tournament result by ID and username (for security)"""
    db = get_db()
    tournaments = db.tournaments
    result = tournaments.delete_one({"_id": ObjectId(tournament_id), "username": username})
    return result.deleted_count

def update_tournament_result(tournament_id, username, tournament_data):
    """Update a single tournament result by ID and username (for security)"""
    db = get_db()
    tournaments = db.tournaments
    
    # Add timestamp for the update
    tournament_data["updated_at"] = datetime.utcnow()
    
    result = tournaments.update_one(
        {"_id": ObjectId(tournament_id), "username": username},
        {"$set": tournament_data}
    )
    return result.modified_count

def get_single_tournament_result(tournament_id, username):
    """Get a single tournament result by ID and username (for security)"""
    db = get_db()
    tournaments = db.tournaments
    return tournaments.find_one({"_id": ObjectId(tournament_id), "username": username}) 