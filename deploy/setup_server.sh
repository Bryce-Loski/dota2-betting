#!/bin/bash
# 服务器部署脚本

echo "========== 开始部署 Dota2 预测网站 =========="

# 更新系统
echo "[1/6] 更新系统..."
apt-get update -y

# 安装 Python 和 pip
echo "[2/6] 安装 Python..."
apt-get install -y python3 python3-pip

# 创建应用目录
echo "[3/6] 创建应用目录..."
mkdir -p /opt/dota2

# 进入目录
cd /opt/dota2

# 创建虚拟环境（可选但推荐）
echo "[4/6] 创建虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 安装依赖
echo "[5/6] 安装依赖..."
pip install flask flask-cors gunicorn

# 创建启动脚本
echo "[6/6] 创建启动脚本..."
cat > start.sh << 'EOF'
#!/bin/bash
cd /opt/dota2
source venv/bin/activate
export FLASK_APP=app.py
export FLASK_ENV=production
# 使用 gunicorn 启动，绑定 0.0.0.0:80
gunicorn -w 4 -b 0.0.0.0:80 app:app
EOF

chmod +x start.sh

echo ""
echo "========== 部署准备完成 =========="
echo ""
echo "请上传代码文件到 /opt/dota2 目录："
echo "  - app.py"
echo "  - database.py"
echo "  - user_manager.py"
echo "  - frontend/ 目录"
echo "  - static/ 目录"
echo ""
echo "上传完成后，运行: ./start.sh"
echo ""
echo "访问地址: http://118.178.123.39"
