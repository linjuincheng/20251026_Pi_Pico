# Streamlit MQTT 監控應用程式

根據 PRD.md 實現的完整 MQTT 監控系統。

## 功能特點

- ✅ MQTT 訂閱功能（訂閱溫度、濕度、電燈狀態）
- ✅ 即時數據顯示（電燈狀態、溫度、濕度）
- ✅ 歷史趨勢圖表（溫度和濕度）
- ✅ 數據表格顯示
- ✅ 自動保存到 Excel 文件
- ✅ 數據下載功能

## 安裝依賴

```bash
cd /home/pi/Documents/GitHub/20251026_Pi_Pico
uv pip install streamlit pandas openpyxl paho-mqtt
```

或使用 pyproject.toml：

```bash
uv pip install -e .
```

## 運行應用

```bash
cd /home/pi/Documents/GitHub/20251026_Pi_Pico/lesson6
streamlit run app.py
```

應用將在瀏覽器中自動打開，通常是 `http://localhost:8501`

## 使用說明

1. **啟動 MQTT Broker**
   - 確保 Mosquitto 或其他 MQTT Broker 正在運行
   - 預設連接到 `localhost:1883`

2. **連接 MQTT**
   - 點擊「連接 MQTT」按鈕
   - 應用將自動訂閱以下主題：
     - `客廳/溫度` - 溫度數據
     - `客廳/濕度` - 濕度數據
     - `客廳/電燈` - 電燈開關狀態

3. **發送測試數據**
   - 可以使用 `lesson6_1.ipynb` 發送測試訊息
   - 或使用其他 MQTT 發布工具

4. **查看數據**
   - 即時顯示當前溫度和濕度
   - 圖表顯示歷史趨勢
   - 數據表格顯示最近接收的訊息

5. **數據儲存**
   - 所有接收到的數據自動保存到 `data/mqtt_data.xlsx`
   - 可以點擊「下載 Excel 文件」按鈕下載

## 文件結構

```
lesson6/
├── app.py              # 主應用程式
├── config.py           # 配置文件
├── PRD.md              # 產品需求文件
├── README.md           # 本文件
├── data/               # 數據目錄（自動創建）
│   └── mqtt_data.xlsx  # Excel 數據文件
├── lesson6_1.ipynb     # MQTT 發布測試
└── lesson6_2.ipynb     # MQTT 訂閱測試
```

## 配置

可以在 `config.py` 中修改：
- MQTT Broker 地址和端口
- 訂閱的主題名稱
- 歷史記錄數量限制

## 注意事項

- 確保 MQTT Broker 正在運行
- 數據會自動保存到 Excel 文件
- 應用會每 2 秒自動刷新以顯示最新數據

