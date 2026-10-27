# Windows 10/11 實驗快速開始（先讀）

適用 Kurose 第 2 章：HTTP Packet Analysis + TCP Socket Debugging。**不必安裝 Ubuntu VM、WSL、Docker 或架設校園伺服器**。所有 Client/Server 流量都在學生自己的 Windows 電腦，透過 `127.0.0.1:8080` 傳輸。

## 0. 安裝一次即可（課前完成）
1. 安裝 **Python 3.10 或更新版本**（建議由 https://www.python.org/downloads/windows/ 取得）；PowerShell 下執行 `py -3 --version`。若無 `py` 指令，可測試 `python --version`，但需確認實際版本與執行路徑。
2. 安裝 **Wireshark（Windows 版）**：https://www.wireshark.org/download.html ，安裝時確認有安裝 **Npcap**，並讓 Wireshark 能夠擷取 Loopback Traffic。注意新版 Npcap 的介面通常顯示為 `Adapter for loopback traffic capture`，不一定叫 `Npcap Loopback Adapter`。
3. Windows 10/11 通常內建 `curl.exe`；在 PowerShell 執行 `curl.exe --version`。**請勿直接用 `curl`**（PowerShell 5.1 可能將它解釋為 `Invoke-WebRequest`）。
4. 解壓縮 ZIP 到一般英文路徑（如 `C:\NetLab\Ch2`），避免直接在 ZIP 預覽介面中執行 `.cmd`。Python 程式可處理中文路徑，但英文路徑較方便除錯。
5. **不須停用 Windows Defender 或防火牆**，HTTP Server 僅繫結 `127.0.0.1`；若被企業／學校權限政策限制擷取，請向老師申請替代環境，不自行關閉安全防護。

## 1. 啟動操作（PowerShell；建議使用）
解壓後，在 `student` 所在目錄（包含 `starter_server.py` 的資料夾）開啟 PowerShell：可以在檔案總管的位址列輸入 `powershell` 後按 Enter。

先做環境檢查：

```powershell
py -3 windows_preflight.py --port 8080
```

如果 `py -3` 不存在，以下命令統一改用 `python`。

產生自己的個人測試資料（請將 `S12345678` 改成學號）：

```powershell
py -3 generate_cases.py --student-id S12345678 --out my_case.json
```

**PowerShell A**：啟動有 Bug 的伺服器（保持視窗開啟）：

```powershell
py -3 starter_server.py --student-id S12345678 --port 8080
```

**PowerShell B**：執行 Client、再執行公開測試：

```powershell
curl.exe --http1.1 --noproxy "*" -i -v "http://127.0.0.1:8080/lab/S12345678-dae6fbfe/hello"
py -3 public_tests.py --student-id S12345678 --port 8080 --log public_test_before.txt
```

注意：`dae6fbfe` 只是示範學號 `S12345678` 的 Token，**你的真實 URL 應從 `my_case.json` 的 `hello_path` 複製**。先保存修改前的 Before 結果，再修正程式，重新啟動 Server，執行：

```powershell
py -3 public_tests.py --student-id S12345678 --port 8080 --log public_test_after.txt
```

`--log` 直接由 Python 產生 UTF-8 文字檔，避免 Windows PowerShell 5.1 使用 `>` 轉存時發生 UTF-16 編碼差異。首次測試未達 8/8 **是刻意安排、屬正常情況**。

## 2. 如果不熟悉命令列，也可以使用 .cmd
已提供 4 個 Windows `.cmd` 啟動檔，可在解壓縮後執行並輸入學號：
- `Windows_00_Check.cmd`：環境檢查
- `Windows_01_Generate.cmd`：產生個人測試資料
- `Windows_02_Start_Server.cmd`：啟動 HTTP Server，執行期間不能關閉該視窗
- `Windows_03_Public_Tests.cmd`：另開視窗執行，選擇 `before` 或 `after`，輸出測試紀錄

若 Windows 顯示執行檔警告，請確認 ZIP 來源為教師授課平台、內容為提供的純文字腳本；不必為了本實驗更改 PowerShell Execution Policy。

