#!/usr/bin/env python3
"""Run every host test under tests/ (no device needed). Exit code 0 only when all pass."""
import sys
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parents[1] / 'tests'

if __name__ == '__main__':
    sys.path.insert(0, str(TESTS))
    suite = unittest.defaultTestLoader.discover(str(TESTS), pattern='test_*.py', top_level_dir=str(TESTS))
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
