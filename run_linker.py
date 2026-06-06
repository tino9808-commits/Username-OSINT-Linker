#!/usr/bin/env python3
"""Interactive launcher for Account Linker."""

from __future__ import annotations

import sys
import webbrowser
from pathlib import Path

from account_linker import main as linker_main


BASE = Path(__file__).resolve().parent
REPORTS = BASE / "reports"


def configure_stdio() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main() -> int:
    configure_stdio()
    csv_files = sorted(REPORTS.glob("report_*.csv"))
    if not csv_files:
        print("reports 資料夾找不到 Maigret CSV。請先執行 run_maigret.py。")
        return 1

    print("Account Linker - Maigret 後處理分析")
    print("選擇要分析的 Maigret CSV：")
    for idx, path in enumerate(csv_files, start=1):
        print(f"{idx}. {path.name}")
    raw = input("編號 > ").strip()
    try:
        selected = csv_files[int(raw) - 1]
    except (ValueError, IndexError):
        print("編號錯誤。")
        return 2

    use_ai = input("是否呼叫本機 LM Studio/OpenAI-compatible AI？(y/N) > ").strip().lower() == "y"
    args = [str(selected)]
    if use_ai:
        endpoint = input("Endpoint，直接 Enter 使用 http://localhost:1234/v1 > ").strip() or "http://localhost:1234/v1"
        model = input("Model 名稱，直接 Enter 使用 local-model > ").strip() or "local-model"
        args.extend(["--ai-endpoint", endpoint, "--ai-model", model])

    rc = linker_main(args)
    output = selected.with_name(selected.stem + "_linkage.md")
    try:
        webbrowser.open(str(output))
    except Exception:
        pass
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
