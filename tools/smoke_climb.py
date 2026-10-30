#!/usr/bin/env python3
"""Guarded CLIMB V2 lifecycle and natural-ending checks; no physical acceptance claim."""
import sys
from smoke_late_games import main as suite
if __name__=='__main__':raise SystemExit(suite([*sys.argv[1:],"--game","climb"]))
