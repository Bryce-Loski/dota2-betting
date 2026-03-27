from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys
import sqlite3

# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder=os.path.join(current_dir, 'frontend'))
CORS(app, supports_credentials=True)
app.secret_key = 'dota2_betting_secret_key'

# 数据库路径 - FC 环境中使用 /tmp 目录
DB_PATH = '/tmp/dota2_betting.db'
USERS_FILE = os.path.join(current_dir, 'static', 'users.txt')

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_balances (
            username TEXT PRIMARY KEY,
            balance REAL DEFAULT 0
        )
    ''')
    
    conn.commit()
    conn.close()

def load_users():
    """从txt文件加载用户列表"""
    users = {}
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and ',' in line:
                    parts = line.split(',')
                    if len(parts) >= 2:
                        users[parts[0]] = parts[1]
    return users

def get_all_usernames():
    """获取所有用户名列表"""
    return list(load_users().keys())

def init_user_balances(usernames):
    """初始化用户余额"""
    conn = get_db_connection()
    cursor = conn.cursor()
    for username in usernames:
        cursor.execute('INSERT OR IGNORE INTO user_balances (username, balance) VALUES (?, 0)', (username,))
    conn.commit()
    conn.close()

# 初始化
try:
    init_db()
    init_user_balances(get_all_usernames())
except Exception as e:
    print(f"Init error: {e}")

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400
    
    users = load_users()
    if username in users and users[username] == password:
        return jsonify({'success': True, 'username': username})
    return jsonify({'success': False, 'message': '用户名或密码错误'}), 401

@app.route('/api/balance/<username>')
def get_balance(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM user_balances WHERE username = ?', (username,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return jsonify({'success': True, 'balance': result['balance']})
    return jsonify({'success': False, 'message': '用户不存在'}), 404

@app.route('/api/matches')
def get_matches():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT m.*, 
               COALESCE(SUM(CASE WHEN b.team = m.team_a THEN b.amount ELSE 0 END), 0) as team_a_total,
               COALESCE(SUM(CASE WHEN b.team = m.team_b THEN b.amount ELSE 0 END), 0) as team_b_total
        FROM matches m
        LEFT JOIN bets b ON m.id = b.match_id
        GROUP BY m.id
        ORDER BY m.created_at DESC
    ''')
    matches = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({'success': True, 'matches': matches})

@app.route('/api/matches', methods=['POST'])
def create_match():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO matches (creator, team_a, team_b, match_type, creator_choice, odds, max_bet)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (data['creator'], data['team_a'], data['team_b'], data['match_type'], 
          data['creator_choice'], data['odds'], data['max_bet']))
    conn.commit()
    match_id = cursor.lastrowid
    conn.close()
    return jsonify({'success': True, 'message': '比赛创建成功', 'match_id': match_id})

@app.route('/api/matches/<int:match_id>/close', methods=['POST'])
def close_match(match_id):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT creator, status FROM matches WHERE id = ?', (match_id,))
    match = cursor.fetchone()
    
    if not match:
        conn.close()
        return jsonify({'success': False, 'message': '比赛不存在'}), 404
    
    if match['creator'] != data['username']:
        conn.close()
        return jsonify({'success': False, 'message': '只有创建者可以封盘'}), 403
    
    cursor.execute('UPDATE matches SET status = ?, closed_at = CURRENT_TIMESTAMP WHERE id = ?',
                   ('closed', match_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': '比赛已封盘'})

@app.route('/api/matches/<int:match_id>/settle', methods=['POST'])
def settle_match(match_id):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM matches WHERE id = ?', (match_id,))
    match = cursor.fetchone()
    
    if not match or match['creator'] != data['username']:
        conn.close()
        return jsonify({'success': False, 'message': '无权限'}), 403
    
    cursor.execute('SELECT * FROM bets WHERE match_id = ?', (match_id,))
    bets = cursor.fetchall()
    
    for bet in bets:
        if bet['team'] == data['winner']:
            profit = bet['amount'] * (bet['odds'] - 1)
            cursor.execute('UPDATE user_balances SET balance = balance + ? WHERE username = ?',
                          (bet['amount'] + profit, bet['username']))
            cursor.execute('UPDATE bets SET result = ?, profit = ? WHERE id = ?',
                          ('win', profit, bet['id']))
        else:
            cursor.execute('UPDATE bets SET result = ?, profit = ? WHERE id = ?',
                          ('loss', -bet['amount'], bet['id']))
    
    cursor.execute('UPDATE matches SET status = ?, winner = ? WHERE id = ?',
                   ('settled', data['winner'], match_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': '比赛已结算'})

@app.route('/api/bets', methods=['POST'])
def place_bet():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT status, odds, max_bet FROM matches WHERE id = ?', (data['match_id'],))
    match = cursor.fetchone()
    
    if not match or match['status'] != 'open':
        conn.close()
        return jsonify({'success': False, 'message': '比赛已封盘'}), 400
    
    cursor.execute('SELECT balance FROM user_balances WHERE username = ?', (data['username'],))
    user = cursor.fetchone()
    
    if not user or user['balance'] < data['amount']:
        conn.close()
        return jsonify({'success': False, 'message': '余额不足'}), 400
    
    cursor.execute('UPDATE user_balances SET balance = balance - ? WHERE username = ?',
                   (data['amount'], data['username']))
    cursor.execute('''
        INSERT INTO bets (match_id, username, team, amount, odds)
        VALUES (?, ?, ?, ?, ?)
    ''', (data['match_id'], data['username'], data['team'], data['amount'], match['odds']))
    
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': '下注成功'})

@app.route('/api/users/<username>/bets')
def get_user_bets(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT b.*, m.team_a, m.team_b, m.match_type, m.status as match_status, m.winner
        FROM bets b
        JOIN matches m ON b.match_id = m.id
        WHERE b.username = ?
        ORDER BY b.created_at DESC
    ''', (username,))
    bets = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({'success': True, 'bets': bets})

@app.route('/api/change_password', methods=['POST'])
def change_password():
    data = request.json
    users = load_users()
    
    if data['username'] in users and users[data['username']] == data['old_password']:
        users[data['username']] = data['new_password']
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            for u, p in users.items():
                f.write(f"{u},{p}\n")
        return jsonify({'success': True, 'message': '密码修改成功'})
    return jsonify({'success': False, 'message': '原密码错误'}), 400

@app.route('/')
def index():
    return send_from_directory(os.path.join(current_dir, 'frontend'), 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(os.path.join(current_dir, 'frontend'), path)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port)
