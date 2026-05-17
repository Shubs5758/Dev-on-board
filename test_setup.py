"""
Quick test script to verify the DevOnboard setup.
Run this before starting the Streamlit app.
"""

import sys
import importlib.util
import io

# Fix encoding for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def check_module(module_name, package_name=None):
    """Check if a module is installed."""
    package = package_name or module_name
    spec = importlib.util.find_spec(module_name)
    if spec is None:
        print(f"❌ {package} is NOT installed")
        return False
    else:
        print(f"✅ {package} is installed")
        return True

def main():
    print("🧭 DevOnboard Setup Checker\n")
    print("=" * 50)
    
    # Check Python version
    print(f"\n📌 Python Version: {sys.version}")
    if sys.version_info < (3, 10):
        print("⚠️  Warning: Python 3.10+ is recommended")
    else:
        print("✅ Python version is compatible")
    
    print("\n" + "=" * 50)
    print("\n📦 Checking Dependencies:\n")
    
    # Check required packages
    required = [
        ("streamlit", "streamlit"),
        ("google.generativeai", "google-generativeai"),
        ("git", "gitpython"),
        ("networkx", "networkx"),
        ("pyvis", "pyvis")
    ]
    
    all_installed = True
    for module, package in required:
        if not check_module(module, package):
            all_installed = False
    
    print("\n" + "=" * 50)
    
    # Check local modules
    print("\n📄 Checking Local Modules:\n")
    
    local_modules = ["utils", "ast_parser", "graph_builder", "agents", "app"]
    for module in local_modules:
        try:
            spec = importlib.util.spec_from_file_location(module, f"{module}.py")
            if spec and spec.loader:
                print(f"✅ {module}.py found")
            else:
                print(f"❌ {module}.py NOT found")
                all_installed = False
        except Exception as e:
            print(f"❌ {module}.py error: {e}")
            all_installed = False
    
    print("\n" + "=" * 50)
    
    # Check .streamlit directory
    print("\n⚙️  Checking Configuration:\n")
    
    import os
    if os.path.exists(".streamlit"):
        print("✅ .streamlit directory exists")
        
        if os.path.exists(".streamlit/config.toml"):
            print("✅ config.toml exists")
        else:
            print("⚠️  config.toml not found (optional)")
        
        if os.path.exists(".streamlit/secrets.toml"):
            print("✅ secrets.toml exists")
            
            # Check if API key is configured
            try:
                with open(".streamlit/secrets.toml", "r") as f:
                    content = f.read()
                    if "your-gemini-api-key-here" in content:
                        print("⚠️  WARNING: Please add your actual Gemini API key to secrets.toml")
                    else:
                        print("✅ API key appears to be configured")
            except:
                pass
        else:
            print("❌ secrets.toml NOT found - please create it with your API key")
            all_installed = False
    else:
        print("❌ .streamlit directory NOT found")
        all_installed = False
    
    print("\n" + "=" * 50)
    print("\n📊 Summary:\n")
    
    if all_installed:
        print("✅ All checks passed! You're ready to run DevOnboard.")
        print("\n🚀 Start the app with: streamlit run app.py")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print("\n📝 To install missing dependencies:")
        print("   pip install -r requirements.txt")
        print("\n🔑 To configure API key:")
        print("   1. Get key from: https://makersuite.google.com/app/apikey")
        print("   2. Add to .streamlit/secrets.toml")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()

# Made with Bob
