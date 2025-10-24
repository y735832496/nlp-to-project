# nlp-to-project

🚀 🚀 🚀 🚀 🚀 项目启动

1. conda create -n your_env python=3.11
2. conda activate your_env
3. pip install -r requirements.txt
4. export GITHUB_TOKEN=YOUR_GITHUB_TOKEN
5. export ZHIPU_API_KEY=zhipu_ai_token
6. and then ...

python main.py



# AutoGen 动态项目生成系统

## 🚀 项目简介

AutoGen 动态项目生成系统是一个基于AI的智能项目生成工具，支持灵活的技术栈选择和AI自主决策。系统能够根据用户的自然语言描述，自动生成完整的项目结构、代码文件和配置文件。

### ✨ 核心特性

- **🤖 AI驱动**: 基于AutoGen框架的多Agent协作系统
- **🔧 灵活技术栈**: 支持Python、Java、Node.js、Go等多种技术栈
- **📁 智能结构**: 自动生成合理的项目目录结构
- **💬 多轮对话**: 支持复杂的多轮对话代码生成
- **🔍 质量检查**: 自动进行代码质量评估
- **🐙 GitHub集成**: 自动创建仓库并推送代码
- **📚 完整文档**: 自动生成项目文档和README

## 📁 项目结构

```
autogen_0.1.0/
├── main.py                          # 主入口文件
├── requirements.txt                 # 依赖文件
├── README.md                        # 项目说明
├── src/                            # 源代码目录
│   ├── __init__.py
│   ├── core/                       # 核心系统
│   │   ├── __init__.py
│   │   ├── enhanced_autogen_system.py
│   │   └── flexible_requirement_parser.py
│   ├── agents/                     # 代理模块
│   │   ├── __init__.py
│   │   ├── enhanced_agents.py
│   │   └── dynamic_agents.py
│   ├── generators/                 # 代码生成器
│   │   ├── __init__.py
│   │   ├── advanced_code_generator.py
│   │   └── project_templates.py
│   ├── managers/                   # 管理器模块
│   │   ├── __init__.py
│   │   ├── code_quality.py
│   │   ├── configuration_management.py
│   │   ├── user_interaction.py
│   │   └── extensibility.py
│   └── models/                     # 数据模型
│       ├── __init__.py
│       └── models.py
├── legacy/                         # 旧版本兼容
│   ├── __init__.py
│   └── requirement_parser.py
└── docs/                          # 文档
    ├── ENHANCED_SYSTEM_README.md
    ├── FLEXIBLE_SYSTEM_README.md
    ├── GITHUB_SETUP.md
    ├── NETWORK_OPTIMIZATION.md
    └── BUGFIX_REPORT.md
```

## 🛠️ 安装和使用

### 环境要求

- Python 3.8+
- Git
- GitHub账户（可选，用于自动推送）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 环境配置

设置GitHub相关环境变量（可选）：

```bash
export GITHUB_TOKEN="your_github_token"
export GITHUB_USERNAME="your_github_username"
```

### 运行系统

```bash
python main.py
```

## 🎯 使用示例

### 1. Python FastAPI项目

```
请输入您的项目需求: 创建一个基于FastAPI的电商系统，包含用户管理、商品管理和订单管理
```

### 2. Java Spring Boot项目

```
请输入您的项目需求: 用Java Spring Boot创建一个企业级用户管理系统
```

### 3. Node.js Express项目

```
请输入您的项目需求: 开发一个基于Express的博客系统，支持文章发布和评论功能
```

### 4. Go Gin项目

```
请输入您的项目需求: 用Go语言和Gin框架构建一个微服务API网关
```

## 🔧 系统架构

### 核心组件

1. **需求解析器** (`src/core/flexible_requirement_parser.py`)
   - 智能解析用户需求
   - 支持灵活的技术栈识别
   - 自动提取项目信息

2. **增强AutoGen系统** (`src/core/enhanced_autogen_system.py`)
   - 核心系统协调器
   - 管理整个项目生成流程
   - 集成所有功能模块

3. **多Agent系统** (`src/agents/`)
   - **项目规划专家**: 设计项目结构
   - **代码生成专家**: 生成具体代码
   - **架构专家**: 设计系统架构
   - **代码审查专家**: 质量检查
   - **性能优化专家**: 性能优化

