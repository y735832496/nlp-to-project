"""
项目模板系统
支持多种技术栈的模板库，支持动态配置和参数化
"""
import os
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from legacy.requirement_parser import TechStack, ProjectType, ProjectRequirement

@dataclass
class TemplateFile:
    """模板文件结构"""
    path: str
    content: str
    is_template: bool = True
    permissions: str = "644"

@dataclass
class ProjectTemplate:
    """项目模板结构"""
    name: str
    tech_stack: TechStack
    project_type: ProjectType
    description: str
    files: List[TemplateFile]
    dependencies: Dict[str, Any]
    build_commands: List[str]
    run_commands: List[str]
    environment_vars: Dict[str, str]
    docker_support: bool = False
    test_support: bool = False

class ProjectTemplateManager:
    """项目模板管理器"""
    #
    # def __init__(self):
    #     self.templates = {}
    #     self._initialize_templates()
    #
    # def _initialize_templates(self):
    #     """初始化所有模板"""
    #     # Python FastAPI 模板
    #     self.templates[TechStack.PYTHON_FASTAPI] = self._create_fastapi_template()
    #
    #     # Python Flask 模板
    #     self.templates[TechStack.PYTHON_FLASK] = self._create_flask_template()
    #
    #     # Node.js Express 模板
    #     self.templates[TechStack.NODEJS_EXPRESS] = self._create_express_template()
    #
    #     # Java Spring Boot 模板
    #     self.templates[TechStack.JAVA_SPRING_BOOT] = self._create_spring_boot_template()
    #
    #     # Go Gin 模板
    #     self.templates[TechStack.GO_GIN] = self._create_gin_template()
    
    def _create_fastapi_template(self) -> ProjectTemplate:
        """创建FastAPI模板"""
        return ProjectTemplate(
            name="FastAPI项目模板",
            tech_stack=TechStack.PYTHON_FASTAPI,
            project_type=ProjectType.WEB_APP,
            description="基于FastAPI的现代Python Web应用",
            files=[
                TemplateFile(
                    path="main.py",
                    content="""from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(title="{{project_name}}", version="1.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型
class Item(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    price: float

# 模拟数据库
items_db = []

@app.get("/")
async def root():
    return {"message": "欢迎使用{{project_name}}", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/items", response_model=List[Item])
async def get_items():
    return items_db

@app.post("/items", response_model=Item)
async def create_item(item: Item):
    item.id = len(items_db) + 1
    items_db.append(item)
    return item

@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int):
    for item in items_db:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

@app.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: int, item: Item):
    for i, existing_item in enumerate(items_db):
        if existing_item.id == item_id:
            item.id = item_id
            items_db[i] = item
            return item
    raise HTTPException(status_code=404, detail="Item not found")

@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    for i, item in enumerate(items_db):
        if item.id == item_id:
            del items_db[i]
            return {"message": "Item deleted"}
    raise HTTPException(status_code=404, detail="Item not found")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
""",
                    is_template=True
                ),
                TemplateFile(
                    path="requirements.txt",
                    content="""fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-multipart==0.0.6
""",
                    is_template=False
                ),
                TemplateFile(
                    path="README.md",
                    content="""# {{project_name}}

基于FastAPI的现代Python Web应用。

## 功能特性

- RESTful API接口
- 自动API文档
- CORS支持
- 数据验证
- 健康检查

## 安装和运行

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 运行应用：
```bash
python main.py
```

3. 访问应用：
- API: http://localhost:8000
- 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

## API接口

- GET / - 欢迎信息
- GET /health - 健康检查
- GET /items - 获取所有项目
- POST /items - 创建新项目
- GET /items/{id} - 获取特定项目
- PUT /items/{id} - 更新项目
- DELETE /items/{id} - 删除项目
""",
                    is_template=True
                )
            ],
            dependencies={
                "python": ">=3.8",
                "packages": ["fastapi", "uvicorn", "pydantic"]
            },
            build_commands=[],
            run_commands=["python main.py"],
            environment_vars={
                "PORT": "8000",
                "HOST": "0.0.0.0"
            },
            docker_support=True,
            test_support=True
        )
    
    def _create_flask_template(self) -> ProjectTemplate:
        """创建Flask模板"""
        return ProjectTemplate(
            name="Flask项目模板",
            tech_stack=TechStack.PYTHON_FLASK,
            project_type=ProjectType.WEB_APP,
            description="基于Flask的Python Web应用",
            files=[
                TemplateFile(
                    path="app.py",
                    content="""from flask import Flask, jsonify, request
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)

# 模拟数据库
items_db = []

@app.route('/')
def home():
    return jsonify({
        "message": "欢迎使用{{project_name}}",
        "version": "1.0.0"
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/items', methods=['GET'])
def get_items():
    return jsonify(items_db)

@app.route('/items', methods=['POST'])
def create_item():
    data = request.get_json()
    item = {
        "id": len(items_db) + 1,
        "name": data.get('name'),
        "description": data.get('description'),
        "price": data.get('price')
    }
    items_db.append(item)
    return jsonify(item), 201

@app.route('/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    for item in items_db:
        if item['id'] == item_id:
            return jsonify(item)
    return jsonify({"error": "Item not found"}), 404

@app.route('/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    data = request.get_json()
    for i, item in enumerate(items_db):
        if item['id'] == item_id:
            items_db[i].update(data)
            return jsonify(items_db[i])
    return jsonify({"error": "Item not found"}), 404

@app.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    for i, item in enumerate(items_db):
        if item['id'] == item_id:
            del items_db[i]
            return jsonify({"message": "Item deleted"})
    return jsonify({"error": "Item not found"}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
""",
                    is_template=True
                ),
                TemplateFile(
                    path="requirements.txt",
                    content="""flask==2.3.3
flask-cors==4.0.0
gunicorn==21.2.0
""",
                    is_template=False
                )
            ],
            dependencies={
                "python": ">=3.8",
                "packages": ["flask", "flask-cors", "gunicorn"]
            },
            build_commands=[],
            run_commands=["python app.py"],
            environment_vars={
                "FLASK_ENV": "development",
                "PORT": "5000"
            },
            docker_support=True,
            test_support=True
        )
    
    def _create_express_template(self) -> ProjectTemplate:
        """创建Express.js模板"""
        return ProjectTemplate(
            name="Express.js项目模板",
            tech_stack=TechStack.NODEJS_EXPRESS,
            project_type=ProjectType.WEB_APP,
            description="基于Express.js的Node.js Web应用",
            files=[
                TemplateFile(
                    path="app.js",
                    content="""const express = require('express');
const cors = require('cors');
const app = express();
const PORT = process.env.PORT || 3000;

// 中间件
app.use(cors());
app.use(express.json());

// 模拟数据库
let items = [];
let nextId = 1;

// 路由
app.get('/', (req, res) => {
    res.json({
        message: '欢迎使用{{project_name}}',
        version: '1.0.0'
    });
});

app.get('/health', (req, res) => {
    res.json({ status: 'healthy' });
});

app.get('/items', (req, res) => {
    res.json(items);
});

app.post('/items', (req, res) => {
    const { name, description, price } = req.body;
    const item = {
        id: nextId++,
        name,
        description,
        price
    };
    items.push(item);
    res.status(201).json(item);
});

app.get('/items/:id', (req, res) => {
    const id = parseInt(req.params.id);
    const item = items.find(i => i.id === id);
    if (!item) {
        return res.status(404).json({ error: 'Item not found' });
    }
    res.json(item);
});

app.put('/items/:id', (req, res) => {
    const id = parseInt(req.params.id);
    const itemIndex = items.findIndex(i => i.id === id);
    if (itemIndex === -1) {
        return res.status(404).json({ error: 'Item not found' });
    }
    items[itemIndex] = { ...items[itemIndex], ...req.body };
    res.json(items[itemIndex]);
});

app.delete('/items/:id', (req, res) => {
    const id = parseInt(req.params.id);
    const itemIndex = items.findIndex(i => i.id === id);
    if (itemIndex === -1) {
        return res.status(404).json({ error: 'Item not found' });
    }
    items.splice(itemIndex, 1);
    res.json({ message: 'Item deleted' });
});

app.listen(PORT, () => {
    console.log(`服务器运行在端口 ${PORT}`);
});
""",
                    is_template=True
                ),
                TemplateFile(
                    path="package.json",
                    content="""{
  "name": "{{project_name}}",
  "version": "1.0.0",
  "description": "基于Express.js的Node.js Web应用",
  "main": "app.js",
  "scripts": {
    "start": "node app.js",
    "dev": "nodemon app.js",
    "test": "jest"
  },
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5"
  },
  "devDependencies": {
    "nodemon": "^3.0.1",
    "jest": "^29.7.0"
  },
  "keywords": ["express", "nodejs", "api"],
  "author": "AI Agent",
  "license": "MIT"
}
""",
                    is_template=True
                )
            ],
            dependencies={
                "node": ">=16.0.0",
                "packages": ["express", "cors"]
            },
            build_commands=[],
            run_commands=["npm start"],
            environment_vars={
                "PORT": "3000",
                "NODE_ENV": "development"
            },
            docker_support=True,
            test_support=True
        )
    
    def _create_spring_boot_template(self) -> ProjectTemplate:
        """创建Spring Boot模板"""
        return ProjectTemplate(
            name="Spring Boot项目模板",
            tech_stack=TechStack.JAVA_SPRING_BOOT,
            project_type=ProjectType.WEB_APP,
            description="基于Spring Boot的Java Web应用",
            files=[
                TemplateFile(
                    path="src/main/java/com/example/{{project_name}}/Application.java",
                    content="""package com.example.{{project_name}};

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
""",
                    is_template=True
                ),
                TemplateFile(
                    path="src/main/java/com/example/{{project_name}}/controller/ItemController.java",
                    content="""package com.example.{{project_name}}.controller;

import com.example.{{project_name}}.model.Item;
import com.example.{{project_name}}.service.ItemService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
public class ItemController {
    
    @Autowired
    private ItemService itemService;
    
    @GetMapping("/")
    public ResponseEntity<String> home() {
        return ResponseEntity.ok("欢迎使用{{project_name}}");
    }
    
    @GetMapping("/health")
    public ResponseEntity<String> health() {
        return ResponseEntity.ok("healthy");
    }
    
    @GetMapping("/items")
    public ResponseEntity<List<Item>> getItems() {
        return ResponseEntity.ok(itemService.getAllItems());
    }
    
    @PostMapping("/items")
    public ResponseEntity<Item> createItem(@RequestBody Item item) {
        return ResponseEntity.ok(itemService.createItem(item));
    }
    
    @GetMapping("/items/{id}")
    public ResponseEntity<Item> getItem(@PathVariable Long id) {
        return ResponseEntity.ok(itemService.getItemById(id));
    }
    
    @PutMapping("/items/{id}")
    public ResponseEntity<Item> updateItem(@PathVariable Long id, @RequestBody Item item) {
        return ResponseEntity.ok(itemService.updateItem(id, item));
    }
    
    @DeleteMapping("/items/{id}")
    public ResponseEntity<String> deleteItem(@PathVariable Long id) {
        itemService.deleteItem(id);
        return ResponseEntity.ok("Item deleted");
    }
}
""",
                    is_template=True
                ),
                TemplateFile(
                    path="pom.xml",
                    content="""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    
    <groupId>com.example</groupId>
    <artifactId>{{project_name}}</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>
    
    <name>{{project_name}}</name>
    <description>基于Spring Boot的Java Web应用</description>
    
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.0</version>
        <relativePath/>
    </parent>
    
    <properties>
        <java.version>17</java.version>
    </properties>
    
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>
    
    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
""",
                    is_template=True
                )
            ],
            dependencies={
                "java": ">=17",
                "maven": ">=3.6"
            },
            build_commands=["mvn clean compile"],
            run_commands=["mvn spring-boot:run"],
            environment_vars={
                "SERVER_PORT": "8080"
            },
            docker_support=True,
            test_support=True
        )
    
    def _create_gin_template(self) -> ProjectTemplate:
        """创建Go Gin模板"""
        return ProjectTemplate(
            name="Go Gin项目模板",
            tech_stack=TechStack.GO_GIN,
            project_type=ProjectType.WEB_APP,
            description="基于Gin的Go Web应用",
            files=[
                TemplateFile(
                    path="main.go",
                    content="""package main

import (
    "net/http"
    "strconv"
    "github.com/gin-gonic/gin"
)

type Item struct {
    ID          int     `json:"id"`
    Name        string  `json:"name"`
    Description string  `json:"description"`
    Price       float64 `json:"price"`
}

var items []Item
var nextID = 1

func main() {
    r := gin.Default()
    
    // CORS中间件
    r.Use(func(c *gin.Context) {
        c.Header("Access-Control-Allow-Origin", "*")
        c.Header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        c.Header("Access-Control-Allow-Headers", "Content-Type")
        
        if c.Request.Method == "OPTIONS" {
            c.AbortWithStatus(204)
            return
        }
        
        c.Next()
    })
    
    // 路由
    r.GET("/", func(c *gin.Context) {
        c.JSON(http.StatusOK, gin.H{
            "message": "欢迎使用{{project_name}}",
            "version": "1.0.0",
        })
    })
    
    r.GET("/health", func(c *gin.Context) {
        c.JSON(http.StatusOK, gin.H{"status": "healthy"})
    })
    
    r.GET("/items", func(c *gin.Context) {
        c.JSON(http.StatusOK, items)
    })
    
    r.POST("/items", func(c *gin.Context) {
        var item Item
        if err := c.ShouldBindJSON(&item); err != nil {
            c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
            return
        }
        
        item.ID = nextID
        nextID++
        items = append(items, item)
        c.JSON(http.StatusCreated, item)
    })
    
    r.GET("/items/:id", func(c *gin.Context) {
        id, err := strconv.Atoi(c.Param("id"))
        if err != nil {
            c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid ID"})
            return
        }
        
        for _, item := range items {
            if item.ID == id {
                c.JSON(http.StatusOK, item)
                return
            }
        }
        
        c.JSON(http.StatusNotFound, gin.H{"error": "Item not found"})
    })
    
    r.PUT("/items/:id", func(c *gin.Context) {
        id, err := strconv.Atoi(c.Param("id"))
        if err != nil {
            c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid ID"})
            return
        }
        
        var updatedItem Item
        if err := c.ShouldBindJSON(&updatedItem); err != nil {
            c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
            return
        }
        
        for i, item := range items {
            if item.ID == id {
                updatedItem.ID = id
                items[i] = updatedItem
                c.JSON(http.StatusOK, updatedItem)
                return
            }
        }
        
        c.JSON(http.StatusNotFound, gin.H{"error": "Item not found"})
    })
    
    r.DELETE("/items/:id", func(c *gin.Context) {
        id, err := strconv.Atoi(c.Param("id"))
        if err != nil {
            c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid ID"})
            return
        }
        
        for i, item := range items {
            if item.ID == id {
                items = append(items[:i], items[i+1:]...)
                c.JSON(http.StatusOK, gin.H{"message": "Item deleted"})
                return
            }
        }
        
        c.JSON(http.StatusNotFound, gin.H{"error": "Item not found"})
    })
    
    r.Run(":8080")
}
""",
                    is_template=True
                ),
                TemplateFile(
                    path="go.mod",
                    content="""module {{project_name}}

go 1.21

require github.com/gin-gonic/gin v1.9.1
""",
                    is_template=True
                )
            ],
            dependencies={
                "go": ">=1.21"
            },
            build_commands=["go mod tidy", "go build -o {{project_name}}"],
            run_commands=["./{{project_name}}"],
            environment_vars={
                "PORT": "8080"
            },
            docker_support=True,
            test_support=True
        )

    def customize_template(self, template: ProjectTemplate, requirements: ProjectRequirement) -> ProjectTemplate:
        """根据需求自定义模板"""
        # 这里可以根据需求动态修改模板
        # 例如：添加认证功能、数据库支持、特定功能模块等
        customized_template = template
        
        # 如果需要认证功能
        if requirements.authentication_required:
            customized_template = self._add_authentication_to_template(customized_template)
        
        # 如果需要数据库
        if requirements.database_required:
            customized_template = self._add_database_to_template(customized_template)
        
        return customized_template
    
    def _add_authentication_to_template(self, template: ProjectTemplate) -> ProjectTemplate:
        """为模板添加认证功能"""
        # 这里可以添加认证相关的文件和配置
        # 具体实现取决于技术栈
        return template
    
    def _add_database_to_template(self, template: ProjectTemplate) -> ProjectTemplate:
        """为模板添加数据库支持"""
        # 这里可以添加数据库相关的文件和配置
        # 具体实现取决于技术栈
        return template
