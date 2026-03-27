// 全局变量
// 自动检测环境：生产环境使用当前域名，开发环境使用 localhost
const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:5001/api'
    : `${window.location.origin}/api`;
let currentUser = null;
let currentMatchId = null;
let matches = [];
let currentFilter = 'all';

// 白名单用户列表
const WHITELIST_USERS = [
    '卷宝', 'meibe', '恩师松鼠', '秋韵', 'zzm', '程义', '凌一', '白桃乌龙', '张学友', '小妈',
    '靳雨滕', '洛羽', '鸟哥', '冰空花束', '牟帅', 'hy', '道勰', '喵八嘎', '包容物种多样性',
    'Hikari', '苏离', '话梅', '美拉', '花男', '斌子', '枫修', 'merci', '金', '坏咪家属',
    '柯六', '思颀', '某改', '真视', '米', '阿瑟', '芷浩', '业原', 'ldd', '驿北', '余曦',
    '家轩', '脸堡', '百辟', 'Rain', '厦开', 'ted', '白泥', '白翎', '鼎云', 'YUN', '小桃',
    '孝坤', '别问', '霄驰', '目日', 'jager', '鸣潮', '燧寒', 'gg老师', '着陆', '泓弋',
    'Less', '森', 'wand', 'drrry', '逸吾', '思努', 'TinyKanja', '方澜', '明辰', '暗尘',
    '幻语', '惜川', '凡轩', '和仪', '寥江', '松鼠'
];

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    initUserList();
    initEventListeners();
    initFilterButtons();
    checkLogin();
});

// 初始化用户列表
function initUserList() {
    const datalist = document.getElementById('user-list');
    WHITELIST_USERS.forEach(user => {
        const option = document.createElement('option');
        option.value = user;
        datalist.appendChild(option);
    });
}

// 初始化事件监听
function initEventListeners() {
    // 监听队伍输入，更新创建者选择
    document.getElementById('match-team-a').addEventListener('input', updateCreatorChoice);
    document.getElementById('match-team-b').addEventListener('input', updateCreatorChoice);
    
    // 监听下注金额变化，计算预计收益
    document.getElementById('bet-amount').addEventListener('input', updateEstimatedProfit);
}

// 初始化筛选按钮
function initFilterButtons() {
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            e.currentTarget.classList.add('active');
            currentFilter = e.currentTarget.dataset.filter;
            renderMatches();
        });
    });
}

// 更新创建者队伍选择
function updateCreatorChoice() {
    const teamA = document.getElementById('match-team-a').value;
    const teamB = document.getElementById('match-team-b').value;
    const select = document.getElementById('creator-choice');
    
    select.innerHTML = '';
    
    if (teamA) {
        const optionA = document.createElement('option');
        optionA.value = teamA;
        optionA.textContent = teamA;
        select.appendChild(optionA);
    }
    
    if (teamB) {
        const optionB = document.createElement('option');
        optionB.value = teamB;
        optionB.textContent = teamB;
        select.appendChild(optionB);
    }
    
    if (!teamA && !teamB) {
        const option = document.createElement('option');
        option.value = '';
        option.textContent = '请先输入队伍名称';
        select.appendChild(option);
    }
}

// 更新预计收益
function updateEstimatedProfit() {
    const amount = parseFloat(document.getElementById('bet-amount').value) || 0;
    const match = matches.find(m => m.id === currentMatchId);
    if (match && amount > 0) {
        const profit = amount * (match.odds - 1);
        document.getElementById('estimated-profit').textContent = `¥${profit.toFixed(2)}`;
    } else {
        document.getElementById('estimated-profit').textContent = '¥0';
    }
}

// 检查登录状态
function checkLogin() {
    const savedUser = localStorage.getItem('currentUser');
    if (savedUser) {
        currentUser = savedUser;
        showMainPage();
    }
}

// 登录
async function login() {
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;
    
    if (!username || !password) {
        alert('请输入用户名和密码');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentUser = username;
            localStorage.setItem('currentUser', username);
            showMainPage();
        } else {
            alert(data.message || '登录失败');
        }
    } catch (error) {
        alert('登录失败，请检查网络连接');
    }
}

// 退出登录
function logout() {
    currentUser = null;
    localStorage.removeItem('currentUser');
    document.getElementById('login-page').classList.remove('hidden');
    document.getElementById('main-page').classList.add('hidden');
    document.getElementById('login-username').value = '';
    document.getElementById('login-password').value = '';
}

// 显示主页面
async function showMainPage() {
    document.getElementById('login-page').classList.add('hidden');
    document.getElementById('main-page').classList.remove('hidden');
    document.getElementById('user-name').textContent = currentUser;
    
    await updateBalance();
    await loadMatches();
}

