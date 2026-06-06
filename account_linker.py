#!/usr/bin/env python3
"""
Account Linker

Post-processes Maigret CSV reports and estimates whether discovered public
profiles likely belong to the same person or organization.

The tool is intentionally evidence-first:
- it reads public Maigret results;
- fetches public profile metadata when reachable;
- calculates transparent rule-based similarity;
- optionally asks an OpenAI-compatible local model, such as LM Studio, to
  summarize the evidence.

It does not log in, bypass access controls, scrape private pages, or identify a
private person as a certainty.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36 AccountLinkerOSINT/1.0"
)
STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "official",
    "profile",
    "instagram",
    "soundcloud",
    "facebook",
    "youtube",
    "twitter",
    "x",
    "github",
    "linkedin",
    "www",
    "com",
    "http",
    "https",
}


@dataclass
class Profile:
    username: str
    platform: str
    url: str
    status: str
    http_status: str
    fetched: bool = False
    fetch_error: str = ""
    final_url: str = ""
    title: str = ""
    description: str = ""
    og_title: str = ""
    og_description: str = ""
    canonical: str = ""
    outbound_links: list[str] | None = None
    tokens: list[str] | None = None


def configure_stdio() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def read_maigret_csv(path: Path) -> list[Profile]:
    profiles: list[Profile] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (row.get("exists") or "").lower() != "claimed":
                continue
            url = (row.get("url_user") or "").strip()
            if not url:
                continue
            profiles.append(
                Profile(
                    username=(row.get("username") or "").strip(),
                    platform=(row.get("name") or "").strip(),
                    url=url,
                    status=(row.get("exists") or "").strip(),
                    http_status=str(row.get("http_status") or "").strip(),
                    outbound_links=[],
                    tokens=[],
                )
            )
    return profiles


def http_get(url: str, timeout: int) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read(350_000)
        content_type = resp.headers.get("content-type", "")
        charset = "utf-8"
        match = re.search(r"charset=([\w.-]+)", content_type, re.I)
        if match:
            charset = match.group(1)
        return {
            "status": resp.status,
            "final_url": resp.geturl(),
            "text": raw.decode(charset, errors="replace"),
        }


def strip_tags(text: str) -> str:
    text = re.sub(r"(?is)<script.*?</script>", " ", text)
    text = re.sub(r"(?is)<style.*?</style>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return html.unescape(re.sub(r"\s+", " ", text)).strip()


def meta_content(page: str, key: str, value: str) -> str:
    pattern = (
        r'<meta[^>]+(?:name|property)=["\']'
        + re.escape(value)
        + r'["\'][^>]+content=["\']([^"\']+)["\']'
    )
    match = re.search(pattern, page, re.I)
    if match:
        return html.unescape(match.group(1)).strip()

    # Reverse attribute order.
    pattern = (
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:name|property)=["\']'
        + re.escape(value)
        + r'["\']'
    )
    match = re.search(pattern, page, re.I)
    return html.unescape(match.group(1)).strip() if match else ""


def extract_links(page: str, base_url: str) -> list[str]:
    links = set()
    for match in re.finditer(r'href=["\']([^"\']+)["\']', page, re.I):
        href = html.unescape(match.group(1)).strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        absolute = urllib.parse.urljoin(base_url, href)
        parsed = urllib.parse.urlparse(absolute)
        if parsed.scheme not in {"http", "https"}:
            continue
        # Keep normalized public URL without query noise.
        normalized = urllib.parse.urlunparse(
            (parsed.scheme, parsed.netloc.lower(), parsed.path.rstrip("/"), "", "", "")
        )
        links.add(normalized)
    return sorted(links)[:40]


def tokenize(*texts: str) -> list[str]:
    combined = " ".join(texts).lower()
    combined = re.sub(r"https?://\S+", " ", combined)
    words = re.findall(r"[\w\u4e00-\u9fff]{2,}", combined)
    clean = []
    for word in words:
        if word in STOPWORDS:
            continue
        if word.isdigit():
            continue
        clean.append(word)
    return sorted(set(clean))[:80]


def fetch_profile(profile: Profile, timeout: int = 12, sleep: float = 0.4) -> Profile:
    try:
        data = http_get(profile.url, timeout)
        profile.fetched = True
        profile.http_status = str(data["status"])
        profile.final_url = data["final_url"]
        page = data["text"]
        title_match = re.search(r"(?is)<title[^>]*>(.*?)</title>", page)
        profile.title = strip_tags(title_match.group(1)) if title_match else ""
        profile.description = meta_content(page, "name", "description")
        profile.og_title = meta_content(page, "property", "og:title")
        profile.og_description = meta_content(page, "property", "og:description")
        canonical_match = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)', page, re.I)
        profile.canonical = html.unescape(canonical_match.group(1)).strip() if canonical_match else ""
        profile.outbound_links = extract_links(page, profile.final_url or profile.url)
        profile.tokens = tokenize(
            profile.username,
            profile.platform,
            profile.title,
            profile.description,
            profile.og_title,
            profile.og_description,
        )
    except (urllib.error.URLError, TimeoutError, OSError, UnicodeError) as exc:
        profile.fetch_error = str(exc)
        profile.tokens = tokenize(profile.username, profile.platform)
        profile.outbound_links = []
    time.sleep(sleep)
    return profile


def jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def score_pair(a: Profile, b: Profile) -> dict[str, Any]:
    evidence = []
    caution = []
    score = 0

    if a.username and a.username.lower() == b.username.lower():
        score += 25
        evidence.append("same username")

    username_token = a.username.lower()
    # Same username is scored separately. Exclude it from content similarity so
    # a repeated handle does not masquerade as independent profile evidence.
    tokens_a = {token for token in (a.tokens or []) if token.lower() != username_token}
    tokens_b = {token for token in (b.tokens or []) if token.lower() != username_token}
    token_overlap = jaccard(tokens_a, tokens_b)
    if token_overlap >= 0.35:
        score += 25
        evidence.append(f"strong text/token overlap ({token_overlap:.2f})")
    elif token_overlap >= 0.18:
        score += 14
        evidence.append(f"moderate text/token overlap ({token_overlap:.2f})")
    elif token_overlap > 0:
        score += 5
        evidence.append(f"weak text/token overlap ({token_overlap:.2f})")

    title_a = " ".join([a.title, a.og_title]).lower()
    title_b = " ".join([b.title, b.og_title]).lower()
    username = a.username.lower()
    if username and username in title_a and username in title_b:
        score += 10
        evidence.append("username appears in both profile titles")

    links_a = set(a.outbound_links or [])
    links_b = set(b.outbound_links or [])
    shared_links = sorted(links_a & links_b)
    if shared_links:
        score += min(25, 10 + len(shared_links) * 5)
        evidence.append("shared outbound links: " + ", ".join(shared_links[:5]))

    if a.fetched and b.fetched:
        score += 5
        evidence.append("both public profile pages were reachable")
    else:
        caution.append("one or both profile pages could not be fetched; confidence is limited")

    if a.platform.lower() == b.platform.lower():
        caution.append("same platform compared; this should usually be ignored")

    score = min(score, 100)
    if score >= 70:
        level = "High"
    elif score >= 45:
        level = "Medium"
    elif score >= 25:
        level = "Low"
    else:
        level = "Very Low"

    return {
        "left": a.platform,
        "right": b.platform,
        "left_url": a.url,
        "right_url": b.url,
        "score": score,
        "level": level,
        "evidence": evidence,
        "caution": caution,
    }


def analyze_profiles(profiles: list[Profile]) -> dict[str, Any]:
    pairs = []
    for i, a in enumerate(profiles):
        for b in profiles[i + 1 :]:
            pairs.append(score_pair(a, b))
    if pairs:
        avg_score = sum(pair["score"] for pair in pairs) / len(pairs)
        max_score = max(pair["score"] for pair in pairs)
    else:
        avg_score = 0
        max_score = 0
    if max_score >= 70:
        conclusion = "High likelihood signals exist, but manual verification is still required."
    elif max_score >= 45:
        conclusion = "Moderate linkage signals exist; treat as investigative leads only."
    elif profiles:
        conclusion = "Limited linkage evidence. Same username alone is not enough for attribution."
    else:
        conclusion = "No claimed profiles were available for analysis."
    return {
        "profile_count": len(profiles),
        "pair_count": len(pairs),
        "average_score": round(avg_score, 1),
        "max_score": max_score,
        "conclusion": conclusion,
        "pairs": pairs,
    }


def ai_summarize(endpoint: str, model: str, report_data: dict[str, Any], timeout: int = 60) -> str:
    prompt = f"""
