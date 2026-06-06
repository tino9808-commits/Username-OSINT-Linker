#!/usr/bin/env python3
"""Simple launcher for Maigret classroom demo."""

from __future__ import annotations

import subprocess
import sys
import webbrowser
from pathlib import Path


BASE = Path(__file__).resolve().parent
MAIGRET = BASE / ".venv" / "Scripts" / "maigret.exe"
REPORTS = BASE / "reports"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if not MAIGRET.exists():
        print("找不到 Maigret。請先確認 .venv 已安裝完成。")
        return 1

    print("Maigret Username OSINT")
    print("輸入公開 username，例如 stake、openai、某個嫌疑帳號公開暱稱。")
    username = input("Username > ").strip()
    if not username:
        print("沒有輸入 username。")
        return 2

    top_sites_raw = input("要查前幾個熱門網站？建議 50，直接 Enter 使用 50 > ").strip()
    try:
        top_sites = int(top_sites_raw) if top_sites_raw else 50
    except ValueError:
        top_sites = 50

    REPORTS.mkdir(exist_ok=True)
    cmd = [
        str(MAIGRET),
        username,
        "--top-sites",
        str(top_sites),
        "--timeout",
        "10",
        "--no-recursion",
        "--no-extracting",
        "--folderoutput",
        str(REPORTS),
        "--html",
        "--csv",
        "--txt",
    ]

    cmd.extend(["--no-progressbar", "--no-color"])

    print("\n開始查詢，第一次可能會先更新資料庫。", flush=True)
    print(" ".join(cmd), flush=True)
    print("", flush=True)

    completed = subprocess.run(cmd, cwd=BASE)
    print("\n完成。報告資料夾：")
    print(REPORTS)
    try:
        webbrowser.open(str(REPORTS))
    except Exception:
        pass
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
