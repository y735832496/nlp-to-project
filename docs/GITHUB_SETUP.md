# GitHub配置指南

## 问题说明

你遇到的错误是因为GitHub推送失败，主要原因是：

1. **网络连接问题**: 无法连接到GitHub服务器
2. **GitHub Token未配置**: 没有设置GitHub访问令牌

## 重试机制

系统现在内置了智能重试机制：

- **重试次数**: 默认3次
- **等待策略**: 递增等待时间 (5s, 10s, 15s)
- **超时处理**: 每次推送60秒超时
- **智能重试**: 区分网络错误和权限错误

## 解决方案

### 方案1: 配置GitHub Token（推荐）

1. **创建GitHub Token**:
   - 访问 https://github.com/settings/tokens
   - 点击 "Generate new token" -> "Generate new token (classic)"
   - 选择权限: `repo` (完整仓库访问权限)
   - 复制生成的token

2. **设置环境变量**:
   ```bash
   # 临时设置（当前会话有效）
   export GITHUB_TOKEN="your_github_token_here"
   export GITHUB_USERNAME="your_github_username"  # 可选，系统会自动获取
   
   # 永久设置（添加到 ~/.bashrc 或 ~/.zshrc）
   echo 'export GITHUB_TOKEN="your_github_token_here"' >> ~/.bashrc
   echo 'export GITHUB_USERNAME="your_github_username"' >> ~/.bashrc
   source ~/.bashrc
   ```

3. **验证配置**:
   ```bash
   echo $GITHUB_TOKEN
   ```

### 方案2: 跳过GitHub推送

如果不需要自动推送到GitHub，系统会：
- ✅ 正常生成项目到本地
- ✅ 提供项目使用说明
- ✅ 显示手动推送命令

### 方案3: 手动推送

如果自动推送失败，可以手动推送：

```bash
# 进入项目目录
cd /path/to/your/project

# 初始化git（如果还没有）
git init

# 添加远程仓库
git remote add origin https://github.com/username/repository-name.git

# 添加文件并提交
git add .
git commit -m "Initial commit"

# 推送到GitHub
git push -u origin main
```

## 网络问题解决

如果遇到网络连接问题：

1. **运行网络诊断工具**:
   ```bash
   python network_diagnosis.py
   ```

2. **检查网络连接**:
   ```bash
   ping github.com
   ```

3. **Git网络优化配置**:
   ```bash
   # 增加缓冲区大小
   git config --global http.postBuffer 524288000
   
   # 禁用低速限制
   git config --global http.lowSpeedLimit 0
   git config --global http.lowSpeedTime 999999
   
   # 增加超时时间
   git config --global http.timeout 300
   ```

4. **使用代理**（如果需要）:
   ```bash
   git config --global http.proxy http://proxy-server:port
   git config --global https.proxy https://proxy-server:port
   ```

5. **使用SSH替代HTTPS**:
   ```bash
   git remote set-url origin git@github.com:username/repository.git
   ```

6. **网络环境优化**:
   - 使用稳定的网络连接
   - 避免网络高峰期推送
   - 考虑使用VPN服务
   - 检查防火墙设置

## 权限问题解决

如果遇到权限问题：

1. **检查Token权限**: 确保token有 `repo` 权限
2. **检查仓库权限**: 确保有推送权限
3. **使用SSH密钥**: 配置SSH密钥认证

## 测试配置

运行以下命令测试GitHub配置：

```bash
python -c "
import os
from github import Github
token = os.getenv('GITHUB_TOKEN')
if token:
    try:
        g = Github(token)
        user = g.get_user()
        print(f'✅ GitHub连接成功: {user.login}')
    except Exception as e:
        print(f'❌ GitHub连接失败: {e}')
else:
    print('⚠️ 未设置GITHUB_TOKEN')
"
```

## 常见问题

### Q: Token权限不足
**A**: 确保token有 `repo` 权限，可以访问和创建仓库

### Q: 网络超时
**A**: 检查网络连接，或使用代理

### Q: 仓库已存在
**A**: 系统会自动添加时间戳避免重名

### Q: 推送被拒绝
**A**: 检查仓库权限和Token有效性

## 总结

- ✅ **推荐**: 配置GitHub Token实现自动推送
- ✅ **备选**: 手动推送或跳过GitHub功能
- ✅ **项目生成**: 无论GitHub推送是否成功，项目都会正常生成到本地
