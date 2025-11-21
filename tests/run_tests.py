#!/usr/bin/env python3
"""
Test Runner - PramaIA Test Suite
Script di esecuzione test con opzioni comuni
"""

import subprocess
import sys
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Esegue comando e mostra risultato"""
    print(f"\n{'=' * 80}")
    print(f"  {description}")
    print(f"{'=' * 80}\n")
    
    try:
        result = subprocess.run(cmd, shell=True)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="PramaIA Test Suite Runner")
    parser.add_argument(
        "suite",
        nargs="?",
        default="all",
        choices=["all", "inventory", "crud", "e2e"],
        help="Which test suite to run"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "-s", "--show-output",
        action="store_true",
        help="Show stdout/stderr"
    )
    parser.add_argument(
        "-x", "--stop-on-failure",
        action="store_true",
        help="Stop on first failure"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Generate HTML report"
    )
    
    args = parser.parse_args()
    
    # Costruisci comando pytest
    cmd_parts = ["pytest"]
    
    # Determina quale suite eseguire
    test_path = "tests/"
    if args.suite == "inventory":
        test_path = "tests/test_inventory.py"
    elif args.suite == "crud":
        test_path = "tests/test_crud_operations.py"
    elif args.suite == "e2e":
        test_path = "tests/test_e2e_pipeline.py"
    
    cmd_parts.append(test_path)
    
    # Opzioni verbosity
    if args.verbose:
        cmd_parts.append("-vv")
    else:
        cmd_parts.append("-v")
    
    if args.show_output:
        cmd_parts.append("-s")
    
    # Altre opzioni
    if args.stop_on_failure:
        cmd_parts.append("-x")
    
    if args.coverage:
        cmd_parts.append("--cov=backend")
        cmd_parts.append("--cov-report=html")
    
    if args.html:
        cmd_parts.append("--html=test_report.html")
        cmd_parts.append("--self-contained-html")
    
    # Esegui
    cmd = " ".join(cmd_parts)
    
    print("\n" + "=" * 80)
    print("  PramaIA Test Suite")
    print("=" * 80)
    print(f"\n📋 Test Suite: {args.suite}")
    print(f"📝 Command: {cmd}\n")
    
    success = run_command(cmd, f"Running {args.suite} tests")
    
    # Report
    print("\n" + "=" * 80)
    if success:
        print("  ✅ Tests completed successfully")
    else:
        print("  ❌ Tests failed")
    print("=" * 80 + "\n")
    
    if args.html:
        print("📊 HTML Report generated: test_report.html")
    if args.coverage:
        print("📊 Coverage report generated: htmlcov/index.html")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
