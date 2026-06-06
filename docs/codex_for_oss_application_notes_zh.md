# Codex for Open Source 申請備忘

官方申請頁：
https://openai.com/form/codex-for-oss/

官方頁面重點：

- Maintainers of active open-source projects can apply.
- OpenAI 會看 repository usage、ecosystem importance、active maintenance evidence。
- 入選維護者可能獲得 6 months of ChatGPT Pro、API credits，以及條件式 Codex Security access。
- Applications are reviewed on a rolling basis.

## 這個專案可以怎麼描述

專案名稱：

```text
Username OSINT Linker
```

Repository URL：

```text
填你的 GitHub public repo URL
```

Describe your role:

```text
Primary maintainer
```

Why does this repository qualify? 500 字內可參考：

```text
Username OSINT Linker is an educational open-source OSINT tool that extends Maigret results with explainable account-linkage analysis. It helps investigators and students triage public username traces while avoiding overclaiming identity attribution. The project includes Windows-friendly launchers, public-data-only guardrails, sample fixtures, reports, and documentation for responsible cybercrime investigation training.
```

How will you use API credits for your project? 500 字內可參考：

```text
I would use API credits to improve AI-assisted OSINT report summarization, evidence scoring explanations, safer attribution language, automated test generation, and maintainer workflows such as pull request review and documentation updates. The AI layer will remain optional and evidence-first, with clear warnings that same username alone is not proof of identity.
```

## 申請前建議

1. GitHub repo 設為 Public。
2. README 寫清楚用途、安裝、範例、限制。
3. 至少 commit 幾次，不要只有一次丟全部。
4. 加上 LICENSE、CONTRIBUTING、requirements。
5. 不要上傳私人查詢報告、真實個資、課堂簡報或 `.venv`。
6. 開 1 到 2 個 issue，例如：
   - Improve profile metadata extraction
   - Add tests for account linkage scoring
7. 做一個 release 或 tag，例如 `v0.1.0`。

## 注意

這不是保證通過。官方會審核專案是否活躍、是否有維護價值、是否對生態系或實務工作有意義。

