from pymongo import MongoClient
import streamlit as st
from datetime import datetime

# Initialize MongoDB connection
@st.cache_resource
def init_connection():
    return MongoClient(st.secrets["MONGODB_URI"])

def get_database():
    client = init_connection()
    return client.poker_coach_db

# User operations
def save_user(email, name, password):
    db = get_database()
    users = db.users
    user_data = {
        "email": email,
        "name": name,
        "password": password,
        "created_at": datetime.utcnow()
    }
    return users.insert_one(user_data)

def get_user(email):
    db = get_database()
    return db.users.find_one({"email": email})

# Chat operations
def save_chat(user_email, mode, messages):
    db = get_database()
    chats = db.chats
    chat_data = {
        "user_email": user_email,
        "mode": mode,
        "messages": messages,
        "timestamp": datetime.utcnow()
    }
    return chats.insert_one(chat_data)

def get_user_chats(user_email):
    db = get_database()
    return list(db.chats.find({"user_email": user_email}).sort("timestamp", -1))

# Tournament results operations
def save_tournament_result(user_email, tournament_data):
    db = get_database()
    tournaments = db.tournaments
    tournament_data.update({
        "user_email": user_email,
        "timestamp": datetime.utcnow()
    })
    return tournaments.insert_one(tournament_data)

def get_user_tournament_results(user_email):
    db = get_database()
    return list(db.tournaments.find({"user_email": user_email}).sort("timestamp", -1))

def get_user_stats(user_email):
    db = get_database()
    tournaments = db.tournaments
    pipeline = [
        {"$match": {"user_email": user_email}},
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