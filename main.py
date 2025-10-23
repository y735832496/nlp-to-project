#!/usr/bin/env python3
"""
灵活需求解析的快速启动脚本
支持动态技术栈和AI自主决策
"""
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.enhanced_autogen_system import EnhancedDynamicAutoGenSystem

async def main():
    """主函数"""
    print("🚀 灵活需求解析的增强AutoGen系统")
    print("=" * 50)
    print("✨ 支持动态技术栈和AI自主决策")
    print("✨ 无技术栈限制，让AI自由发挥")
    print("=" * 50)
    
    # 获取用户输入
    user_input = input("\n请输入您的项目需求: ").strip()
    
    if not user_input:
        print("❌ 请输入有效的项目需求")
        return
    
    print(f"\n🔍 解析需求: {user_input}")
    
    try:
        # 创建增强系统
        system = EnhancedDynamicAutoGenSystem(
            api_key=None,  # 使用模拟客户端
            github_token=os.getenv("GITHUB_TOKEN"),
            github_username=os.getenv("GITHUB_USERNAME", "ai-agent"),
            interactive_mode=True
        )
        
        # 运行系统
        result = await system.generate_complex_project(user_input)
        
        if result:
            print("\n🎉 项目生成成功！")
            print(f"📁 项目路径: {result.get('project_path', '未知')}")
            print(f"🐙 GitHub仓库: {result.get('github_url', '未创建')}")
        else:
            print("\n❌ 项目生成失败")
            
    except Exception as e:
        print(f"\n❌ 系统运行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
