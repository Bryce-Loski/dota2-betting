# Dota2 比赛预测网站

一个类似 Polymarket 的 Dota2 比赛预测平台，支持创建比赛、下注、封盘和结算功能。

## 功能特性

- **用户系统**: 基于白名单的登录系统，支持修改密码
- **市场页面**: 查看所有进行中的比赛，支持创建新比赛
- **创建比赛**: 庄家可以创建比赛，设置赔率、最大下注金额
- **下注功能**: 玩家可以对比赛进行下注
- **封盘功能**: 庄家可以随时封盘，阻止新的下注
- **结算功能**: 比赛结束后，庄家手动结算，自动计算盈亏
- **我的预测**: 查看自己参与的所有预测记录

## 技术栈

- **前端**: HTML + CSS + JavaScript (原生)
- **后端**: Python Flask
- **数据库**: SQLite
- **用户数据**: 本地 txt 文件存储

## 安装和运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动后端服务

```bash
cd backend
python app.py
```

后端服务将在 http://localhost:5001 运行

### 3. 访问网站

打开浏览器访问 http://localhost:5001

## 默认用户

系统预置了白名单用户，初始密码均为 `123456`：

卷宝, meibe, 恩师松鼠, 秋韵, zzm, 程义, 凌一, 白桃乌龙, 张学友, 小妈, 靳雨滕, 洛羽, 鸟哥, 冰空花束, 牟帅, hy, 道勰, 喵八嘎, 包容物种多样性, Hikari, 苏离, 话梅, 美拉, 花男, 斌子, 枫修, merci, 金, 坏咪家属, 柯六, 思颀, 某改, 真视, 米, 阿瑟, 芷浩, 业原, ldd, 驿北, 余曦, 家轩, 脸堡, 百辟, Rain, 厦开, ted, 白泥, 白翎, 鼎云, YUN, 小桃, 孝坤, 别问, 霄驰, 目日, jager, 鸣潮, 燧寒, gg老师, 着陆, 泓弋, Less, 森, wand, drrry, 逸吾, 思努, TinyKanja, 方澜, 明辰, 暗尘, 幻语, 惜川, 凡轩, 和仪, 寥江, 松鼠

## 使用说明

1. **登录**: 使用白名单中的用户名和初始密码 `123456` 登录
2. **创建比赛**: 点击"创建比赛"按钮，填写队伍信息、选择预测类型、设置赔率和最大下注金额
3. **下注**: 在市场页面选择比赛，点击"下注"按钮进行下注
4. **封盘**: 作为创建者，可以随时封盘，阻止新的下注
5. **结算**: 比赛结束后，创建者可以结算比赛，选择获胜队伍，系统自动计算盈亏
6. **查看预测**: 在"我的预测"页面查看所有参与的预测记录

## 项目结构

```
dota2/
├── backend/
│   ├── app.py          # Flask 后端主程序
│   ├── database.py     # 数据库操作
│   └── user_manager.py # 用户管理
├── frontend/
│   ├── index.html      # 主页面
│   ├── style.css       # 样式文件
│   └── app.js          # 前端逻辑
├── static/
│   └── users.txt       # 用户数据文件
├── requirements.txt    # Python 依赖
└── README.md          # 项目说明
```

## 部署到 GitHub

1. 创建 GitHub 仓库
2. 推送代码到仓库
3. 可以使用 GitHub Pages 部署前端，或使用其他平台部署完整的 Flask 应用

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yourusername/dota2-betting.git
git push -u origin main
```
