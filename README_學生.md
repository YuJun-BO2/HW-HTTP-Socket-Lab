# 第 2 章整合實驗：HTTP Packet Analysis × TCP Socket Debugging

**適用：** 大三計算機網路實驗；Kurose & Ross, *Computer Networking: A Top-Down Approach*, Chapter 2  
**工作量：** 兩次每次 2 小時實驗課 + 課後 2–3 小時；**個人作業**。  
**環境：** **以 Windows 10/11 為預設**：Python 3.10+、`curl.exe`、Wireshark + Npcap；Python 程式僅使用標準函式庫。若為 macOS/Linux 亦可執行，但請參考各系統的介面與命令。

> **Windows 同學：請先閱讀 `README_Windows_先讀.md`。** 它包含 PowerShell 完整命令、.cmd 快捷操作、Npcap Loopback 擷取及錯誤排除。下文重點在協定規格與評分。

## 學習目標
1. 辨識 HTTP/1.1 Request line、Status line、Headers 與 Body。
2. 使用 Wireshark 將實際 HTTP request/response 對應到 TCP 連線。
3. 說明 TCP 是 byte stream，`recv(n)` 不保證讀到一則完整 HTTP 訊息。
4. 正確計算 `Content-Length` 的 UTF-8 **位元組數**、處理 `Location`、`Host`、`405`。
5. 在未知的有效測試輸入下，能預測、驗證與解釋回應。

## 個人化設定（Windows PowerShell）
請用自己的學號（英數字、底線、連字號；長度 3–24）取代 `S12345678`，在兩個 PowerShell 視窗中操作。

```powershell
py -3 generate_cases.py --student-id S12345678 --out my_case.json
py -3 starter_server.py --student-id S12345678 --port 8080
```

在另一個 PowerShell 視窗執行（實際 URL 需依 `my_case.json` 的 `hello_path`）：

```powershell
curl.exe --http1.1 --noproxy "*" -i -v "http://127.0.0.1:8080/lab/S12345678-dae6fbfe/hello"
py -3 public_tests.py --student-id S12345678 --port 8080 --log public_test_before.txt
```

**第一次的 public tests 出現失敗是正常的**，因為 `starter_server.py` 刻意含缺陷。先儲存 Before，修改後重新啟動 Server，再執行：

```powershell
py -3 public_tests.py --student-id S12345678 --port 8080 --log public_test_after.txt
```

若 `py -3` 不存在，改用 `python` 並確認是 Python 3.10 以上。`--log` 由 Python 直接產生 UTF-8 文字結果，避免 Windows PowerShell 5.1 轉檔編碼差異。可將修正後檔案命名為 `fixed_server.py`，但執行介面須一致。

## 本實驗 HTTP/1.1 介面（固定規格）
- 僅支援 `GET`，其他 HTTP Method → `405 Method Not Allowed`、`Allow: GET`。
- HTTP/1.1 必須有**非空** `Host` Header（大小寫不敏感）；缺少 → `400 Bad Request`。
- 僅讀取一次完整的 request headers（以 `\r\n\r\n` 為結束），**每個 TCP 連線只處理一個 Request**，回應後關閉；不要求 keep-alive、pipelining、request body、HTTPS。
- 每次回應都必須含 `Content-Type: text/plain; charset=utf-8`、正確的 `Content-Length`（body UTF-8 bytes）、`Connection: close`。
- Header 以 CRLF (`\r\n`) 分行，空行後接 Response Body；`Content-Length` 不包含 HTTP Headers。
- `GET <prefix>/hello` → `200`；body 與 `my_case.json` 的 `hello_body` 完全一致。
- `GET <prefix>/unicode` → `200`；body 與 `unicode_body` 一致。
- `GET <prefix>/redirect` → `302 Found`；`Location: <prefix>/hello`；body 固定 `Redirect\n`。
- `GET <prefix>/echo?msg=<URL encoded text>` → `200`；body `ECHO: <decoded text>\n`。
- 其他路徑 → `404 Not Found`、body `Not Found\n`。
- 錯誤 Method → body `Method Not Allowed\n`；缺 Host/不合法 Request → body `Bad Request\n`。
- 原則上不要在 Request 尚未讀到 `\r\n\r\n` 時送出最終回應；header 上限 8192 bytes（可回 431）。

