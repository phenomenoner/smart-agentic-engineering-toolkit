# Smart Agentic Engineering Toolkit

[English](README.en.md)

一組可獨立觸發、可驗收、可持續改進的軟體工程 skills。它把我們常用的工作方式整理成
清楚的產品，而不是再造一套「所有任務都必須照表操課」的方法論。

建議路徑是：需要時先規格化，再實作、review、用測試或 incident drill 補足證據，直到
主張被支持或遇到明確 stop condition。任務可以直接從診斷、實作、review 或 incident
開始；小改動不必先產生計畫、WAL、worktree、subagent 或完整測試套件。

若規格正在引入實質機制，先明問「Do we really need this to make things happen?」與「Is
there a simpler and more direct way?」，把可觀察 outcome/invariant 與 mechanism proxy 分開，
優先考慮刪除、人工操作、內嵌/即時計算或既有平台 primitive；只有確有需要才增加新狀態。
這是條件式煞車，已清楚的小型 contract 仍可直接實作。

**新finding不自動等於新scope。** 行動前先依已授權deliverable與claim分類為`IN_SCOPE`、
最小`SCOPE_GUARD`、`ADJACENT_RISK`或`OUT_OF_SCOPE`。若處置會提高claim、acceptance level、
release rigor、system boundary、authority、writable surface或external effects，必須停在明示的
scope-change checkpoint。嚴重finding仍應揭露，但severity本身不能修改任務授權。

## 這套工具解決什麼

- 把「先想清楚」落成可觀察行為、non-goals、失敗語意與可證偽 acceptance，而不是只寫
  一份大計畫；實質機制還要先列出複雜度、authority、recovery 與 failure-state 成本。
- 把 implementation、debugging、review、readiness judgment 與 incident regression 分開，
  避免一個 skill 偷渡另一個 skill 的權限或結論。
- 用跨階段anti-scope-drift guard讓finding與驗證深度受已授權claim約束，同時保留owner明示
  scope amendment後的直接路徑。
- 對具有多個可獨立失敗環節、且integration回饋昂貴的composite seam，條件式採用unit-first：
  先證明各link與contract-relevant failure class，再測composition boundary，最後才驗證低層
  無法代表的native或lifecycle行為。
- 對 TOCTOU、ABA、PID/handle reuse、replacement cleanup、rollback ownership 等時序問題，
  要求 forbidden trace、linearization point、stable capability/CAS 與精準 interleaving test。
- 把 WAL 當最小可恢復地圖；Canvas、CodeGraph、AAR、knowledge graph 與模型 worker 都是
  可選增強，不是權威或品質證明。
- 長任務可選用 [canon orchestration profile](workflows/specify-implement-review-drill.md)：
  以無狀態 transition guard 鎖住產品承諾與目標終態，用五個邏輯責任視角、兩個有預算的
  loop 與 shadow specification reopen 協作，並把 core、每個 host seam、per-target release
  與 overall verdict 分開，避免中途里程碑或單一平台 PASS 冒充完成。
- 每個 toolkit-owned skill 都內建 upstream improvement protocol：發現實質缺口時，整理
  public-safe evidence、精確 patch 與判別性 eval；有 GitHub 寫入授權才開 draft PR，否則
  提供 PR-ready packet 並明確詢問是否代為提交。

## 分類

| 類別 | Skills |
| --- | --- |
| Core | `engineering-specification`, `engineering-debugging`, `engineering-implementation`, `engineering-wal`, `batch-complete-independent-review`, `completeness-and-test-synthesis`, `incident-to-regression`, `specify-temporal-ownership`, `evolve-engineering-toolkit` |
| Assurance | `canon-engineering-disciplines` |
| Navigation / composition | `codegraph-first-navigation`, `programmatic-tool-composition` |
| Windows / Codex adapters | `long-run-supervisor`, `codex-cli-luna-worker`, `codex-app-mcp-update` |
| Explicit provider adapter | `claude-independent-review` |

完整 trigger、non-trigger、implicit policy 與 canonical owner 在
[`catalog/skills.json`](catalog/skills.json) 與 [`docs/taxonomy.md`](docs/taxonomy.md)。

## Codex plugin 安裝

本 repo 根目錄就是 plugin source。發布版本會提供 GitHub tag/release 與逐檔 hash lock。
把已通過 gate 的精確 commit checkout（發布後也可使用對應 tag）註冊成 local marketplace、
安裝 plugin、完整重啟 Codex Desktop，並在 **新的 task** 裡做 native behavior 驗證。設定檔、
catalog 可見或 MCP health 不等於 skill/tool 真正可用；完整 plugin 與 standalone profile 指令見
[`docs/installation.md`](docs/installation.md)。

若環境已有同名 loose skills，先保留它們，利用本 toolkit 的新 skill 驗證 plugin 已被新
task 載入，再依 [`docs/migration.md`](docs/migration.md) 做可恢復的逐項切換。不要用 `Force`
覆蓋未知修改。

## 外部整合

`baton-fanout-skill` 在 0.4.0 仍由原 repo 擁有，toolkit 只 pin integration；Context Canvas、
Understand Anything 與 AAR 也維持各自 canonical owner。詳見
[`docs/integrations.md`](docs/integrations.md)。Superpowers 僅是比較資料，不會重新啟用其
mandatory bootstrap/TDD/worktree/fan-out chain。

## 驗證與貢獻

執行：

```powershell
python -m pip install --editable ".[dev]"
python scripts/validate_toolkit.py
python -m pytest -q
```

貢獻前請讀 [`CONTRIBUTING.md`](CONTRIBUTING.md)。尤其不要直接修改 installed skill 或
plugin cache；修正應落在 canonical source，並包含能區分修正前後的 activation、
non-activation 或 workflow eval。

## 狀態與限制

0.4.0 新增條件式unit-first composite-seam ladder、由Baton治理的stable bounded Luna/max worker
資格，以及Codex independent review的Sol/high最低路由。它不新增skill、profile、schema或
mandatory lifecycle，並保留單一簡單seam的直接路徑。本版沿用0.1.0的63-case baseline，只重綁
release identity與current input hashes；supplemental fresh-agent behavior仍以實際保存的host
evidence為界。本版主張只涵蓋已列出的repository bytes、source tests、plugin/standalone
install與host evidence；不表示OpenAI官方推薦、
Plugin Directory 審核通過、AAR/Canvas/外部 provider 已部署或可用。

授權：MIT。外部參考與 provenance 見 [`NOTICE`](NOTICE) 與
[`docs/influences-and-provenance.md`](docs/influences-and-provenance.md)。