4. **代码生成器** (`src/generators/`)
   - 高级代码生成器
   - 项目模板管理
   - 多轮对话生成

5. **管理器模块** (`src/managers/`)
   - 代码质量检查
   - 配置管理
   - 用户交互
   - 扩展性管理

## 🚀 工作流程

### 1. 需求解析
- 用户输入自然语言需求
- AI解析技术栈和项目类型
- 提取关键信息

### 2. 用户确认
- 确认技术栈选择
- 确认项目名称
- 确认部署方式

### 3. 项目规划
- 设计项目结构
- 规划文件组织
- 确定依赖关系

### 4. 代码生成
- 多轮对话生成代码
- 生成配置文件
- 创建测试文件

### 5. 质量检查
- 语法检查
- 代码规范检查
- 性能评估

### 6. 项目部署
- 创建项目目录
- 写入文件
- 推送到GitHub

## 🎨 支持的技术栈

### 编程语言
- ✅ **Python**: FastAPI, Flask, Django
- ✅ **Java**: Spring Boot, Spring MVC
- ✅ **JavaScript/Node.js**: Express, Koa
- ✅ **Go**: Gin, Echo
- ✅ **其他**: 支持任何编程语言

### 框架和库
- ✅ **Web框架**: FastAPI, Flask, Express, Spring Boot, Gin
- ✅ **数据库**: MySQL, PostgreSQL, MongoDB, Redis
- ✅ **机器学习**: PyTorch, TensorFlow, Scikit-learn
- ✅ **前端**: React, Vue, Angular
- ✅ **工具**: Docker, Kubernetes, CI/CD

### 项目类型
- ✅ **Web应用**: 网站、API、微服务
- ✅ **机器学习**: 模型训练、预测、数据分析
- ✅ **企业应用**: 管理系统、OA系统
- ✅ **Demo项目**: 演示、教程

## 🔍 质量保证

### 代码质量检查
- **语法检查**: 自动检查代码语法错误
- **规范检查**: 检查代码风格和规范
- **性能评估**: 评估代码性能
- **安全检查**: 基础安全检查

### 质量评分
系统会自动为生成的项目进行质量评分（0-100分），包括：
- 代码结构合理性
- 代码规范性
- 性能优化程度
- 安全性

## 🐙 GitHub集成

### 自动仓库创建
- 自动创建GitHub仓库
- 设置仓库描述
- 配置仓库权限

### 代码推送
- 自动初始化Git仓库
- 提交所有文件
- 推送到GitHub

## 📚 扩展性

### 自定义扩展
系统支持自定义扩展，包括：
- **技术栈扩展**: 添加新的技术栈支持
- **Agent角色扩展**: 添加新的Agent角色
- **模板扩展**: 添加新的项目模板

### 插件系统
- 支持动态加载插件
- 支持插件配置
- 支持插件依赖管理

## 🐛 故障排除

### 常见问题

1. **导入错误**
   ```bash
   # 确保在项目根目录运行
   cd /path/to/autogen_0.1.0
   python main.py
   ```

2. **GitHub推送失败**
   - 检查网络连接
   - 验证GitHub Token
   - 检查仓库权限

3. **依赖安装失败**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

### 调试模式

启用详细日志输出：
```python
# 在main.py中设置
system = EnhancedDynamicAutoGenSystem(
    api_key=None,
    interactive_mode=True,
    debug_mode=True  # 启用调试模式
)
```

## 🤝 贡献指南

### 开发环境设置

1. 克隆项目
```bash
git clone <repository-url>
cd autogen_0.1.0
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 运行测试
```bash
python main.py
```

### 代码规范

- 使用Python PEP 8规范
- 添加适当的注释
- 编写单元测试
- 更新文档

## 📄 许可证

本项目采用MIT许可证。详见LICENSE文件。

## 🙏 致谢

- [AutoGen](https://github.com/microsoft/autogen) - 多Agent对话框架
- [PyGithub](https://github.com/PyGithub/PyGithub) - GitHub API客户端
- 所有贡献者和用户

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交Issue
- 发送邮件
- 参与讨论

---

**AutoGen 动态项目生成系统** - 让AI为您生成完美的项目！🚀
