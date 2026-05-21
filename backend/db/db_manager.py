import os
import sqlite3
import hashlib
import json
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from backend.utils.logger import app_logger

DATABASE_PATH = os.path.join("data", "craving_ai.db")

_otp_rate_limits = {}

class DBManager:
    def __init__(self):
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        self.conn = self._get_connection()
        self._create_tables()

    def _get_connection(self):
        # Using check_same_thread=False since FastAPI handles concurrency
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_tables(self):
        cursor = self.conn.cursor()
        
        # 1. Users Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_or_email TEXT UNIQUE NOT NULL,
                verified BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 1.5 User Profiles
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                avatar_id TEXT,
                preferences TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
        
        # 1.7 OTP Codes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS otp_codes (
                phone_or_email TEXT PRIMARY KEY,
                code TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL
            )
        """)
        
        # 2. Sessions Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
        
        # 3. Favorites Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                user_id INTEGER NOT NULL,
                dish_id TEXT NOT NULL,
                name TEXT NOT NULL,
                cuisine TEXT NOT NULL,
                price REAL NOT NULL,
                rating REAL NOT NULL,
                restaurant_name TEXT NOT NULL,
                image_url TEXT,
                PRIMARY KEY (user_id, dish_id),
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
        
        # 4. Saved Recipes Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS saved_recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                dish_id TEXT NOT NULL,
                title TEXT NOT NULL,
                prep_time TEXT,
                cook_time TEXT,
                ingredients TEXT, -- JSON string representing ingredients list
                instructions TEXT, -- JSON string representing step-by-step instructions
                chef_tips TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
        
        # 5. Craving Logs Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS craving_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                query TEXT NOT NULL,
                craving_type TEXT,
                mood TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
        
        # 6. Cart Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cart (
                user_id INTEGER NOT NULL,
                dish_id TEXT NOT NULL,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                quantity INTEGER DEFAULT 1,
                image_url TEXT,
                restaurant_name TEXT,
                PRIMARY KEY (user_id, dish_id),
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
        
        # 7. Orders Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                status TEXT DEFAULT 'preparing',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
        
        # 8. Order Items Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                order_id INTEGER NOT NULL,
                dish_id TEXT NOT NULL,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE
            )
        """)
        
        self.conn.commit()
        app_logger.info("SQLite database tables initialized successfully.")

    # ── AUTHENTICATION & OTP METHODS ──────────────────────────────────────────
    def create_otp(self, phone_or_email: str) -> str:
        global _otp_rate_limits
        now = datetime.now()
        
        # Check rate limit (max 3 requests per minute per user)
        if phone_or_email in _otp_rate_limits:
            _otp_rate_limits[phone_or_email] = [t for t in _otp_rate_limits[phone_or_email] if t > now - timedelta(minutes=1)]
        else:
            _otp_rate_limits[phone_or_email] = []
            
        if len(_otp_rate_limits[phone_or_email]) >= 3:
            raise ValueError("Rate limit exceeded. Maximum 3 requests per minute.")
            
        _otp_rate_limits[phone_or_email].append(now)
        
        cursor = self.conn.cursor()
        code = ''.join(secrets.choice(string.digits) for _ in range(6))
        expires_at = now + timedelta(minutes=10)
        
        cursor.execute("""
            INSERT OR REPLACE INTO otp_codes (phone_or_email, code, expires_at)
            VALUES (?, ?, ?)
        """, (phone_or_email, code, expires_at.isoformat()))
        self.conn.commit()
        return code

    def verify_otp(self, phone_or_email: str, code: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("SELECT code, expires_at FROM otp_codes WHERE phone_or_email = ?", (phone_or_email,))
        row = cursor.fetchone()
        if not row:
            return False
            
        expires_at = datetime.fromisoformat(row['expires_at'])
        if datetime.now() > expires_at:
            cursor.execute("DELETE FROM otp_codes WHERE phone_or_email = ?", (phone_or_email,))
            self.conn.commit()
            return False
            
        if row['code'] == code:
            cursor.execute("DELETE FROM otp_codes WHERE phone_or_email = ?", (phone_or_email,))
            self.conn.commit()
            return True
        return False

    def get_or_create_user(self, phone_or_email: str) -> dict:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, verified FROM users WHERE phone_or_email = ?", (phone_or_email,))
        row = cursor.fetchone()
        
        if row:
            return {"id": row['id'], "is_new": False, "verified": bool(row['verified'])}
            
        cursor.execute("INSERT INTO users (phone_or_email, verified) VALUES (?, ?)", (phone_or_email, False))
        user_id = cursor.lastrowid
        self.conn.commit()
        return {"id": user_id, "is_new": True, "verified": False}
        
    def create_user_profile(self, user_id: int, name: str, avatar_id: str, preferences: list):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO user_profiles (user_id, name, avatar_id, preferences)
            VALUES (?, ?, ?, ?)
        """, (user_id, name, avatar_id, json.dumps(preferences)))
        cursor.execute("UPDATE users SET verified = 1 WHERE id = ?", (user_id,))
        self.conn.commit()

    def get_user_profile(self, user_id: int) -> Optional[dict]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT u.id, u.phone_or_email, u.verified, p.name, p.avatar_id, p.preferences
            FROM users u
            LEFT JOIN user_profiles p ON u.id = p.user_id
            WHERE u.id = ?
        """, (user_id,))
        row = cursor.fetchone()
        if row:
            d = dict(row)
            d['verified'] = bool(d['verified'])
            if d.get('preferences'):
                d['preferences'] = json.loads(d['preferences'])
            else:
                d['preferences'] = []
            return d
        return None

    def create_session(self, user_id: int) -> str:
        token = secrets.token_hex(32)
        expires_at = datetime.now() + timedelta(days=7)
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
            (token, user_id, expires_at.isoformat())
        )
        self.conn.commit()
        return token

    def verify_session(self, token: str) -> Optional[int]:
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM sessions WHERE token = ?", (token,))
            row = cursor.fetchone()
            if not row:
                return None
                
            expires_at = datetime.fromisoformat(row['expires_at'])
            if expires_at < datetime.now():
                # Session expired, delete it
                cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
                self.conn.commit()
                return None
                
            return row['user_id']
        except Exception as e:
            app_logger.error(f"Error verifying session: {e}")
            return None

    def delete_session(self, token: str):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
        self.conn.commit()

    # ── FAVORITES METHODS ─────────────────────────────────────────────────────
    def get_favorites(self, user_id: int) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM favorites WHERE user_id = ?", (user_id,))
        return [dict(r) for r in cursor.fetchall()]

    def add_favorite(self, user_id: int, dish: Dict[str, Any]) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO favorites (user_id, dish_id, name, cuisine, price, rating, restaurant_name, image_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    dish["id"],
                    dish["name"],
                    dish["cuisine"],
                    dish["price"],
                    dish["rating"],
                    dish["restaurant_name"],
                    dish.get("image_url")
                )
            )
            self.conn.commit()
            return True
        except Exception as e:
            app_logger.error(f"Error adding favorite: {e}")
            return False

    def remove_favorite(self, user_id: int, dish_id: str) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM favorites WHERE user_id = ? AND dish_id = ?", (user_id, dish_id))
            self.conn.commit()
            return True
        except Exception as e:
            app_logger.error(f"Error removing favorite: {e}")
            return False

    # ── SAVED RECIPES METHODS ─────────────────────────────────────────────────
    def get_saved_recipes(self, user_id: int) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM saved_recipes WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        result = []
        for r in cursor.fetchall():
            item = dict(r)
            item["ingredients"] = json.loads(item["ingredients"]) if item["ingredients"] else []
            item["instructions"] = json.loads(item["instructions"]) if item["instructions"] else []
            result.append(item)
        return result

    def save_recipe(self, user_id: int, dish_id: str, title: str, prep_time: str, cook_time: str, ingredients: List[str], instructions: List[str], chef_tips: str) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO saved_recipes (user_id, dish_id, title, prep_time, cook_time, ingredients, instructions, chef_tips)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    dish_id,
                    title,
                    prep_time,
                    cook_time,
                    json.dumps(ingredients),
                    json.dumps(instructions),
                    chef_tips
                )
            )
            self.conn.commit()
            return True
        except Exception as e:
            app_logger.error(f"Error saving recipe: {e}")
            return False

    def remove_recipe(self, user_id: int, recipe_id: int) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM saved_recipes WHERE user_id = ? AND id = ?", (user_id, recipe_id))
            self.conn.commit()
            return True
        except Exception as e:
            app_logger.error(f"Error removing recipe: {e}")
            return False

    # ── CRAVING LOGS METHODS ──────────────────────────────────────────────────
    def get_craving_logs(self, user_id: int, limit: int = 15) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM craving_logs WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit)
        )
        return [dict(r) for r in cursor.fetchall()]

    def add_craving_log(self, user_id: int, query: str, craving_type: Optional[str] = None, mood: Optional[str] = None):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO craving_logs (user_id, query, craving_type, mood) VALUES (?, ?, ?, ?)",
                (user_id, query, craving_type, mood)
            )
            self.conn.commit()
        except Exception as e:
            app_logger.error(f"Error adding craving log: {e}")

    # ── CART & ORDERS METHODS ─────────────────────────────────────────────────
    def add_to_cart(self, user_id: int, dish_id: str, name: str, price: float, image_url: str, restaurant_name: str) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT quantity FROM cart WHERE user_id = ? AND dish_id = ?", (user_id, dish_id))
            row = cursor.fetchone()
            if row:
                cursor.execute("UPDATE cart SET quantity = quantity + 1 WHERE user_id = ? AND dish_id = ?", (user_id, dish_id))
            else:
                cursor.execute("""
                    INSERT INTO cart (user_id, dish_id, name, price, quantity, image_url, restaurant_name)
                    VALUES (?, ?, ?, ?, 1, ?, ?)
                """, (user_id, dish_id, name, price, image_url, restaurant_name))
            self.conn.commit()
            return True
        except Exception as e:
            app_logger.error(f"Error adding to cart: {e}")
            return False

    def remove_from_cart(self, user_id: int, dish_id: str) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT quantity FROM cart WHERE user_id = ? AND dish_id = ?", (user_id, dish_id))
            row = cursor.fetchone()
            if row:
                if row['quantity'] > 1:
                    cursor.execute("UPDATE cart SET quantity = quantity - 1 WHERE user_id = ? AND dish_id = ?", (user_id, dish_id))
                else:
                    cursor.execute("DELETE FROM cart WHERE user_id = ? AND dish_id = ?", (user_id, dish_id))
                self.conn.commit()
            return True
        except Exception as e:
            app_logger.error(f"Error removing from cart: {e}")
            return False

    def get_cart(self, user_id: int) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM cart WHERE user_id = ?", (user_id,))
        return [dict(r) for r in cursor.fetchall()]

    def clear_cart(self, user_id: int) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
            self.conn.commit()
            return True
        except Exception as e:
            app_logger.error(f"Error clearing cart: {e}")
            return False
            
    def checkout(self, user_id: int) -> Optional[int]:
        try:
            cursor = self.conn.cursor()
            cart_items = self.get_cart(user_id)
            if not cart_items:
                return None
                
            total_amount = sum(item['price'] * item['quantity'] for item in cart_items)
            
            cursor.execute("INSERT INTO orders (user_id, total_amount) VALUES (?, ?)", (user_id, total_amount))
            order_id = cursor.lastrowid
            
            for item in cart_items:
                cursor.execute("""
                    INSERT INTO order_items (order_id, dish_id, name, price, quantity)
                    VALUES (?, ?, ?, ?, ?)
                """, (order_id, item['dish_id'], item['name'], item['price'], item['quantity']))
                
            cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
            self.conn.commit()
            return order_id
        except Exception as e:
            app_logger.error(f"Error during checkout: {e}")
            return None


# Singleton instance
db_manager = DBManager()