## 3. Wireshark 擷取 Windows Loopback 封包（重要）
1. **直接在 Windows 主機執行** Wireshark，而非另一台電腦或不同的 VM。
2. 在首頁的 Capture Interface 選 `Adapter for loopback traffic capture`（Npcap；實際名稱依版本而異）。**不可選一般 Wi-Fi 介面期待看到 127.0.0.1**。
3. 如欲設定 Capture Filter（擷取前）：`tcp port 8080`；按鯊魚鰭 Start Capture。
4. 回到 PowerShell B，執行上面的 `curl.exe ... /hello`，再執行 `/unicode`、`/redirect`、`/not-found`。
5. Wireshark **Display Filter**（擷取後）輸入 `tcp.port == 8080`。可選任一 TCP 封包，右鍵 `Follow > TCP Stream`，檢查 HTTP Request/Response。若 HTTP 未被自動辨識，使用 `Analyze > Decode As ...` 將 TCP port 8080 指定為 HTTP。
6. 先 Stop Capture，再 `File > Save As...` 儲存 `http_lab_before.pcapng`。修正後重新擷取可另存 `http_lab_after.pcapng`。**作業報告務必保存原始擷取檔，不能只交截圖**。

### 建議完成的 HTTP 操作（全部以 `curl.exe`）
請根據你的 `my_case.json` 自己組 URL（此處以下使用示範 Token）：

```powershell
curl.exe --http1.1 --noproxy "*" -i -v "http://127.0.0.1:8080/lab/S12345678-dae6fbfe/hello"
curl.exe --http1.1 --noproxy "*" -i -v "http://127.0.0.1:8080/lab/S12345678-dae6fbfe/unicode"
curl.exe --http1.1 --noproxy "*" -i -v "http://127.0.0.1:8080/lab/S12345678-dae6fbfe/redirect"
curl.exe --http1.1 --noproxy "*" -i -v -L "http://127.0.0.1:8080/lab/S12345678-dae6fbfe/redirect"
curl.exe --http1.1 --noproxy "*" -i -v "http://127.0.0.1:8080/lab/S12345678-dae6fbfe/not-found"
```

觀測重點：302 使用 `-L` 跟隨重新導向後可能會多一筆 GET；`unicode` Response 的正確 `Content-Length` 應為 UTF-8 **byte** 數，而不是中文字元數。

## 4. Windows 常見問題
| 症狀 | 排除方式 |
|---|---|
| `py` not recognized | 改用 `python`；檢查 Python 3.10+ 是否安裝以及 PATH／Python Launcher 設定。|
| `python` 啟動 Microsoft Store | 使用 Python.org 安裝的 Python Launcher `py -3`；檢查 Windows App execution aliases 設定。|
| `curl` 執行結果很奇怪 | 請改用 `curl.exe`。|
| `Connection refused` | 先檢查 Server 視窗是否仍在執行、Port 是否一致。|
| `Address already in use` / WinError 10048 | 關閉舊 Server，或 Client、Server、測試均改同一個未使用 Port。|
| Wireshark 找不到 Loopback | 確認安裝 Npcap；選 `Adapter for loopback traffic capture`（或新版相對應介面）；必要時重新安裝／依校方權限請求協助。|
| Wireshark 沒看到 HTTP | 先用 `tcp.port == 8080`，再 `Follow TCP Stream`，必要時 `Decode As HTTP`。|
| 中文顯示亂碼 | 使用 UTF-8 編碼打開 `my_case.json`；改在 Wireshark 或 VS Code 檢查 bytes；測試程式以 UTF-8 解碼。|
| `public_tests.py` 執行後出現 FAIL | Buggy Server 預期會失敗；先紀錄 Before、修正後再測。|
| 測試看似卡住 | 觀察 Server 視窗；一個請求未完成可能等待 socket timeout，若遇到 port 衝突先停止並重啟。|

## 5. 繳交內容
- 修改後的 `fixed_server.py` 或 `starter_server.py`（**必須保留** `--student-id` 與 `--port` 介面）
- `my_case.json`
- `http_lab_before.pcapng`、`http_lab_after.pcapng`（如果分兩次擷取；請勿偽造）
- `public_test_before.txt`、`public_test_after.txt`（使用 `--log` 產生）
- `report.pdf`（至多 4 頁，封包附錄不計）

**重點：不需要在家安裝 WSL/VirtualBox；但 Npcap 可能需要安裝權限。若沒有管理員權限或無法擷取，請事先通知教師安排補救方式。**
