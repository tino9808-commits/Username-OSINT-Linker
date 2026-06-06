# Username OSINT Linker

Username OSINT Linker is a small Windows-friendly classroom project built around
[Maigret](https://github.com/soxoj/maigret). It runs Maigret username searches,
then post-processes the public profile results to estimate whether the discovered
accounts may belong to the same person or organization.

The project is designed for OSINT education, cybercrime investigation training,
and public-source lead triage. It does **not** identify a person with certainty.
It produces evidence, confidence levels, and limitations for human review.

## Features

- Run Maigret from a simple interactive launcher.
- Generate HTML / CSV / TXT Maigret reports.
- Read Maigret CSV reports and analyze claimed profile URLs.
- Fetch public profile metadata when reachable.
- Compare username, page titles, profile descriptions, token overlap, and shared links.
- Produce a Markdown account-linkage report.
- Optionally call an OpenAI-compatible local AI endpoint such as LM Studio for a cautious Chinese summary.

## Why This Matters

In fraud, phishing, gambling-site, fake-exchange, or social engineering cases,
investigators often see repeated identifiers:

- usernames
- customer-service nicknames
- Telegram / LINE IDs
- email prefixes
- social-media handles

Maigret helps find where a username appears. Username OSINT Linker adds a second
layer: it explains whether the discovered public profiles have enough similarity
to be treated as investigative leads.

## Install

```powershell
git clone <your-repo-url>
cd Username-OSINT-Linker
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run Maigret

```powershell
python .\run_maigret.py
```

Enter a public username such as:

```text
therock
```

Reports are written to `reports/`.

## Analyze Account Linkage

After Maigret creates a CSV report:

```powershell
python .\account_linker.py .\reports\report_therock.csv
```

This creates:

```text
reports/report_therock_linkage.md
```

Interactive launcher:

```powershell
python .\run_linker.py
```

## Optional AI Summary

If LM Studio or another OpenAI-compatible local endpoint is running:

```powershell
python .\account_linker.py .\reports\report_therock.csv --ai-endpoint http://localhost:1234/v1 --ai-model local-model
```

The rule-based analysis still runs even when AI is unavailable.

## Output Interpretation

The linkage score is not an identity decision.

| Level | Meaning |
|---|---|
| High | Strong public similarity signals exist, but manual verification is required. |
| Medium | Useful investigative lead; needs corroboration. |
| Low | Weak signals; same username may be coincidental. |
| Very Low | Insufficient public evidence. |

## Legal And Ethical Boundary

This project uses public data only. It does not:

- log in to target accounts
- bypass access controls
- exploit websites
- deanonymize private persons with certainty
- replace lawful investigative records

Use the output as a lead list. Stronger attribution requires corroborating
evidence such as matching biographies, shared outbound links, repeated contact
details, consistent avatars/personas, time patterns, platform records, or other
lawfully obtained data.

## Note On IP Addresses Behind CDN Providers

If a website resolves to Cloudflare, Akamai, AWS, or another hosting/CDN
provider, that IP is usually infrastructure provider space, not necessarily the
site operator's real server or physical location. Treat it as infrastructure
context, not attribution.

