Part A:

    Q1: 指出一組 request/response 的 stream、Request Line、Status Line、Host、Content-Length，以及 TCP 四元組。
    A: 以 http_lab_before.pcapng 中 hello 的請求與回應為例：
        Stream：tcp.stream == 0，Request 為第 4 個封包，Response 為第 6 個封包。
        Request Line：GET /lab/S412242266-fac0106b/hello HTTP/1.1
        Status Line：HTTP/1.1 200 OK
        Host：127.0.0.1:8080
        Content-Length：34，表示回應 body 共 34 bytes，包含最後的換行，不包含 HTTP 標頭。
        TCP 四元組（來源 IP、來源 Port、目的 IP、目的 Port）：
        Request：(127.0.0.1, 62691, 127.0.0.1, 8080)
        Response：(127.0.0.1, 8080, 127.0.0.1, 62691)

    Q2: 說明 200、302、404 的差異；對 302 解釋為何 curl -L 的封包可能多一組 Request。
    A:  200 OK 表示請求成功。
        302 Found 表示資源暫時位於另一個網址，透過 Location 標頭提供重新導向的目的地。
        404 Not Found 表示伺服器找不到請求的資源。
        curl 加上 -L 後會跟隨 Location，因此先請求 redirect，收到 302 後，再發出一筆 GET 請求到 hello。

    Q3: 比較 unicode 回應的字元數、UTF-8 bytes 與宣告的 Content-Length；若數字不同，解釋。
    A:  unicode 的完整 body 為「網路實驗：S412242266｜測試成功\n」，包含最後的換行共有 21 個字元，編碼成 UTF-8 後則是 41 bytes。
        本例共有 10 個中文字元與全形符號，各占 3 bytes；學號的 10 個 ASCII 字元與換行各占 1 byte，因此共 10 × 3 + 10 + 1 = 41 bytes。
        修改前宣告 Content-Length: 21，但實際送出 41 bytes，原因是使用 len(body_text) 計算字元數。
        修改後先執行 body_bytes = body_text.encode("utf-8")，再使用 len(body_bytes)，因此宣告的 Content-Length: 41 與實際資料一致。
        command_log.txt 中，修改前 curl 出現 excess = 20 且內容顯示不完整；修改後可完整顯示中文 body。

    Q4: 選一筆實驗，記錄修改前與修改後的封包證據（可用兩個獨立擷取檔）。
    A:  以下為 unicode 的完整 Request／Response stream，從封包檔擷取並以 UTF-8 顯示。

        修改前：http_lab_before.pcapng，tcp.stream == 1。
        TCP 端點：127.0.0.1:58775 ↔ 127.0.0.1:8080。

        GET /lab/S412242266-fac0106b/unicode HTTP/1.1
        Host: 127.0.0.1:8080
        User-Agent: curl/8.21.0
        Accept: */*

        HTTP/1.1 200 OK
        Content-Type: text/plain; charset=utf-8
        Content-Length: 21
        Connection: close

        網路實驗：S412242266｜測試成功

        修改後：http_lab_after.pcapng，tcp.stream == 1。
        TCP 端點：127.0.0.1:54034 ↔ 127.0.0.1:8080。

        GET /lab/S412242266-fac0106b/unicode HTTP/1.1
        Host: 127.0.0.1:8080
        User-Agent: curl/8.21.0
        Accept: */*

        HTTP/1.1 200 OK
        Content-Type: text/plain; charset=utf-8
        Content-Length: 41
        Connection: close

        網路實驗：S412242266｜測試成功

        差異：
        1. Content-Length 從 21 改為 41；兩次實際 body 都是 41 bytes，修改後宣告長度與內容相符。
        2. 用戶端 Port 從 58775 改為 54034，代表兩次不同的 TCP 連線；Request、Status Line 與 body 內容相同。

Part B:

    Q1: 為何 recv(1024) 無法代表「讀完 HTTP header」？應以何種條件繼續讀取？
    A:  TCP 提供的是位元組串流，沒有 HTTP 訊息邊界；recv(1024) 只表示這次最多接收 1024 bytes，可能只取得部分標頭，也可能取得標頭與部分 body。
        應反覆 recv() 並累積資料，直到緩衝區包含 b"\r\n\r\n"，才表示完整標頭已收到，再進行解析。
        若 recv() 回傳 b""，代表對方已結束傳送；若逾時或標頭超過作業規定的 8192 bytes，也應結束處理，避免無限等待。

    Q2: 為何 len(text) 不適合作為含中文 Response 的 Content-Length？
    A:  len(text) 計算 Python 字串的 Unicode 字元數，Content-Length 則必須是實際回應 body 的位元組數，兩者在 UTF-8 下可能不同。
        例如「測試」共有 2 個字元，UTF-8 編碼後卻占 6 bytes。因此應先執行 body_bytes = text.encode("utf-8")，再以 len(body_bytes) 填入 Content-Length，並傳送同一份 body_bytes。

    Q3: 302 回應若沒有 Location，Client 會遇到什麼問題？
    A:  Client 雖然知道這是一個重新導向回應，卻無法從標頭得知新的目的地，因此無法依照這個回應自動發出後續請求。
        本實驗修改前只回傳 302 Found 與 Redirect body，沒有提供 hello 的網址；修改後加入 Location: /lab/S412242266-fac0106b/hello，curl -L 才能依此前往 hello。

    Q4: send() 與 sendall() 有何差異？
    A:  send(data) 回傳這次實際送出的 byte 數，一次呼叫可能只送出部分資料，因此程式必須檢查回傳值，並繼續傳送剩餘部分。
        sendall(data) 會持續傳送直到全部資料送出或發生錯誤，成功時回傳 None，失敗時拋出例外。本實驗使用 conn.sendall(response)，避免 HTTP 回應只送出一部分。

    Q5: 為什麼要區分 POST 與 GET、檢查 Host？
    A:  GET 用於取得資源，POST 用於提交資料並要求伺服器處理，兩者代表不同的操作。伺服器應依照支援的方法處理請求。
        本實驗只支援 GET，因此 POST 等其他方法應回傳 405 Method Not Allowed，並附上 Allow: GET；若只檢查路徑，就可能把 POST 錯誤地當作 GET 回傳 200。
        Host 指出要存取的主機及可選的連接埠，讓同一個 IP 上的伺服器能區分不同網站，例如本實驗的 Host: 127.0.0.1:8080。
        作業要求 HTTP/1.1 必須提供唯一、非空的 Host；缺少、空白或重複時回傳 400 Bad Request，解析標頭名稱時則不區分大小寫。
