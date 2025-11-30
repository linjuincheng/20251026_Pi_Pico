"""
MQTT Streamlit 應用程式配置文件
"""

# MQTT Broker 設定
MQTT_BROKER = "localhost"  # 或使用 "127.0.0.1"
MQTT_PORT = 1883
MQTT_KEEPALIVE = 60

# MQTT 主題列表
TOPICS = {
    "temperature": "客廳/溫度",
    "humidity": "客廳/濕度",
    "light": "客廳/電燈"
}

# 數據文件路徑（在 app.py 中動態處理）
EXCEL_FILENAME = "mqtt_data.xlsx"

# 數據顯示設定
MAX_HISTORY_RECORDS = 100  # 圖表中顯示的最大歷史記錄數

# Excel 欄位名稱
EXCEL_COLUMNS = ["時間戳記", "主題", "溫度", "濕度", "電燈狀態", "原始訊息"]

