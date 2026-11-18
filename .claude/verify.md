# OpenMontage：怎麼證明做好了

以下每條都在 2026-11-18 於 `feat/local-video-generation`（dce0cc3）實際跑過，結果寫在箭頭後面。都在 repo 根目錄執行，除非另外註明。

1. Python 全套測試（約 2.5 分鐘）：
   `.venv/bin/python -m pytest tests/ -q -p no:cacheprovider` → `1855 passed, 12 skipped, 3 xfailed`，0 failed
   - 改了工具合約，至少要跑 `.venv/bin/python -m pytest tests/contracts -q`，0 failed。
   - 已知與環境相關的例外：`tests/contracts/test_tls_trust.py::test_certifi_excludes_emudhra_incident_roots` 在 `~/OpenMontage-upstream` 的上游 main 上會紅，修改前後都一樣，屬於既有狀態，不算回歸。
   - 不要加 `--timeout`，因為沒裝 pytest-timeout。
2. 工具登錄（preflight）：
   `.venv/bin/python -c "from tools.tool_registry import registry; registry.discover(); print(len(registry.provider_menu()))"` → 印出 `24`（provider 類別數）。這個數字變少，代表有工具載入失敗。
3. Remotion 型別檢查：
   `cd remotion-composer && npx --no-install tsc --noEmit -p .` → 沒有輸出，離開碼 0。用 `--listFilesOnly` 確認，實際檢查 34 個 `src/` 檔案，不是空跑。
4. Remotion 能列出 composition，也能出圖：
   - `cd remotion-composer && npx --no-install remotion compositions src/index.tsx -q | wc -w` → `13`
   - `npx --no-install remotion still src/index.tsx Explainer /tmp/om-smoke.png --frame=0` → `Rendered 1/1`，產出約 1.8 MB 的 PNG。打開看要是有內容的畫面，不能是全黑。
5. ffmpeg：`ffmpeg -version | head -1` → `ffmpeg version 6.1.1…`
6. 影片成品：以 `projects/<id>/renders/final.mp4` 為準，用 `ffprobe -v error -show_entries format=duration:stream=width,height -of csv=p=0 <檔>` 核對長度與解析度跟腳本相符。「render 跑完了」不算數，要附 ffprobe 輸出。實跑範例：`projects/talkybuddy-final-demo/renders/final.mp4` → `1920,1080` 與 `285.566667`。
7. 上游 PR：`gh pr view <n> -R calesthio/OpenMontage --json state,mergeable` → 是 `OPEN MERGEABLE` 或已合併（實跑：#963 → `OPEN MERGEABLE`）。PR 內文必須附「未修版 N 條測試紅，修後全綠」。

## 一定要使用者本人判斷（L3）

- 影片的觀感：節奏、旁白語速、字幕與畫面有沒有重疊、配樂合不合適。這些只能由人看完整支片子後決定。
- 任何會花錢的生成，例如 Veo、ElevenLabs、付費配樂，或付費 API 的 image-to-video。
- 對外上傳或發布：YouTube、送件系統、上游 PR 的新開與內文修改。
- 拍攝本人或現場素材；有兒童或觀眾露臉的畫面，要人看過後才能放行（`face_ok`）。