// 更新余额
async function updateBalance() {
    try {
        const response = await fetch(`${API_BASE}/balance/${currentUser}`);
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('user-balance').innerHTML = 
                `<i class="fas fa-coins"></i> ¥${data.balance.toFixed(2)}`;
        }
    } catch (error) {
        console.error('获取余额失败:', error);
    }
}

// 切换标签页
function switchTab(tab) {
    // 更新按钮状态
    document.querySelectorAll('.nav-tab').forEach(btn => btn.classList.remove('active'));
    event.currentTarget.classList.add('active');
    
    // 显示对应内容
    document.querySelectorAll('.tab-content').forEach(content => content.classList.add('hidden'));
    document.getElementById(`${tab}-tab`).classList.remove('hidden');
    
    if (tab === 'market') {
        loadMatches();
    } else if (tab === 'my-bets') {
        loadMyBets();
    }
}

// 加载比赛列表
async function loadMatches() {
    try {
        const response = await fetch(`${API_BASE}/matches`);
        const data = await response.json();
        
        if (data.success) {
            matches = data.matches;
            renderMatches();
        }
    } catch (error) {
        console.error('加载比赛失败:', error);
    }
}

// 渲染比赛列表
function renderMatches() {
    const container = document.getElementById('matches-list');
    
    // 根据筛选条件过滤
    let filteredMatches = matches;
    if (currentFilter !== 'all') {
        filteredMatches = matches.filter(m => m.status === currentFilter);
    }
    
    if (filteredMatches.length === 0) {
        container.innerHTML = `
            <div class="empty">
                <i class="fas fa-inbox"></i>
                <p>暂无比赛</p>
            </div>
        `;
        return;
    }
    
    const typeLabels = {
        'winner': '比赛胜负',
        'first_blood': '一血',
        'ten_kills': '10杀'
    };
    
    const typeIcons = {
        'winner': 'fa-trophy',
        'first_blood': 'fa-skull',
        'ten_kills': 'fa-fire'
    };
    
    const statusLabels = {
        'open': '进行中',
        'closed': '已封盘',
        'settled': '已结算'
    };
    
    container.innerHTML = filteredMatches.map(match => {
        const isCreator = match.creator === currentUser;
        const canBet = match.status === 'open' && !isCreator;
        const canClose = match.status === 'open' && isCreator;
        const canSettle = match.status === 'closed' && isCreator;
        
        const totalBet = (match.team_a_total || 0) + (match.team_b_total || 0);
        const progressPercent = Math.min((totalBet / match.max_bet) * 100, 100);
        
        return `
            <div class="match-card">
                <div class="match-header">
                    <div class="match-type-badge ${match.match_type}">
                        <i class="fas ${typeIcons[match.match_type]}"></i>
                        ${typeLabels[match.match_type]}
                    </div>
                    <div class="match-creator">
                        <i class="fas fa-user"></i> 庄家: <span>${match.creator}</span>
                    </div>
                    <span class="match-status ${match.status}">${statusLabels[match.status]}</span>
                </div>
                <div class="match-teams">
                    <div class="team">
                        <div class="team-name">${match.team_a}</div>
                        <div class="team-bet-amount">
                            <i class="fas fa-coins"></i> ¥${(match.team_a_total || 0).toFixed(2)}
                        </div>
                    </div>
                    <div class="vs">VS</div>
                    <div class="team">
                        <div class="team-name">${match.team_b}</div>
                        <div class="team-bet-amount">
                            <i class="fas fa-coins"></i> ¥${(match.team_b_total || 0).toFixed(2)}
                        </div>
                    </div>
                </div>
                <div class="match-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${progressPercent}%"></div>
                    </div>
                    <div class="progress-info">
                        <span><i class="fas fa-chart-bar"></i> 已下注: ¥${totalBet.toFixed(2)}</span>
                        <span>上限: ¥${match.max_bet}</span>
                    </div>
                </div>
                <div class="match-info">
                    <div class="match-info-item">
                        <i class="fas fa-percentage"></i>
                        <span>赔率: ${match.odds}</span>
                    </div>
                    ${match.winner ? `
                    <div class="match-info-item">
                        <i class="fas fa-crown"></i>
                        <span>获胜: ${match.winner}</span>
                    </div>
                    ` : ''}
                </div>
                <div class="match-actions">
                    ${canBet ? `<button class="btn-bet" onclick="showBetModal(${match.id})"><i class="fas fa-coins"></i> 下注</button>` : ''}
                    ${canClose ? `<button class="btn-close" onclick="closeMatch(${match.id})"><i class="fas fa-lock"></i> 封盘</button>` : ''}
                    ${canSettle ? `<button class="btn-settle" onclick="showSettleModal(${match.id})"><i class="fas fa-trophy"></i> 结算</button>` : ''}
                    ${!canBet && !canClose && !canSettle ? `<button class="btn-disabled" disabled><i class="fas fa-ban"></i> 不可操作</button>` : ''}
                </div>
            </div>
        `;
    }).join('');
}

