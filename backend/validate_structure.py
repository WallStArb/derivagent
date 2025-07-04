#!/usr/bin/env python3
"""
Validate the Derivagent backend structure
Checks file structure, imports, and basic functionality without requiring dependencies
"""

import os
import sys
import json
from datetime import datetime

def check_file_structure():
    """Check if all required files exist"""
    print("📁 Checking file structure...")
    
    required_files = [
        "main.py",
        "requirements.txt",
        "test_api.py",
        "ai/model_router.py",
        "ai/agent_clients.py",
        "config/model_config.json"
    ]
    
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            missing_files.append(file_path)
    
    return len(missing_files) == 0

def check_main_api():
    """Check main.py structure"""
    print("\n🔍 Checking main.py structure...")
    
    try:
        with open("main.py", "r") as f:
            content = f.read()
        
        # Check for required imports and components
        required_components = [
            "from fastapi import FastAPI",
            "from ai.agent_clients import",
            "app = FastAPI(",
            "@app.post(\"/agents/market-regime\",",
            "@app.post(\"/agents/volatility-surface\",",
            "@app.post(\"/agents/support-resistance\",",
            "@app.post(\"/agents/liquidity-analysis\",",
            "@app.get(\"/health\",",
            "async def startup_event():"
        ]
        
        missing_components = []
        for component in required_components:
            if component in content:
                print(f"✅ {component}")
            else:
                print(f"❌ {component} - MISSING")
                missing_components.append(component)
        
        return len(missing_components) == 0
        
    except FileNotFoundError:
        print("❌ main.py not found")
        return False
    except Exception as e:
        print(f"❌ Error reading main.py: {e}")
        return False

def check_agent_framework():
    """Check agent_clients.py structure"""
    print("\n🤖 Checking agent framework...")
    
    try:
        with open("ai/agent_clients.py", "r") as f:
            content = f.read()
        
        # Check for required classes and functions
        required_classes = [
            "class BaseAgent(ABC):",
            "class MarketRegimeAgent(BaseAgent):",
            "class VolatilitySurfaceAgent(BaseAgent):",
            "class SupportResistanceAgent(BaseAgent):",
            "class LiquidityAnalysisAgent(BaseAgent):",
            "class AgentFactory:",
            "async def analyze("
        ]
        
        missing_classes = []
        for cls in required_classes:
            if cls in content:
                print(f"✅ {cls}")
            else:
                print(f"❌ {cls} - MISSING")
                missing_classes.append(cls)
        
        return len(missing_classes) == 0
        
    except FileNotFoundError:
        print("❌ ai/agent_clients.py not found")
        return False
    except Exception as e:
        print(f"❌ Error reading agent_clients.py: {e}")
        return False

def check_model_config():
    """Check model configuration"""
    print("\n⚙️  Checking model configuration...")
    
    try:
        with open("config/model_config.json", "r") as f:
            config = json.load(f)
        
        # Check required configuration sections
        required_sections = [
            "model_list",
            "agent_routing",
            "fallback_strategy",
            "cost_optimization"
        ]
        
        missing_sections = []
        for section in required_sections:
            if section in config:
                print(f"✅ {section}")
            else:
                print(f"❌ {section} - MISSING")
                missing_sections.append(section)
        
        # Check model list structure
        if "model_list" in config and len(config["model_list"]) > 0:
            model = config["model_list"][0]
            if "model_name" in model and "litellm_params" in model:
                print("✅ Model configuration structure valid")
            else:
                print("❌ Model configuration structure invalid")
                return False
        
        return len(missing_sections) == 0
        
    except FileNotFoundError:
        print("❌ config/model_config.json not found")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in model_config.json: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading model_config.json: {e}")
        return False

def check_requirements():
    """Check requirements.txt"""
    print("\n📋 Checking requirements.txt...")
    
    try:
        with open("requirements.txt", "r") as f:
            content = f.read()
        
        # Check for essential packages
        essential_packages = [
            "fastapi",
            "uvicorn",
            "pydantic",
            "litellm",
            "openai",
            "python-dotenv"
        ]
        
        missing_packages = []
        for package in essential_packages:
            if package in content:
                print(f"✅ {package}")
            else:
                print(f"❌ {package} - MISSING")
                missing_packages.append(package)
        
        return len(missing_packages) == 0
        
    except FileNotFoundError:
        print("❌ requirements.txt not found")
        return False
    except Exception as e:
        print(f"❌ Error reading requirements.txt: {e}")
        return False

def validate_api_endpoints():
    """Validate API endpoint structure"""
    print("\n🌐 Validating API endpoints...")
    
    expected_endpoints = [
        "/health",
        "/agents/market-regime",
        "/agents/volatility-surface", 
        "/agents/support-resistance",
        "/agents/liquidity-analysis",
        "/agents/batch-analysis",
        "/agents/info",
        "/test/agents"
    ]
    
    try:
        with open("main.py", "r") as f:
            content = f.read()
        
        missing_endpoints = []
        for endpoint in expected_endpoints:
            if f'"{endpoint}"' in content:
                print(f"✅ {endpoint}")
            else:
                print(f"❌ {endpoint} - MISSING")
                missing_endpoints.append(endpoint)
        
        return len(missing_endpoints) == 0
        
    except Exception as e:
        print(f"❌ Error validating endpoints: {e}")
        return False

def main():
    """Main validation function"""
    print("🚀 Validating Derivagent Backend Structure...")
    print("=" * 50)
    
    tests = [
        ("File Structure", check_file_structure),
        ("Main API", check_main_api),
        ("Agent Framework", check_agent_framework),
        ("Model Configuration", check_model_config),
        ("Requirements", check_requirements),
        ("API Endpoints", validate_api_endpoints)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 30)
        result = test_func()
        results.append((test_name, result))
    
    print("\n📊 Validation Results Summary:")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Validation Score: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All validations passed! Backend structure is ready.")
        print("\nNext steps:")
        print("1. Install dependencies: python3 setup.py")
        print("2. Set up environment: cp .env.example .env")
        print("3. Start server: uvicorn main:app --reload")
        return True
    else:
        print("⚠️  Some validations failed. Check the output above.")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        sys.exit(1)