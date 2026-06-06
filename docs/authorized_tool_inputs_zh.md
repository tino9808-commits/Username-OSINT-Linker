# 授權外部工具匯入筆記

這份筆記整理課堂常見工具如何接到 Username OSINT Linker。核心原則是：
工具本身不主動對任意網站掃描，而是分析已合法取得、已授權取得，或公開被動查詢得到的結果。

## 專案定位

Username OSINT Linker 的重點不是取代 WPScan、dirmap、DNSDumpster，也不是做成攻擊工具。
它的定位是把外部工具產生的線索轉成可讀、可追查、可解釋的 OSINT 報告。

可接受的資料來源包含：

- 自有網站或單位授權測試站。
- 課堂、CTF、靶場或老師指定演練環境。
- 已完成授權掃描後匯出的結果檔。
- DNSDumpster 這類公開被動查詢得到的網域與子網域資料。
- 公開判決書、公開新聞、公開社群頁面等合法公開資料。

不建議公開專案內建的功能：

- 對任意網站自動目錄爆破。
- 對任意 WordPress 站台主動掃描弱點。
- 嘗試登入、破解密碼、繞過驗證或取得非公開資料。
- 把同一個 username 直接判定為同一個真人。

## 可以延伸的流程

```text
授權工具結果
  ↓
抽取 username / email / domain / subdomain / contact / crypto address
  ↓
Maigret 查公開帳號足跡
  ↓
Username OSINT Linker 分析是否可能同一人或同一組織
  ↓
AI 輔助產出證據型 OSINT 報告
```

## WPScan 的 OSINT 用法

WPScan 常用於 WordPress 網站安全檢查。若在授權環境中取得結果，可能出現：

- WordPress 使用者名稱。
- 外掛名稱與版本。
- 佈景主題名稱與版本。
- 站台標題、技術指紋、公開作者頁。

這些資訊可以轉成 OSINT 線索，例如：

| 發現項目 | 可轉成的 OSINT 線索 |
|---|---|
| author slug | username |
| plugin/theme name | 技術棧與營運習慣 |
| contact page | email、姓名、社群帳號 |
| site title | 組織名稱或品牌名稱 |

報告語氣應該保持保守：

```text
在授權 WordPress 檢查結果中發現 username: example_user。
此 username 可作為公開帳號足跡查詢的初始線索，但不能單獨證明身分。
```

## dirmap / 目錄發現結果的 OSINT 用法

目錄發現工具在授權情境下可能找到：

- `/admin/`
- `/backup/`
- `/uploads/`
- `/old/`
- `/test/`
- `/api/`
- `/robots.txt`
- `/sitemap.xml`

對 OSINT 來說，重點不是「破站」，而是辨識公開暴露的線索。例如：

| 路徑類型 | 可能線索 |
|---|---|
| `/backup/` | 檔名、日期、舊系統名稱 |
| `/uploads/` | 上傳者名稱、圖檔 metadata、檔名規則 |
| `/old/` | 舊版品牌、舊網域、舊聯絡資訊 |
| `/api/` | 服務名稱、公開端點、技術架構 |
| `/robots.txt` | 站方不希望被索引的公開路徑 |
| `/sitemap.xml` | 網站結構與公開頁面 |

建議工具只做「結果匯入」：

```text
url,status,title,note
https://example.test/robots.txt,200,robots.txt,public file
https://example.test/old/,200,Old site,legacy path
https://example.test/uploads/,403,Forbidden,interesting exposed directory
```

接著從結果中抽取 username、email、domain、subdomain、Telegram ID、LINE ID、錢包地址等線索。

## DNSDumpster 的 OSINT 用法

DNSDumpster 屬於被動式網域情報查詢，適合做初期 OSINT。常見可取得：

- 子網域。
- DNS 紀錄。
- MX 郵件主機。
- NS 名稱伺服器。
- 可能的雲端服務商或 CDN。

這類資料可用於建立基礎情資圖：

```text
domain
  ↓
subdomains
  ↓
hosting / mail / CDN / service provider
  ↓
possible organization infrastructure
```

注意：如果 IP 指向 Cloudflare、Akamai、AWS、Google Cloud、Azure 等服務商，通常只能代表基礎設施，不代表真實機房、真實營運者地址或犯罪者位置。

## 建議新增功能

未來可以把專案延伸成三個匯入器：

| 匯入器 | 功能 |
|---|---|
| `import_wpscan.py` | 讀取 WPScan JSON/TXT，抽取 username、外掛、主題、站台資訊 |
| `import_dirmap.py` | 讀取 dirmap/dirsearch/ffuf 結果，標記敏感公開路徑與可疑檔名 |
| `import_dnsdumpster.py` | 讀取 DNSDumpster 匯出或手動整理結果，建立 domain/subdomain 線索 |

匯入後可以產出統一格式：

```csv
source,type,value,context,confidence,note
wpscan,username,example_user,author slug,medium,authorized scan result
dirmap,path,/old/,legacy public path,low,needs manual review
dnsdumpster,subdomain,mail.example.test,MX-related host,medium,passive DNS result
```

這樣後續就可以把 `type=username` 的項目交給 Maigret，把 `type=domain` 或 `type=subdomain` 的項目交給網域情資分析，把 `type=crypto_address` 的項目交給金流分析。

## 報告措辭範例

建議用證據型文字：

```text
本報告僅整理公開或授權來源取得的線索。相同 username、相似站台資訊或相同基礎設施，
只能作為偵查方向或待驗證關聯，不能單獨作為身分認定。
```

不建議用絕對判斷：

```text
此帳號就是同一人。
此 IP 就是犯罪者真實位置。
此網站一定有漏洞。
```

## Fork 開源專案管理建議

如果課堂上要求使用 fork 開源專案，可以用這個方式說明：

1. Fork Maigret 或其他 OSINT 工具作為參考來源。
2. 不直接修改原工具核心掃描邏輯。
3. 自己的專案負責結果整理、匯入、關聯分析與報告生成。
4. 用 README 說明原工具來源、授權、用途與限制。
5. 把自己新增的程式、範例資料、文件與報告格式放在公開 repo。

這種做法比較適合公開維護，也比較容易通過開源專案審查。
