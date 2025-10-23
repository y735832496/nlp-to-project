"""
配置管理系统
动态生成依赖文件和环境配置
"""
import os
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from legacy.requirement_parser import TechStack, ProjectRequirement

class ConfigType(Enum):
    """配置类型枚举"""
    DEPENDENCIES = "dependencies"
    ENVIRONMENT = "environment"
    DOCKER = "docker"
    CI_CD = "ci_cd"
    DATABASE = "database"
    SECURITY = "security"

@dataclass
class ConfigFile:
    """配置文件结构"""
    path: str
    content: str
    config_type: ConfigType
    is_template: bool = False

class ConfigurationManager:
    """配置管理器"""
    
    def __init__(self):
        self.config_templates = {}
        self._initialize_config_templates()
    
    def _initialize_config_templates(self):
        """初始化配置模板"""
        # Python依赖配置
        self.config_templates[TechStack.PYTHON_FASTAPI] = {
            ConfigType.DEPENDENCIES: self._create_python_dependencies,
            ConfigType.ENVIRONMENT: self._create_python_environment,
            ConfigType.DOCKER: self._create_python_docker,
            ConfigType.CI_CD: self._create_python_ci_cd,
            ConfigType.DATABASE: self._create_python_database,
            ConfigType.SECURITY: self._create_python_security
        }
        
        # Node.js配置
        self.config_templates[TechStack.NODEJS_EXPRESS] = {
            ConfigType.DEPENDENCIES: self._create_nodejs_dependencies,
            ConfigType.ENVIRONMENT: self._create_nodejs_environment,
            ConfigType.DOCKER: self._create_nodejs_docker,
            ConfigType.CI_CD: self._create_nodejs_ci_cd,
            ConfigType.DATABASE: self._create_nodejs_database,
            ConfigType.SECURITY: self._create_nodejs_security
        }
        
        # Java配置
        self.config_templates[TechStack.JAVA_SPRING_BOOT] = {
            ConfigType.DEPENDENCIES: self._create_java_dependencies,
            ConfigType.ENVIRONMENT: self._create_java_environment,
            ConfigType.DOCKER: self._create_java_docker,
            ConfigType.CI_CD: self._create_java_ci_cd,
            ConfigType.DATABASE: self._create_java_database,
            ConfigType.SECURITY: self._create_java_security
        }
        
        # Go配置
        self.config_templates[TechStack.GO_GIN] = {
            ConfigType.DEPENDENCIES: self._create_go_dependencies,
            ConfigType.ENVIRONMENT: self._create_go_environment,
            ConfigType.DOCKER: self._create_go_docker,
            ConfigType.CI_CD: self._create_go_ci_cd,
            ConfigType.DATABASE: self._create_go_database,
            ConfigType.SECURITY: self._create_go_security
        }
    
    def generate_configurations(self, requirements: ProjectRequirement, user_confirmations: Dict[str, Any]) -> List[ConfigFile]:
        """生成项目配置"""
        config_files = []
        
        tech_stack = requirements.tech_stack
        if tech_stack not in self.config_templates:
            return config_files
        
        templates = self.config_templates[tech_stack]
        
        # 生成依赖配置
        if ConfigType.DEPENDENCIES in templates:
            config_files.extend(templates[ConfigType.DEPENDENCIES](requirements, user_confirmations))
        
        # 生成环境配置
        if ConfigType.ENVIRONMENT in templates:
            config_files.extend(templates[ConfigType.ENVIRONMENT](requirements, user_confirmations))
        
        # 生成Docker配置
        if user_confirmations.get("deployment") == "docker":
            if ConfigType.DOCKER in templates:
                config_files.extend(templates[ConfigType.DOCKER](requirements, user_confirmations))
        
        # 生成CI/CD配置
        if ConfigType.CI_CD in templates:
            config_files.extend(templates[ConfigType.CI_CD](requirements, user_confirmations))
        
        # 生成数据库配置
        if requirements.database_required and ConfigType.DATABASE in templates:
            config_files.extend(templates[ConfigType.DATABASE](requirements, user_confirmations))
        
        # 生成安全配置
        if requirements.authentication_required and ConfigType.SECURITY in templates:
            config_files.extend(templates[ConfigType.SECURITY](requirements, user_confirmations))
        
        return config_files
    
    # Python配置生成器
    def _create_python_dependencies(self, requirements: ProjectRequirement, user_confirmations: Dict[str, Any]) -> List[ConfigFile]:
        """创建Python依赖配置"""
        files = []
        
        # requirements.txt
        dependencies = [
            "fastapi==0.104.1",
            "uvicorn[standard]==0.24.0",
            "pydantic==2.5.0",
            "python-multipart==0.0.6"
        ]
        
        if requirements.database_required:
            dependencies.extend([
                "sqlalchemy==2.0.23",
                "alembic==1.12.1",
                "psycopg2-binary==2.9.9"
            ])
        
        if requirements.authentication_required:
            dependencies.extend([
                "python-jose[cryptography]==3.3.0",
                "passlib[bcrypt]==1.7.4",
                "python-multipart==0.0.6"
            ])
        
        # 添加测试依赖
        dependencies.extend([
            "pytest==7.4.3",
            "pytest-asyncio==0.21.1",
            "httpx==0.25.2"
        ])
        
        files.append(ConfigFile(
            path="requirements.txt",
            content="\n".join(dependencies),
            config_type=ConfigType.DEPENDENCIES
        ))
        
        # requirements-dev.txt
        dev_dependencies = dependencies + [
            "black==23.11.0",
            "flake8==6.1.0",
            "mypy==1.7.1",
            "bandit==1.7.5",
            "coverage==7.3.2"
        ]
        
        files.append(ConfigFile(
            path="requirements-dev.txt",
            content="\n".join(dev_dependencies),
            config_type=ConfigType.DEPENDENCIES
        ))
        
        return files
    
    def _create_python_environment(self, requirements: ProjectRequirement, user_confirmations: Dict[str, Any]) -> List[ConfigFile]:
        """创建Python环境配置"""
        files = []
        
        # .env文件
        env_content = f"""# 应用配置
APP_NAME={requirements.project_name}
APP_VERSION=1.0.0
DEBUG=true
HOST=0.0.0.0
PORT=8000

# 数据库配置
DATABASE_URL=sqlite:///./app.db
"""
        
        if requirements.database_required:
            env_content += """
# 生产环境数据库
# DATABASE_URL=postgresql://user:password@localhost/dbname
"""
        
        if requirements.authentication_required:
            env_content += """
# 认证配置
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
"""
        
        files.append(ConfigFile(
            path=".env",
            content=env_content,
            config_type=ConfigType.ENVIRONMENT
        ))
        
        # .env.example
        files.append(ConfigFile(
            path=".env.example",
            content=env_content,
            config_type=ConfigType.ENVIRONMENT
        ))
        
        return files
    
    def _create_python_docker(self, requirements: ProjectRequirement, user_confirmations: Dict[str, Any]) -> List[ConfigFile]:
        """创建Python Docker配置"""
        files = []
        
        # Dockerfile
        dockerfile_content = """FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 运行应用
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
        
        files.append(ConfigFile(
            path="Dockerfile",
            content=dockerfile_content,
            config_type=ConfigType.DOCKER
        ))
        
        # docker-compose.yml
        compose_content = f"""version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/{requirements.project_name}
    depends_on:
      - db
    volumes:
      - .:/app

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: {requirements.project_name}
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
"""
        
        files.append(ConfigFile(
            path="docker-compose.yml",
            content=compose_content,
            config_type=ConfigType.DOCKER
        ))
        
        return files
    
    def _create_python_ci_cd(self, requirements: ProjectRequirement, user_confirmations: Dict[str, Any]) -> List[ConfigFile]:
        """创建Python CI/CD配置"""
        files = []
        
        # GitHub Actions
        github_actions_content = """name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-dev.txt
    
    - name: Lint with flake8
      run: |
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
    
    - name: Security check with bandit
      run: |
        bandit -r . -f json -o bandit-report.json || true
    
    - name: Test with pytest
      run: |
        pytest --cov=. --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
