# 客服總機

此專案使用 Chainlit 建構，並以 Python 3.11 與 Poetry 為開發環境。以下文件說明如何建立執行環境、安裝依賴以及啟動應用程式。

## 需求 (Requirements)

- **Python 3.11**  
  請確認已安裝 Python 3.11，可於終端機中輸入 `python --version` 檢查版本。

- **Poetry**  
  使用 Poetry 管理相依套件與虛擬環境。  

## 安裝 (Installation)

1. **安裝 Poetry**  
   若尚未安裝 Poetry，可透過 pip 安裝：

   ```bash
   pip install poetry
   ```

2. **建立專案環境**  
   進入專案目錄，然後安裝專案依賴與建立虛擬環境：

   ```bash
   cd /poc_cs
   poetry install
   ```

3. **啟用虛擬環境**  

   ```bash
   poetry shell
   ```

## 執行專案 (Running the Application)

在完成環境設定後，即可使用以下命令啟動 Chainlit 應用程式：

```bash
chainlit run app.py --host=127.0.0.1 --port=5000 --headless
```

執行後，你可以在瀏覽器中透過 `http://127.0.0.1:5000` 連線至你的應用程式。

## 額外說明 (Additional Information)

- **Headless 模式**  
  使用 `--headless` 參數可在無頭環境下執行，若需要介面互動，可移除此參數。
  
- **其他命令**  
  如需其他指令或設置方式，請參閱 [Chainlit 官方文件](https://docs.chainlit.io)。

## 版權與許可 (License)

請依照實際狀況補充或使用專案所採用的開源許可條款，例如 MIT License 或 Apache License。

---

這份說明文件內容包含了需求、安裝步驟、執行方法及其他補充資訊，供使用者依循進行專案環境建置與執行。
