from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys

sys.path.append(os.path.dirname(__file__))

from database import get_db_connection, init_db, init_user_balances
from user_manager import verify_user, change_password, get_all_usernames, user_exists

# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder=os.path.join(current_dir, 'frontend'))
CORS(app, supports_credentials=True)
app.secret_key = 'dota2_betting_secret_key'

# 初始化数据库（函数计算环境下使用 /tmp 目录）
import database
database.DB_PATH = '/tmp/dota2_betting.db'
init_db()
init_user_balances(get_all_usernames())

# ==================== 用户认证API ====================

@app.route('/api/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400
    
    if verify_user(username, password):
        return jsonify({'success': True, 'username': username})
    else:
        return jsonify({'success': False, 'message': '用户名或密码错误'}), 401

@app.route('/api/change_password', methods=['POST'])
def change_pwd():
    """修改密码"""
    data = request.json
    username = data.get('username')
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not all([username, old_password, new_password]):
        return jsonify({'success': False, 'message': '请填写所有字段'}), 400
    
    if change_password(username, old_password, new_password):
        return jsonify({'success': True, 'message': '密码修改成功'})
    else:
        return jsonify({'success': False, 'message': '原密码错误'}), 400

@app.route('/api/balance/<username>', methods=['GET'])
def get_balance(username):
    """获取用户余额"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM user_balances WHERE username = ?', (username,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return jsonify({'success': True, 'balance': result['balance']})
    return jsonify({'success': False, 'message': '用户不存在'}), 404

# ==================== 比赛管理API ====================

@app.route('/api/matches', methods=['GET'])
def get_matches():
    """获取所有比赛列表"""
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
    """创建比赛"""
    data = request.json
    creator = data.get('creator')
    team_a = data.get('team_a')
    team_b = data.get('team_b')
    match_type = data.get('match_type')
    creator_choice = data.get('creator_choice')
    odds = float(data.get('odds', 1.0))
    max_bet = float(data.get('max_bet', 100))
    
    if not all([creator, team_a, team_b, match_type, creator_choice]):
        return jsonify({'success': False, 'message': '请填写所有必填字段'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO matches (creator, team_a, team_b, match_type, creator_choice, odds, max_bet)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (creator, team_a, team_b, match_type, creator_choice, odds, max_bet))
    conn.commit()
    match_id = cursor.lastrowid
    conn.close()
    
    return jsonify({'success': True, 'message': '比赛创建成功', 'match_id': match_id})

@app.route('/api/matches/<int:match_id>/close', methods=['POST'])
def close_match(match_id):
    """封盘比赛"""
    data = request.json
    username = data.get('username')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查是否是创建者
    cursor.execute('SELECT creator, status FROM matches WHERE id = ?', (match_id,))
    match = cursor.fetchone()
    
    if not match:
        conn.close()
        return jsonify({'success': False, 'message': '比赛不存在'}), 404
    
    if match['creator'] != username:
        conn.close()
        return jsonify({'success': False, 'message': '只有创建者可以封盘'}), 403
    
    if match['status'] != 'open':
        conn.close()
        return jsonify({'success': False, 'message': '比赛已经封盘或已结算'}), 400
    
    cursor.execute('''
        UPDATE matches SET status = 'closed', closed_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (match_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '比赛已封盘'})

@app.route('/api/matches/<int:match_id>/settle', methods=['POST'])
def settle_match(match_id):
    """结算比赛"""
    data = request.json
    username = data.get('username')
    winner = data.get('winner')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查是否是创建者
    cursor.execute('SELECT * FROM matches WHERE id = ?', (match_id,))
    match = cursor.fetchone()
    
    if not match:
        conn.close()
        return jsonify({'success': False, 'message': '比赛不存在'}), 404
    
    if match['creator'] != username:
        conn.close()
        return jsonify({'success': False, 'message': '只有创建者可以结算'}), 403
    
    if match['status'] == 'settled':
        conn.close()
        return jsonify({'success': False, 'message': '比赛已经结算'}), 400
    
    # 获取所有下注
    cursor.execute('SELECT * FROM bets WHERE match_id = ?', (match_id,))
    bets = cursor.fetchall()
    
    # 结算每个下注
    for bet in bets:
        bet_amount = bet['amount']
        bet_odds = bet['odds']
        bet_team = bet['team']
        bet_user = bet['username']
        
        if bet_team == winner:
            # 赢了
            profit = bet_amount * (bet_odds - 1)
            result = 'win'
            # 返还本金+盈利
            cursor.execute('''
                UPDATE user_balances 
                SET balance = balance + ? 
                WHERE username = ?
            ''', (bet_amount + profit, bet_user))
        else:
            # 输了
            profit = -bet_amount
            result = 'loss'
        
        cursor.execute('''
            UPDATE bets SET result = ?, profit = ? WHERE id = ?
        ''', (result, profit, bet['id']))
    
    # 更新比赛状态
    cursor.execute('''
        UPDATE matches SET status = 'settled', winner = ? WHERE id = ?
    ''', (winner, match_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '比赛已结算'})

# ==================== 下注API ====================

@app.route('/api/matches/<int:match_id>/bets', methods=['GET'])
def get_match_bets(match_id):
    """获取比赛的投注情况"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT b.*, m.creator, m.team_a, m.team_b, m.creator_choice
        FROM bets b
        JOIN matches m ON b.match_id = m.id
        WHERE b.match_id = ?
    ''', (match_id,))
    bets = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({'success': True, 'bets': bets})

@app.route('/api/bets', methods=['POST'])
def place_bet():
    """下注"""
    data = request.json
    match_id = data.get('match_id')
    username = data.get('username')
    team = data.get('team')
    amount = float(data.get('amount', 0))
    
    if not all([match_id, username, team]) or amount <= 0:
        return jsonify({'success': False, 'message': '请填写所有必填字段'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查比赛状态
    cursor.execute('SELECT * FROM matches WHERE id = ?', (match_id,))
    match = cursor.fetchone()
    
    if not match:
        conn.close()
        return jsonify({'success': False, 'message': '比赛不存在'}), 404
    
    if match['status'] != 'open':
        conn.close()
        return jsonify({'success': False, 'message': '比赛已封盘，无法下注'}), 400
    
    # 检查用户余额
    cursor.execute('SELECT balance FROM user_balances WHERE username = ?', (username,))
    user = cursor.fetchone()
    
    if not user or user['balance'] < amount:
        conn.close()
        return jsonify({'success': False, 'message': '余额不足'}), 400
    
    # 检查是否超过最大下注额
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) as total_bet 
        FROM bets 
        WHERE match_id = ? AND username = ?
    ''', (match_id, username))
    total_bet = cursor.fetchone()['total_bet']
    
    if total_bet + amount > match['max_bet']:
        conn.close()
        return jsonify({'success': False, 'message': f'超过最大下注限额 {match["max_bet"]}'}), 400
    
    # 扣除余额
    cursor.execute('''
        UPDATE user_balances SET balance = balance - ? WHERE username = ?
    ''', (amount, username))
    
    # 记录下注
    cursor.execute('''
        INSERT INTO bets (match_id, username, team, amount, odds)
        VALUES (?, ?, ?, ?, ?)
    ''', (match_id, username, team, amount, match['odds']))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '下注成功'})

@app.route('/api/users/<username>/bets', methods=['GET'])
def get_user_bets(username):
    """获取用户的所有下注"""
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

# ==================== 静态文件服务 ====================

@app.route('/')
def index():
    return send_from_directory(os.path.join(current_dir, 'frontend'), 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(os.path.join(current_dir, 'frontend'), path)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