"""
        
        files.append(ConfigFile(
            path=".github/workflows/ci.yml",
            content=github_actions_content,
            config_type=ConfigType.CI_CD
        ))
        
        return files
    
    def _create_python_database(self, requirements: ProjectRequirement, user_confirmations: Dict[str, Any]) -> List[ConfigFile]:
        """创建Python数据库配置"""
        files = []
        
        # alembic.ini
        alembic_content = """[alembic]
script_location = alembic
prepend_sys_path = False
timezone = UTC
sqlalchemy.url = sqlite:///./app.db

[post_write_hooks]
hooks = black
black.type = console_scripts
black.entrypoint = black
black.options = -l 79 REVISION_SCRIPT_FILENAME

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""
        
        files.append(ConfigFile(
            path="alembic.ini",
            content=alembic_content,
            config_type=ConfigType.DATABASE
        ))
        
        return files
    
    def _create_python_security(self, requirements: ProjectRequirement, user_confirmations: Dict[str, Any]) -> List[ConfigFile]:
        """创建Python安全配置"""
        files = []
        
        # .bandit
        bandit_content = """[bandit]
exclude_dirs = tests,venv,env
skips = B101,B601
"""
        
        files.append(ConfigFile(
            path=".bandit",
            content=bandit_content,
            config_type=ConfigType.SECURITY
        ))
        
        return files
    
    # Node.js配置生成器
    def _create_nodejs_dependencies(self, requirements: ProjectRequirement, user_confirmations: Dict[str, Any]) -> List[ConfigFile]:
        """创建Node.js依赖配置"""
        files = []
        
        # package.json
        package_json = {
            "name": requirements.project_name,
            "version": "1.0.0",
            "description": requirements.description,
            "main": "app.js",
            "scripts": {
                "start": "node app.js",
                "dev": "nodemon app.js",
                "test": "jest",
                "lint": "eslint .",
                "lint:fix": "eslint . --fix"
            },
            "dependencies": {
                "express": "^4.18.2",
                "cors": "^2.8.5",
                "helmet": "^7.1.0",
                "morgan": "^1.10.0"
            },
            "devDependencies": {
                "nodemon": "^3.0.1",
                "jest": "^29.7.0",
                "eslint": "^8.54.0",
                "supertest": "^6.3.3"
            },
            "keywords": ["express", "nodejs", "api"],
            "author": "AI Agent",
            "license": "MIT"
        }
        
        if requirements.database_required:
            package_json["dependencies"]["mongoose"] = "^8.0.3"
        
        if requirements.authentication_required:
            package_json["dependencies"]["jsonwebtoken"] = "^9.0.2"
            package_json["dependencies"]["bcryptjs"] = "^2.4.3"
        
        files.append(ConfigFile(
            path="package.json",
            content=json.dumps(package_json, indent=2),
            config_type=ConfigType.DEPENDENCIES
        ))
        
        return files
    
    def _create_nodejs_environment(self, requirements: ProjectRequirement, user_confirmations: Dict[str, Any]) -> List[ConfigFile]:
        """创建Node.js环境配置"""
        files = []
        
        # .env
        env_content = f"""NODE_ENV=development
PORT=3000
APP_NAME={requirements.project_name}
"""
        
        if requirements.database_required:
            env_content += """
DATABASE_URL=mongodb://localhost:27017/your-database
"""
        
        if requirements.authentication_required:
            env_content += """
JWT_SECRET=your-jwt-secret-key
JWT_EXPIRES_IN=24h
"""
        
        files.append(ConfigFile(
            path=".env",
            content=env_content,
            config_type=ConfigType.ENVIRONMENT
        ))
        
        return files
    
    def _create_nodejs_docker(self, requirements: ProjectRequirement, user_confirmations: Dict[str, Any]) -> List[ConfigFile]:
        """创建Node.js Docker配置"""
        files = []
        
        # Dockerfile
        dockerfile_content = """FROM node:18-alpine

WORKDIR /app

# 复制package文件
COPY package*.json ./

# 安装依赖
RUN npm ci --only=production

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 3000

# 运行应用
CMD ["npm", "start"]
"""
        
        files.append(ConfigFile(
            path="Dockerfile",
            content=dockerfile_content,
            config_type=ConfigType.DOCKER
        ))
        
        return files
    
    def _create_nodejs_ci_cd(self, requirements: ProjectRequirement, user_confirmations: Dict[str, Any]) -> List[ConfigFile]:
        """创建Node.js CI/CD配置"""
        files = []
        
        # GitHub Actions
        github_actions_content = """name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Run linter
      run: npm run lint
    
    - name: Run tests
      run: npm test
    
    - name: Build application
      run: npm run build
"""
        
        files.append(ConfigFile(
            path=".github/workflows/ci.yml",
            content=github_actions_content,
            config_type=ConfigType.CI_CD
        ))
        
        return files
    
    def _create_nodejs_database(self, requirements: ProjectRequirement, user_confirmations: Dict[str, Any]) -> List[ConfigFile]:
        """创建Node.js数据库配置"""
        files = []
        
        # 数据库连接配置
        db_config_content = """const mongoose = require('mongoose');

const connectDB = async () => {
    try {
        const conn = await mongoose.connect(process.env.DATABASE_URL, {
            useNewUrlParser: true,
            useUnifiedTopology: true,
        });
        console.log(`MongoDB Connected: ${conn.connection.host}`);
    } catch (error) {
        console.error('Database connection error:', error);
        process.exit(1);
    }
};

module.exports = connectDB;
"""
        
        files.append(ConfigFile(
            path="config/database.js",
            content=db_config_content,
            config_type=ConfigType.DATABASE
        ))
        
        return files
    
    def _create_nodejs_security(self, requirements: ProjectRequirement, user_confirmations: Dict[str, Any]) -> List[ConfigFile]:
        """创建Node.js安全配置"""
        files = []
        
        # .eslintrc.js
        eslint_content = """module.exports = {
    env: {
        node: true,
        es2021: true,
        jest: true
    },
    extends: [
        'eslint:recommended'
    ],
    parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module'
    },
    rules: {
        'no-console': 'warn',
        'no-unused-vars': 'error',
        'prefer-const': 'error'
    }
};
"""
        
        files.append(ConfigFile(
            path=".eslintrc.js",
            content=eslint_content,
            config_type=ConfigType.SECURITY
        ))
        
        return files
    
    # Java配置生成器
    def _create_java_dependencies(self, requirements: ProjectRequirement, user_confirmations: Dict[str, Any]) -> List[ConfigFile]:
        """创建Java依赖配置"""
        files = []
        
        # pom.xml已经在项目模板中定义，这里可以添加额外的配置
        return files
    
    def _create_java_environment(self, requirements: ProjectRequirement, user_confirmations: Dict[str, Any]) -> List[ConfigFile]:
        """创建Java环境配置"""
        files = []
        
        # application.yml
        app_config_content = f"""server:
  port: 8080

spring:
  application:
    name: {requirements.project_name}
  
  datasource:
    url: jdbc:sqlite:./app.db
    driver-class-name: org.sqlite.JDBC
    
  jpa:
    hibernate:
      ddl-auto: update
    show-sql: true

logging:
  level:
    com.example.{requirements.project_name}: DEBUG
"""
        
        files.append(ConfigFile(
            path="src/main/resources/application.yml",
            content=app_config_content,
            config_type=ConfigType.ENVIRONMENT
        ))
        
        return files
    
    def _create_java_docker(self, requirements: ProjectRequirement, user_confirmations: Dict[str, Any]) -> List[ConfigFile]:
        """创建Java Docker配置"""
        files = []
        
        # Dockerfile
        dockerfile_content = """FROM openjdk:17-jdk-slim

WORKDIR /app

# 复制Maven文件
COPY pom.xml .
COPY src ./src

# 构建应用
RUN apt-get update && apt-get install -y maven
RUN mvn clean package -DskipTests

# 运行应用
EXPOSE 8080
CMD ["java", "-jar", "target/*.jar"]
"""
        
        files.append(ConfigFile(
            path="Dockerfile",
            content=dockerfile_content,
            config_type=ConfigType.DOCKER
        ))
        
        return files
    
    def _create_java_ci_cd(self, requirements: ProjectRequirement, user_confirmations: Dict[str, Any]) -> List[ConfigFile]:
        """创建Java CI/CD配置"""
        files = []
        
        # GitHub Actions
        github_actions_content = """name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up JDK 17
      uses: actions/setup-java@v4
      with:
        java-version: '17'
        distribution: 'temurin'
    
    - name: Cache Maven dependencies
      uses: actions/cache@v3
      with:
        path: ~/.m2
        key: ${{ runner.os }}-m2-${{ hashFiles('**/pom.xml') }}
    
    - name: Run tests
      run: mvn test
    
    - name: Build application
      run: mvn clean package -DskipTests
"""
        
        files.append(ConfigFile(
            path=".github/workflows/ci.yml",
            content=github_actions_content,
            config_type=ConfigType.CI_CD
        ))
        
        return files
    
    def _create_java_database(self, requirements: ProjectRequirement, user_confirmations: Dict[str, Any]) -> List[ConfigFile]:
        """创建Java数据库配置"""
        files = []
        
        # 数据库配置已经在application.yml中定义
        return files
    
    def _create_java_security(self, requirements: ProjectRequirement, user_confirmations: Dict[str, Any]) -> List[ConfigFile]:
        """创建Java安全配置"""
        files = []
        
        # 安全配置
        security_config_content = """@Configuration
@EnableWebSecurity
public class SecurityConfig {
    
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .csrf().disable()
            .authorizeHttpRequests(authz -> authz
                .requestMatchers("/api/public/**").permitAll()
                .anyRequest().authenticated()
            )
            .httpBasic();
        return http.build();
    }
}
"""
        
        files.append(ConfigFile(
            path="src/main/java/com/example/security/SecurityConfig.java",
            content=security_config_content,
            config_type=ConfigType.SECURITY
        ))
        
        return files
    
    # Go配置生成器
    def _create_go_dependencies(self, requirements: ProjectRequirement, user_confirmations: Dict[str, Any]) -> List[ConfigFile]:
        """创建Go依赖配置"""
        files = []
        
        # go.mod已经在项目模板中定义
        return files
    
    def _create_go_environment(self, requirements: ProjectRequirement, user_confirmations: Dict[str, Any]) -> List[ConfigFile]:
        """创建Go环境配置"""
        files = []
        
        # .env
        env_content = f"""APP_NAME={requirements.project_name}
PORT=8080
HOST=0.0.0.0
"""
        
        if requirements.database_required:
            env_content += """
DATABASE_URL=postgres://user:password@localhost/dbname?sslmode=disable
"""
        
        files.append(ConfigFile(
            path=".env",
            content=env_content,
            config_type=ConfigType.ENVIRONMENT
        ))
        
        return files
    
    def _create_go_docker(self, requirements: ProjectRequirement, user_confirmations: Dict[str, Any]) -> List[ConfigFile]:
        """创建Go Docker配置"""
        files = []
        
        # Dockerfile
        dockerfile_content = """FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN go build -o main .

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/

COPY --from=builder /app/main .

EXPOSE 8080
CMD ["./main"]
"""
        
        files.append(ConfigFile(
            path="Dockerfile",
            content=dockerfile_content,
            config_type=ConfigType.DOCKER
        ))
        
        return files
    
    def _create_go_ci_cd(self, requirements: ProjectRequirement, user_confirmations: Dict[str, Any]) -> List[ConfigFile]:
        """创建Go CI/CD配置"""
        files = []
        
        # GitHub Actions
        github_actions_content = """name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Go
      uses: actions/setup-go@v4
      with:
        go-version: '1.21'
    
    - name: Install dependencies
      run: go mod download
    
    - name: Run tests
      run: go test ./...
    
    - name: Build application
      run: go build -o main .
"""
        
        files.append(ConfigFile(
            path=".github/workflows/ci.yml",
            content=github_actions_content,
            config_type=ConfigType.CI_CD
        ))
        
        return files
    
    def _create_go_database(self, requirements: ProjectRequirement, user_confirmations: Dict[str, Any]) -> List[ConfigFile]:
        """创建Go数据库配置"""
        files = []
        
        # 数据库连接配置
        db_config_content = """package database

import (
    "database/sql"
    "fmt"
    "os"
    _ "github.com/lib/pq"
)

func ConnectDB() (*sql.DB, error) {
    dbURL := os.Getenv("DATABASE_URL")
    if dbURL == "" {
        dbURL = "postgres://user:password@localhost/dbname?sslmode=disable"
    }
    
    db, err := sql.Open("postgres", dbURL)
    if err != nil {
        return nil, fmt.Errorf("failed to connect to database: %w", err)
    }
    
    if err := db.Ping(); err != nil {
        return nil, fmt.Errorf("failed to ping database: %w", err)
    }
    
    return db, nil
}
"""
        
        files.append(ConfigFile(
            path="database/connection.go",
            content=db_config_content,
            config_type=ConfigType.DATABASE
        ))
        
        return files
    
    def _create_go_security(self, requirements: ProjectRequirement, user_confirmations: Dict[str, Any]) -> List[ConfigFile]:
        """创建Go安全配置"""
        files = []
        
        # 安全中间件
        security_content = """package middleware

import (
    "net/http"
    "strings"
)

func CORS(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("Access-Control-Allow-Origin", "*")
        w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
        
        if r.Method == "OPTIONS" {
            w.WriteHeader(http.StatusOK)
            return
        }
        
        next.ServeHTTP(w, r)
    })
}

func SecurityHeaders(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("X-Content-Type-Options", "nosniff")
        w.Header().Set("X-Frame-Options", "DENY")
        w.Header().Set("X-XSS-Protection", "1; mode=block")
        next.ServeHTTP(w, r)
    })
}
"""
        
        files.append(ConfigFile(
            path="middleware/security.go",
            content=security_content,
            config_type=ConfigType.SECURITY
        ))
        
        return files