> 注意：**TCP Segment、一次 `send()` 呼叫、一次 `recv()` 結果不是一對一的關係。** 在測試中拆開傳送 Request，是要檢查應用層是否等候完整 Header，而不是要求 Wireshark 一定顯示固定數量的封包。

## Part A：HTTP 封包分析（25 分）
依序測試 `hello`、`unicode`、`redirect`、`not-found` 四個 URL；另自選一次 `echo?msg=` 使用有中文的訊息。每次都應記錄指令和觀測結果。利用 Wireshark 擷取至少 3 個 HTTP request/response exchange，其中至少包含一次 `unicode`，以及一次 `redirect`。

**Windows Wireshark 操作**：選 `Adapter for loopback traffic capture`（需有 Npcap 支援），開始擷取後才執行 `curl.exe`。擷取前可設定 Capture Filter `tcp port 8080`；擷取後使用 Display Filter `tcp.port == 8080`、Follow → TCP Stream。以 `File > Save As...` 儲存為 `.pcapng`。**請勿在一般 Wi-Fi 介面擷取 127.0.0.1 流量**。若 Wireshark 未將 Port 8080 自動辨識為 HTTP，可使用 Analyze → Decode As → HTTP。完整圖文步驟與疑難排除請見 `README_Windows_先讀.md`。

**不用 HTTPS、VPN、校園網路或 Docker**。Server 和 Client 都在同一台 Windows 電腦執行；如果自行使用 WSL/VM，切記不要在 Windows 主機的錯誤介面上擷取另一個虛擬網路環境的流量。

**Part A 必答：**
1. 指出一組 request/response 的 stream、Request Line、Status Line、Host、Content-Length，以及 TCP 四元組。
2. 說明 `200`、`302`、`404` 的差異；對 `302` 解釋為何 `curl -L` 的封包可能多一組 Request。
3. 比較 `unicode` 回應的字元數、UTF-8 bytes 與宣告的 `Content-Length`；若數字不同，解釋。
4. 選一筆實驗，記錄**修改前**與**修改後**的封包證據（可用兩個獨立擷取檔）。

## Part B：TCP Socket 錯誤診斷（30 分）
修正 `starter_server.py`，保持上述路徑與回應內容不變。必須能通過 public tests，且能合理說明：
- 為何 `recv(1024)` 無法代表「讀完 HTTP header」？應以何種條件繼續讀取？
- 為何 `len(text)` 不適合作為含中文 Response 的 `Content-Length`？
- `302` 回應若沒有 `Location`，Client 會遇到什麼問題？
- `send()` 與 `sendall()` 有何差異？
- 為什麼要區分 `POST` 與 `GET`、檢查 `Host`？

注意：不需要實作完整 RFC HTTP Server，不需要多執行緒或 TLS，請不要改成 Flask/FastAPI 等框架。

## Part C：報告（25 分）
最多 **4 頁（封包截圖附錄不計）**：
- 第 1 頁：實驗環境、命令、個人測試資料、封包證據索引。
- 第 2 頁：HTTP 欄位解釋、UTF-8 byte-length 對照表、302 比較。
- 第 3 頁：錯誤定位表（症狀 → 原因 → 修補方式 → 測試結果）。
- 第 4 頁：自行提出一個變更輸入的預測與實測、反思 AI 使用與驗證過程。

## Part D：現場抽測（20 分）
教師在課堂隨機選題，要求**先口頭預測，再實際操作驗證**；每人約 90 秒。重點在解釋與可重現性，不看是否背熟固定輸出。教師可以要求修正錯誤的推論再測一次。

## AI 工具規則
**允許**查詢概念、說明 HTTP Header、詢問一般除錯方法；**不得**讓 AI 偽造 `.pcap` / `.pcapng`、測試輸出、實驗紀錄、自己的解釋或現場結果。任何用 AI 產生/修改的程式碼片段，須在報告中列出使用方式並能口頭說明。評分不以 AI 偵測器為依據。

## 繳交清單
- `fixed_server.py`（或修正後 `starter_server.py`）
- `my_case.json`
- `http_lab_before.pcapng` 與 `http_lab_after.pcapng`（或等效可開啟的封包檔）
- `public_test_before.txt`, `public_test_after.txt`
- `report.pdf`（建議將下方 `submission_template.md` 製成 PDF）

請用 `py -3 public_tests.py --student-id <你的 ID> --port 8080 --log public_test_after.txt` 驗證；檔名不得含學號以外的個人敏感資料。
