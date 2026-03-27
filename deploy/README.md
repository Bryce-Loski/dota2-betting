# 阿里云函数计算 FC 部署指南

## 前置要求

1. 安装阿里云 Serverless Devs 工具
```bash
npm install @serverless-devs/s -g
```

2. 配置阿里云凭证
```bash
s config add
```
按提示输入你的阿里云 AccessKey ID 和 AccessKey Secret

## 部署步骤

### 1. 进入部署目录
```bash
cd deploy
```

### 2. 部署到函数计算
```bash
s deploy
```

### 3. 获取访问地址
部署完成后，控制台会输出 HTTP 触发器的访问地址，例如：
```
https://dota2-betting-xxx.cn-hangzhou.fcapp.run
```

## 费用说明

阿里云函数计算 FC 按调用次数计费：
- **免费额度**：每月 100 万次调用 + 40万 GB-秒资源使用量
- **超出后**：约 0.013元/万次调用
- 对于个人使用的预测网站，通常完全在免费额度内

## 自定义域名（可选）

如果你想使用自己的域名：
1. 在函数计算控制台找到你的函数
2. 进入「触发器管理」
3. 点击「自定义域名」
4. 添加你的域名并配置 CNAME

## 注意事项

1. 数据库使用 /tmp 目录，函数重启后数据会丢失（如需持久化，建议使用阿里云 RDS 或 Tablestore）
2. 静态文件已打包到部署包中
3. 如需修改代码，修改后重新运行 `s deploy` 即可