// 显示创建比赛弹窗
function showCreateMatch() {
    document.getElementById('create-match-modal').classList.remove('hidden');
}

// 创建比赛
async function createMatch() {
    const teamA = document.getElementById('match-team-a').value.trim();
    const teamB = document.getElementById('match-team-b').value.trim();
    const matchType = document.getElementById('match-type').value;
    const creatorChoice = document.getElementById('creator-choice').value;
    const odds = parseFloat(document.getElementById('match-odds').value);
    const maxBet = parseFloat(document.getElementById('max-bet').value);
    
    if (!teamA || !teamB || !creatorChoice || !odds || !maxBet) {
        alert('请填写所有字段');
        return;
    }
    
    if (teamA === teamB) {
        alert('两队名称不能相同');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/matches`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                creator: currentUser,
                team_a: teamA,
                team_b: teamB,
                match_type: matchType,
                creator_choice: creatorChoice,
                odds: odds,
                max_bet: maxBet
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('比赛创建成功');
            closeModal('create-match-modal');
            // 清空表单
            document.getElementById('match-team-a').value = '';
            document.getElementById('match-team-b').value = '';
            document.getElementById('match-odds').value = '';
            document.getElementById('max-bet').value = '';
            updateCreatorChoice();
            loadMatches();
        } else {
            alert(data.message || '创建失败');
        }
    } catch (error) {
        alert('创建失败，请检查网络连接');
    }
}

// 显示下注弹窗
function showBetModal(matchId) {
    currentMatchId = matchId;
    const match = matches.find(m => m.id === matchId);
    
    if (!match) return;
    
    // 玩家只能下注创建者没选的队伍
    const creatorChoice = match.creator_choice;
    const otherTeam = creatorChoice === match.team_a ? match.team_b : match.team_a;
    
    document.getElementById('bet-match-info').innerHTML = `
        <p><i class="fas fa-shield-alt"></i> ${match.team_a} VS ${match.team_b}</p>
        <p><i class="fas fa-tag"></i> 类型: ${match.match_type === 'winner' ? '比赛胜负' : match.match_type === 'first_blood' ? '一血' : '10杀'}</p>
        <p><i class="fas fa-percentage"></i> 赔率: ${match.odds}</p>
    `;
    
    const select = document.getElementById('bet-team');
    select.innerHTML = `<option value="${otherTeam}">${otherTeam}</option>`;
    
    document.getElementById('bet-amount').value = '';
    document.getElementById('estimated-profit').textContent = '¥0';
    
    document.getElementById('place-bet-modal').classList.remove('hidden');
}

// 下注
async function placeBet() {
    const team = document.getElementById('bet-team').value;
    const amount = parseFloat(document.getElementById('bet-amount').value);
    
    if (!team || !amount || amount <= 0) {
        alert('请填写正确的下注信息');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/bets`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                match_id: currentMatchId,
                username: currentUser,
                team: team,
                amount: amount
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('下注成功');
            closeModal('place-bet-modal');
            document.getElementById('bet-amount').value = '';
            await updateBalance();
            loadMatches();
        } else {
            alert(data.message || '下注失败');
        }
    } catch (error) {
        alert('下注失败，请检查网络连接');
    }
}

// 封盘
async function closeMatch(matchId) {
    if (!confirm('确定要封盘吗？封盘后其他玩家将无法下注。')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/matches/${matchId}/close`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: currentUser })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('比赛已封盘');
            loadMatches();
        } else {
            alert(data.message || '封盘失败');
        }
    } catch (error) {
        alert('封盘失败，请检查网络连接');
    }
}

// 显示结算弹窗
function showSettleModal(matchId) {
    currentMatchId = matchId;
    const match = matches.find(m => m.id === matchId);
    
    if (!match) return;
    
    const container = document.getElementById('settle-teams');
    container.innerHTML = `
        <button class="settle-team-btn" onclick="settleMatch('${match.team_a}')">
            <i class="fas fa-shield-alt"></i> ${match.team_a}
        </button>
        <button class="settle-team-btn" onclick="settleMatch('${match.team_b}')">
            <i class="fas fa-shield-alt"></i> ${match.team_b}
        </button>
    `;
    
    document.getElementById('settle-modal').classList.remove('hidden');
}

// 结算比赛
async function settleMatch(winner) {
    if (!confirm(`确定 ${winner} 获胜吗？结算后将无法更改。`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/matches/${currentMatchId}/settle`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: currentUser,
                winner: winner
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('比赛已结算');
            closeModal('settle-modal');
            await updateBalance();
            loadMatches();
        } else {
            alert(data.message || '结算失败');
        }
    } catch (error) {
        alert('结算失败，请检查网络连接');
    }
}