You are an OSINT analyst. Review the evidence below and write a cautious
Traditional Chinese assessment. Do not claim certainty. Distinguish observed
facts, inference, and limitations. Mention that same username alone is not proof.

Evidence JSON:
{json.dumps(report_data, ensure_ascii=False, indent=2)[:12000]}
"""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You write careful OSINT attribution assessments."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    req = urllib.request.Request(
        endpoint.rstrip("/") + "/chat/completions",
        method="POST",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8", errors="replace"))
    return data["choices"][0]["message"]["content"].strip()


def render_markdown(csv_path: Path, profiles: list[Profile], analysis: dict[str, Any], ai_text: str = "") -> str:
    lines = [
        "# Account Linkage OSINT Report",
        "",
        f"- Source Maigret CSV: `{csv_path}`",
        f"- Generated at: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- Claimed profiles analyzed: {len(profiles)}",
        "",
        "## Scope",
        "",
        "This report uses public Maigret results and public profile metadata. It does not log in, bypass access controls, or make a definitive identity attribution.",
        "",
        "## Profile Metadata",
        "",
        "| Platform | URL | Fetched | Title / OG Title | Description Preview |",
        "|---|---|---:|---|---|",
    ]
    for p in profiles:
        title = p.og_title or p.title or "-"
        desc = p.og_description or p.description or p.fetch_error or "-"
        desc = re.sub(r"\s+", " ", desc)[:160]
        lines.append(
            f"| {p.platform} | {p.url} | {'yes' if p.fetched else 'no'} | {title} | {desc} |"
        )

    lines.extend(
        [
            "",
            "## Pairwise Linkage",
            "",
            "| Pair | Score | Level | Evidence | Caution |",
            "|---|---:|---|---|---|",
        ]
    )
    for pair in analysis["pairs"]:
        evidence = "; ".join(pair["evidence"]) or "-"
        caution = "; ".join(pair["caution"]) or "-"
        lines.append(
            f"| {pair['left']} ↔ {pair['right']} | {pair['score']} | {pair['level']} | {evidence} | {caution} |"
        )

    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Max score: {analysis['max_score']}",
            f"- Average pair score: {analysis['average_score']}",
            f"- Conclusion: {analysis['conclusion']}",
            "",
            "## Analyst Note",
            "",
            "Same username is a lead, not proof. Stronger attribution requires corroborating evidence such as matching biographies, shared outbound links, repeated contact details, consistent avatar/persona, temporal patterns, platform records, or lawful investigative data.",
        ]
    )
    if ai_text:
        lines.extend(["", "## AI-Assisted Assessment", "", ai_text])
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze Maigret username results for possible account linkage.")
    parser.add_argument("csv", type=Path, help="Maigret CSV report, e.g. reports/report_therock.csv")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Output Markdown path")
    parser.add_argument("--json", type=Path, default=None, help="Optional JSON output path")
    parser.add_argument("--timeout", type=int, default=12, help="HTTP timeout per profile")
    parser.add_argument("--no-fetch", action="store_true", help="Analyze Maigret URLs without fetching profile metadata")
    parser.add_argument("--ai-endpoint", default="", help="OpenAI-compatible endpoint, e.g. http://localhost:1234/v1")
    parser.add_argument("--ai-model", default="local-model", help="Model name for OpenAI-compatible endpoint")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    configure_stdio()
    args = parse_args(argv)
    if not args.csv.exists():
        print(f"找不到 CSV：{args.csv}", file=sys.stderr)
        return 2

    profiles = read_maigret_csv(args.csv)
    if not args.no_fetch:
        profiles = [fetch_profile(profile, timeout=args.timeout) for profile in profiles]
    else:
        for profile in profiles:
            profile.tokens = tokenize(profile.username, profile.platform)
            profile.outbound_links = []

    analysis = analyze_profiles(profiles)
    report_data = {
        "source_csv": str(args.csv),
        "profiles": [asdict(profile) for profile in profiles],
        "analysis": analysis,
    }

    ai_text = ""
    if args.ai_endpoint:
        try:
            ai_text = ai_summarize(args.ai_endpoint, args.ai_model, report_data)
        except Exception as exc:  # noqa: BLE001 - report AI failure without hiding rule-based output.
            ai_text = f"AI summary failed: {exc}"

    output = args.output
    if output is None:
        output = args.csv.with_name(args.csv.stem + "_linkage.md")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_markdown(args.csv, profiles, analysis, ai_text), encoding="utf-8-sig")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report_data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"已產生帳號關聯分析報告：{output}")
    print(f"Claimed profiles: {analysis['profile_count']}")
    print(f"Max score: {analysis['max_score']}")
    print(f"Conclusion: {analysis['conclusion']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
