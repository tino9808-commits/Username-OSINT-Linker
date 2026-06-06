# Contributing

Thanks for considering a contribution.

This project is for public-source OSINT education and investigative lead
triage. Contributions should keep the tool evidence-first and cautious.

## Good Contributions

- Improve public profile metadata extraction.
- Add more transparent similarity features.
- Improve reports and documentation.
- Add tests or sample fixtures.
- Improve Windows setup instructions.

## Not Accepted

- Credential collection.
- Phishing pages.
- Login bypasses.
- Exploit modules.
- Claims that a person is definitively identified from username alone.

## Development

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe .\account_linker.py .\examples\report_demo.csv --no-fetch
```

