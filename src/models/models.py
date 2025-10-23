"""
Pydantic模型定义，用于Instructor控制LLM输出格式
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class GeneratedFile(BaseModel):
    """生成的文件模型"""
    path: str = Field(..., description="文件路径")
    content: str = Field(..., description="文件内容")
    is_executable: bool = Field(default=False, description="是否为可执行文件")

class Dependencies(BaseModel):
    """依赖信息模型"""
    language_version: str = Field(..., description="语言版本要求")
    packages: List[str] = Field(default=[], description="依赖包列表")

class CodeGenerationResponse(BaseModel):
    """代码生成响应模型"""
    files: List[GeneratedFile] = Field(..., description="生成的文件列表")
    dependencies: Dependencies = Field(..., description="依赖信息")
    build_commands: List[str] = Field(default=[], description="构建命令")
    run_commands: List[str] = Field(default=[], description="运行命令")
    test_commands: List[str] = Field(default=[], description="测试命令")
    
    class Config:
        json_schema_extra = {
            "example": {
                "files": [
                    {
                        "path": "pom.xml",
                        "content": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<project>...</project>",
                        "is_executable": False
                    }
                ],
                "dependencies": {
                    "language_version": "17",
                    "packages": ["spring-boot-starter-web"]
                },
                "build_commands": ["mvn clean compile"],
                "run_commands": ["mvn spring-boot:run"],
                "test_commands": ["mvn test"]
            }
        }
