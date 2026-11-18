# OpenMontage ROADMAP
> 更新：2026-11-18｜維護：指揮:OpenMontage｜類型：維運

## 願景
讓使用者自己就能用影片管線替提案、比賽產出介紹影片，修到的缺陷回饋上游 calesthio/OpenMontage。

## 里程碑

### M1 我方上游 PR 都有結論
- 狀態：進行中
- 交付日：無（上游維護者審查沒有期限）
- 完成條件：
  1. 我方 7 條上游 PR（#538、#539、#540、#541、#912、#913、#963）都已合併或關閉，下列指令印出 `[]` → 驗證：`gh pr list -R calesthio/OpenMontage --state open --limit 200 --json number,headRepositoryOwner -q '[.[]|select(.headRepositoryOwner.login=="bbudaedu")|.number]'`
  2. 仍 OPEN 的 PR 都可以合併，沒有衝突 → 驗證：verify §7
- L3：開新 PR、修改 PR 內文都是對外發文，要使用者核准
- 追蹤：無
- 證據：

### OPS 維運
- 狀態：常駐
- 完成條件：
  1. 本機測試、工具登錄、Remotion 型別檢查與出圖、ffmpeg 全部綠燈 → 驗證：verify §1–§5
  2. 上游巡檢 cron 每天 10:10 有寫 log，沒有中斷超過 2 天 → 驗證：`tail -3 ~/.claude/state/openmontage-watch/watch.log`

## 不做的事
- 不用付費的 image-to-video（Veo 一顆 $3.20，使用者已否決）；要讓畫面動起來，用 Remotion 的鏡頭運動。
- 不把 `feat/local-video-generation` 的本地改動整包送上游；一個 PR 只修一個缺陷，而且要附回歸測試。
- 不主動合併上游 PR，也不替其他專案開新影片製作，除非有派工。

## 分項評估
| 面向 | 自評 | 依據（測試、量測或「未量測」） |
|---|---|---|
| 本機測試 | 4/5 | `pytest tests/` 結果是 1855 passed、0 failed（2026-11-18，`feat/local-video-generation` dce0cc3） |
| Remotion 出圖 | 3/5 | tsc 0 錯、13 個 composition、單幀 still 出圖成功；整片 render 時間：未量測 |
| 與上游同步 | 2/5 | 本機 `main` 和 fork `main` 都落後 origin/main 404 個 commit；`feat/local-video-generation` 落後 276、領先 12 |
| 上游 PR 進度 | 2/5 | 7 條 OPEN，其中 #539、#541 從 8/23 起沒有 review |
| 本地影片生成（WAN） | 1/5 | 15 GB RAM 時被 OOM 砍掉；調到 32 GB 之後：未量測 |

## 缺口清單
1. fork `main` 落後上游 404 個 commit，fork PR #1（verify.md）等人工合併。
2. `resolveTheme()` 丟棄 themeConfig，被 playbook 缺 `surface` 色擋住，暫時不能修。
3. `subtitle_gen` 的 `max_chars_per_line` 把全形字算成 1 欄，CJK 行寬會變成兩倍（PR #538 內文已標 deferred）。
4. `pipeline_defs/cinematic.yaml` 的 research 階段列了 registry 裡沒有的 `web_search`，性質待確認。
5. 約 40 個工具的 asset cache key 漏了欄位（上游走逐工具補 key）；`hyperframes_compose` 也漏。
6. 鶴伴影片已知兩處瑕疵沒修：s3 語速 237 字/分；片尾字幕與片尾卡輕微重疊。

## 點子（未排程、沒有ID）
- 32 GB RAM 之後重測 WAN 2.1 1.3B 文生影片；圖生影片要 14B，需要 48 GB RAM。
