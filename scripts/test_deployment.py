#!/usr/bin/env python3
"""
Test script to verify deployment system functionality
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def test_docker_build():
    """Test if Docker image can be built"""
    print("Testing Docker build...")
    result = subprocess.run(
        ["docker", "build", "-t", "projectim-test", "."],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("✓ Docker build successful")
        return True
    else:
        print(f"✗ Docker build failed: {result.stderr}")
        return False

def test_deployment_script():
    """Test if deployment script is valid"""
    print("\nTesting deployment script...")
    script_path = Path(__file__).parent / "deploy.sh"
    if script_path.exists() and os.access(script_path, os.X_OK):
        print("✓ Deployment script exists and is executable")
        return True
    else:
        print("✗ Deployment script not found or not executable")
        return False

def test_github_workflow():
    """Test if GitHub workflow is valid YAML"""
    print("\nTesting GitHub workflow...")
    workflow_path = Path(__file__).parent.parent / ".github" / "workflows" / "auto-deploy.yml"
    try:
        import yaml
        with open(workflow_path, 'r') as f:
            yaml.safe_load(f)
        print("✓ GitHub workflow is valid YAML")
        return True
    except Exception as e:
        print(f"✗ GitHub workflow validation failed: {e}")
        return False

def test_webhook_server():
    """Test if webhook server can be imported"""
    print("\nTesting webhook server...")
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        import webhook_server
        print("✓ Webhook server can be imported")
        return True
    except Exception as e:
        print(f"✗ Webhook server import failed: {e}")
        return False

def main():
    """Run all deployment tests"""
    print("=" * 50)
    print("ProjectIM Deployment System Test")
    print("=" * 50)
    
    tests = [
        test_deployment_script,
        test_github_workflow,
        test_webhook_server,
        # Docker test might fail in some environments
        # test_docker_build,
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with error: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All deployment tests passed!")
        return 0
    else:
        print("✗ Some deployment tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())