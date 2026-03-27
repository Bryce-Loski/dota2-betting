import os

USERS_FILE = os.path.join(os.path.dirname(__file__), '..', 'static', 'users.txt')

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
                        username = parts[0]
                        password = parts[1]
                        users[username] = password
    return users

def save_users(users):
    """保存用户列表到txt文件"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        for username, password in users.items():
            f.write(f"{username},{password}\n")

def verify_user(username, password):
    """验证用户登录"""
    users = load_users()
    if username in users:
        return users[username] == password
    return False

def change_password(username, old_password, new_password):
    """修改用户密码"""
    users = load_users()
    if username in users and users[username] == old_password:
        users[username] = new_password
        save_users(users)
        return True
    return False

def get_all_usernames():
    """获取所有用户名列表"""
    users = load_users()
    return list(users.keys())

def user_exists(username):
    """检查用户是否存在"""
    users = load_users()
    return username in users
