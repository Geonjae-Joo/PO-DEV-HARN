#!/usr/bin/env python3
"""
MOVED: 이 스크립트는 이동되었습니다.

새 위치: skills/gate-a-check/scripts/gate-a-check.py

gate-a-check 스킬이 직접 호출하는 스크립트이므로 해당 스킬 폴더로 이동.
"""
import sys, os
new_path = os.path.join(os.path.dirname(__file__), "../skills/gate-a-check/scripts/gate-a-check.py")
exec(open(new_path).read())