// 加载我的预测
async function loadMyBets() {
    try {
        const response = await fetch(`${API_BASE}/users/${currentUser}/bets`);
        const data = await response.json();
        
        if (data.success) {
            renderMyBets(data.bets);
        }
    } catch (error) {
        console.error('加载预测失败:', error);
    }
}

// 渲染我的预测
function renderMyBets(bets) {
    const container = document.getElementById('my-bets-list');
    
    if (bets.length === 0) {
        container.innerHTML = `
            <div class="empty">
                <i class="fas fa-ticket-alt"></i>
                <p>暂无预测记录</p>
            </div>
        `;
        return;
    }
    
    const typeLabels = {
        'winner': '比赛胜负',
        'first_blood': '一血',
        'ten_kills': '10杀'
    };
    
    const typeIcons = {
        'winner': 'fa-trophy',
        'first_blood': 'fa-skull',
        'ten_kills': 'fa-fire'
    };
    
    container.innerHTML = bets.map(bet => {
        let statusClass = 'pending';
        let statusText = '进行中';
        let statusIcon = 'fa-clock';
        
        if (bet.result === 'win') {
            statusClass = 'win';
            statusText = '赢';
            statusIcon = 'fa-check-circle';
        } else if (bet.result === 'loss') {
            statusClass = 'loss';
            statusText = '输';
            statusIcon = 'fa-times-circle';
        }
        
        const profitClass = bet.profit > 0 ? 'positive' : bet.profit < 0 ? 'negative' : '';
        
        return `
            <div class="bet-card">
                <div class="bet-header">
                    <span class="bet-teams">
                        <i class="fas fa-shield-alt"></i> ${bet.team_a} VS ${bet.team_b}
                    </span>
                    <span class="bet-status ${statusClass}">
                        <i class="fas ${statusIcon}"></i> ${statusText}
                    </span>
                </div>
                <div class="bet-type">
                    <i class="fas ${typeIcons[bet.match_type]}"></i> ${typeLabels[bet.match_type]}
                </div>
                <div class="bet-details">
                    <div class="bet-detail">
                        <div class="bet-detail-label">预测队伍</div>
                        <div class="bet-detail-value">${bet.team}</div>
                    </div>
                    <div class="bet-detail">
                        <div class="bet-detail-label">下注金额</div>
                        <div class="bet-detail-value">¥${bet.amount.toFixed(2)}</div>
                    </div>
                    <div class="bet-detail">
                        <div class="bet-detail-label">赔率</div>
                        <div class="bet-detail-value">${bet.odds}</div>
                    </div>
                    ${bet.result ? `
                    <div class="bet-detail">
                        <div class="bet-detail-label">盈亏</div>
                        <div class="bet-detail-value ${profitClass}">
                            ${bet.profit > 0 ? '+' : ''}¥${bet.profit.toFixed(2)}
                        </div>
                    </div>
                    ` : ''}
                </div>
                ${bet.winner ? `
                <div class="bet-winner">
                    <i class="fas fa-crown"></i> 获胜: ${bet.winner}
                </div>
                ` : ''}
            </div>
        `;
    }).join('');
}

// 显示修改密码弹窗
function showChangePassword() {
    document.getElementById('change-password-modal').classList.remove('hidden');
}

// 修改密码
async function changePassword() {
    const oldPassword = document.getElementById('old-password').value;
    const newPassword = document.getElementById('new-password').value;
    
    if (!oldPassword || !newPassword) {
        alert('请填写所有字段');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/change_password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: currentUser,
                old_password: oldPassword,
                new_password: newPassword
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('密码修改成功');
            closeModal('change-password-modal');
            document.getElementById('old-password').value = '';
            document.getElementById('new-password').value = '';
        } else {
            alert(data.message || '修改失败');
        }
    } catch (error) {
        alert('修改失败，请检查网络连接');
    }
}

// 关闭弹窗
function closeModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
}

// 点击弹窗外部关闭
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.classList.add('hidden');
    }
}
