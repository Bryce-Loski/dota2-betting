import sqlite3
import os
from datetime import datetime

# 数据库路径 - FC 环境中使用 /tmp 目录
DB_PATH = os.environ.get('DB_PATH', os.path.join(os.path.dirname(__file__), 'dota2_betting.db'))

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 创建比赛表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creator TEXT NOT NULL,
            team_a TEXT NOT NULL,
            team_b TEXT NOT NULL,
            match_type TEXT NOT NULL,
            creator_choice TEXT NOT NULL,
            odds REAL NOT NULL,
            max_bet REAL NOT NULL,
            status TEXT DEFAULT 'open',
            winner TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            closed_at TIMESTAMP
        )
    ''')
    
    # 创建下注表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            team TEXT NOT NULL,
            amount REAL NOT NULL,
            odds REAL NOT NULL,
            result TEXT,
            profit REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (match_id) REFERENCES matches (id)
        )
    ''')
    
    # 创建用户余额表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_balances (
            username TEXT PRIMARY KEY,
            balance REAL DEFAULT 1000.0
        )
    ''')
    
    conn.commit()
    conn.close()
    print("数据库初始化完成")

def init_user_balances(usernames):
    """初始化用户余额"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for username in usernames:
        cursor.execute('''
            INSERT OR IGNORE INTO user_balances (username, balance)
            VALUES (?, 0)
        ''', (username,))
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
