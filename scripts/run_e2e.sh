#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
pip install -e ".[test]" -q
echo "Running Night Fall E2E integration tests..."
pytest tests/test_e2e_integration.py -v
