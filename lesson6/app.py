"""
Streamlit MQTT 監控應用程式
根據 PRD.md 實現的完整功能
"""

import streamlit as st
import paho.mqtt.client as mqtt
import json
import pandas as pd
import time
from datetime import datetime
from pathlib import Path
import threading
import config

# 初始化 session_state
if 'mqtt_client' not in st.session_state:
    st.session_state.mqtt_client = None
if 'mqtt_connected' not in st.session_state:
    st.session_state.mqtt_connected = False
if 'data_history' not in st.session_state:
    st.session_state.data_history = []
if 'current_temperature' not in st.session_state:
    st.session_state.current_temperature = None
if 'current_humidity' not in st.session_state:
    st.session_state.current_humidity = None
if 'light_status' not in st.session_state:
    st.session_state.light_status = None
if 'last_update_time' not in st.session_state:
    st.session_state.last_update_time = None

# 確保數據目錄存在
import os
data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
Path(data_dir).mkdir(parents=True, exist_ok=True)


def save_to_excel(data_row):
    """將數據追加到 Excel 文件"""
    try:
        excel_path = Path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "mqtt_data.xlsx"))
        
        # 如果文件不存在，創建新的 DataFrame
        if not excel_path.exists():
            df = pd.DataFrame(columns=config.EXCEL_COLUMNS)
        else:
            # 讀取現有數據
            df = pd.read_excel(excel_path, engine='openpyxl')
        
        # 追加新數據
        new_row = pd.DataFrame([data_row], columns=config.EXCEL_COLUMNS)
        df = pd.concat([df, new_row], ignore_index=True)
        
        # 保存到 Excel
        df.to_excel(excel_path, index=False, engine='openpyxl')
        
    except Exception as e:
        st.error(f"保存 Excel 文件時發生錯誤: {e}")


def parse_mqtt_message(topic, payload):
    """解析 MQTT 訊息"""
    try:
        # 嘗試解析 JSON
        data = json.loads(payload)
        
        # 提取數據
        temperature = data.get('temperature', None)
        humidity = data.get('humidity', None)
        light = data.get('light', None)
        
        # 如果主題中包含關鍵字，也嘗試從主題判斷
        if '溫度' in topic or 'temperature' in topic.lower():
            if temperature is None:
                temperature = float(payload) if payload.replace('.', '').replace('-', '').isdigit() else None
        elif '濕度' in topic or 'humidity' in topic.lower():
            if humidity is None:
                humidity = float(payload) if payload.replace('.', '').replace('-', '').isdigit() else None
        elif '電燈' in topic or 'light' in topic.lower():
            if light is None:
                light = payload.strip().lower() in ['on', '開', 'true', '1']
        
        return {
            'temperature': temperature,
            'humidity': humidity,
            'light': light,
            'raw_data': data if isinstance(data, dict) else payload
        }
    except json.JSONDecodeError:
        # 如果不是 JSON，嘗試直接解析
        value = None
        try:
            value = float(payload)
        except ValueError:
            pass
        
        # 根據主題判斷數據類型
        if '溫度' in topic or 'temperature' in topic.lower():
            return {'temperature': value, 'humidity': None, 'light': None, 'raw_data': payload}
        elif '濕度' in topic or 'humidity' in topic.lower():
            return {'temperature': None, 'humidity': value, 'light': None, 'raw_data': payload}
        elif '電燈' in topic or 'light' in topic.lower():
            light_status = payload.strip().lower() in ['on', '開', 'true', '1', '開燈']
            return {'temperature': None, 'humidity': None, 'light': light_status, 'raw_data': payload}
        
        return {'temperature': None, 'humidity': None, 'light': None, 'raw_data': payload}


def on_connect(client, userdata, flags, reason_code, properties):
    """MQTT 連接回調"""
    if reason_code.is_failure:
        st.session_state.mqtt_connected = False
        st.error(f"❌ MQTT 連接失敗，錯誤代碼: {reason_code}")
    else:
        st.session_state.mqtt_connected = True
        # 訂閱所有主題
        for topic in config.TOPICS.values():
            client.subscribe(topic, qos=1)
        st.success(f"✅ 成功連接到 MQTT Broker: {config.MQTT_BROKER}")


def on_subscribe(client, userdata, mid, reason_codes, properties):
    """MQTT 訂閱回調"""
    pass


def on_message(client, userdata, message):
    """MQTT 訊息接收回調"""
    topic = message.topic
    payload = message.payload.decode('utf-8')
    timestamp = datetime.now()
    
    # 解析訊息
    parsed = parse_mqtt_message(topic, payload)
    
    # 更新當前狀態
    if parsed['temperature'] is not None:
        st.session_state.current_temperature = parsed['temperature']
    if parsed['humidity'] is not None:
        st.session_state.current_humidity = parsed['humidity']
    if parsed['light'] is not None:
        st.session_state.light_status = parsed['light']
    
    st.session_state.last_update_time = timestamp
    
    # 創建數據記錄
    data_record = {
        '時間戳記': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        '主題': topic,
        '溫度': parsed['temperature'] if parsed['temperature'] is not None else '',
        '濕度': parsed['humidity'] if parsed['humidity'] is not None else '',
        '電燈狀態': '開' if parsed['light'] else '關' if parsed['light'] is not None else '',
        '原始訊息': json.dumps(parsed['raw_data']) if isinstance(parsed['raw_data'], dict) else str(parsed['raw_data'])
    }
    
    # 添加到歷史記錄
    history_item = {
        'timestamp': timestamp,
        'temperature': parsed['temperature'],
        'humidity': parsed['humidity'],
        'light': parsed['light']
    }
    st.session_state.data_history.append(history_item)
    
    # 限制歷史記錄數量
    if len(st.session_state.data_history) > config.MAX_HISTORY_RECORDS:
        st.session_state.data_history = st.session_state.data_history[-config.MAX_HISTORY_RECORDS:]
    
    # 保存到 Excel
    save_to_excel(data_record)


def connect_mqtt():
    """連接 MQTT Broker"""
    if st.session_state.mqtt_client is not None:
        disconnect_mqtt()
    
    try:
        client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        client.on_connect = on_connect
        client.on_subscribe = on_subscribe
        client.on_message = on_message
        
        client.connect(config.MQTT_BROKER, config.MQTT_PORT, config.MQTT_KEEPALIVE)
        client.loop_start()
        
        st.session_state.mqtt_client = client
        time.sleep(1)  # 等待連接建立
        return True
    except Exception as e:
        st.error(f"連接 MQTT 時發生錯誤: {e}")
        return False


def disconnect_mqtt():
    """斷開 MQTT 連接"""
    if st.session_state.mqtt_client is not None:
        try:
            st.session_state.mqtt_client.loop_stop()
            st.session_state.mqtt_client.disconnect()
        except:
            pass
        st.session_state.mqtt_client = None
        st.session_state.mqtt_connected = False


# Streamlit UI
st.set_page_config(page_title="MQTT 監控系統", page_icon="📡", layout="wide")

st.title("📡 MQTT 監控系統")
st.markdown("---")

# 連接控制區域
col1, col2, col3 = st.columns([2, 2, 2])

with col1:
    if st.button("🔌 連接 MQTT", disabled=st.session_state.mqtt_connected):
        if connect_mqtt():
            st.rerun()

with col2:
    if st.button("🔌 斷開連接", disabled=not st.session_state.mqtt_connected):
        disconnect_mqtt()
        st.rerun()

with col3:
    connection_status = "🟢 已連接" if st.session_state.mqtt_connected else "🔴 未連接"
    st.markdown(f"**連接狀態**: {connection_status}")

st.markdown("---")

# 主要顯示區域
if st.session_state.mqtt_connected:
    # 電燈狀態顯示
    st.subheader("💡 電燈狀態")
    light_col1, light_col2 = st.columns([1, 3])
    
    with light_col1:
        if st.session_state.light_status is not None:
            light_text = "開" if st.session_state.light_status else "關"
            light_color = "normal" if st.session_state.light_status else "off"
            st.metric("電燈", light_text, delta=None)
        else:
            st.metric("電燈", "未知", delta=None)
    
    with light_col2:
        if st.session_state.light_status is not None:
            status_emoji = "💡" if st.session_state.light_status else "🌙"
            status_text = "電燈已開啟" if st.session_state.light_status else "電燈已關閉"
            st.info(f"{status_emoji} {status_text}")
        else:
            st.info("⏳ 等待數據...")
    
    st.markdown("---")
    
    # 環境數據顯示
    st.subheader("🌡️ 環境數據")
    
    env_col1, env_col2 = st.columns(2)
    
    with env_col1:
        if st.session_state.current_temperature is not None:
            st.metric("溫度", f"{st.session_state.current_temperature}°C", delta=None)
        else:
            st.metric("溫度", "N/A", delta=None)
    
    with env_col2:
        if st.session_state.current_humidity is not None:
            st.metric("濕度", f"{st.session_state.current_humidity}%", delta=None)
        else:
            st.metric("濕度", "N/A", delta=None)
    
    st.markdown("---")
    
    # 圖表顯示
    st.subheader("📊 歷史趨勢圖")
    
    if len(st.session_state.data_history) > 0:
        # 準備圖表數據
        chart_data = []
        for item in st.session_state.data_history:
            chart_data.append({
                '時間': item['timestamp'],
                '溫度': item['temperature'] if item['temperature'] is not None else None,
                '濕度': item['humidity'] if item['humidity'] is not None else None
            })
        
        df_chart = pd.DataFrame(chart_data)
        df_chart = df_chart.set_index('時間')
        
        # 溫度圖表
        if df_chart['溫度'].notna().any():
            st.markdown("**溫度趨勢**")
            st.line_chart(df_chart[['溫度']], use_container_width=True)
        
        # 濕度圖表
        if df_chart['濕度'].notna().any():
            st.markdown("**濕度趨勢**")
            st.line_chart(df_chart[['濕度']], use_container_width=True)
    else:
        st.info("⏳ 等待數據以顯示圖表...")
    
    st.markdown("---")
    
    # 數據表格
    st.subheader("📋 最近接收的數據")
    
    if len(st.session_state.data_history) > 0:
        # 準備表格數據
        table_data = []
        for item in st.session_state.data_history[-20:]:  # 顯示最近 20 條
            table_data.append({
                '時間': item['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                '溫度': f"{item['temperature']}°C" if item['temperature'] is not None else "N/A",
                '濕度': f"{item['humidity']}%" if item['humidity'] is not None else "N/A",
                '電燈': '開' if item['light'] else '關' if item['light'] is not None else 'N/A'
            })
        
        df_table = pd.DataFrame(table_data)
        st.dataframe(df_table, use_container_width=True, hide_index=True)
    else:
        st.info("⏳ 尚未接收到任何數據...")
    
    st.markdown("---")
    
    # 控制按鈕
    control_col1, control_col2 = st.columns(2)
    
    with control_col1:
        if st.button("🗑️ 清除歷史數據"):
            st.session_state.data_history = []
            st.session_state.current_temperature = None
            st.session_state.current_humidity = None
            st.session_state.light_status = None
            st.rerun()
    
    with control_col2:
        excel_path = Path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "mqtt_data.xlsx"))
        if excel_path.exists():
            with open(excel_path, 'rb') as f:
                st.download_button(
                    label="📥 下載 Excel 文件",
                    data=f.read(),
                    file_name=f"mqtt_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.info("尚未有數據可下載")
    
    # 最後更新時間
    if st.session_state.last_update_time:
        st.caption(f"最後更新時間: {st.session_state.last_update_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 自動刷新（每 2 秒）
    time.sleep(2)
    st.rerun()
    
else:
    st.info("👆 請點擊「連接 MQTT」按鈕開始監控")
    st.markdown("""
    ### 使用說明
    
    1. 確保 MQTT Broker 正在運行（localhost:1883）
    2. 點擊「連接 MQTT」按鈕
    3. 應用程式將自動訂閱以下主題：
       - `客廳/溫度` - 溫度數據
       - `客廳/濕度` - 濕度數據
       - `客廳/電燈` - 電燈開關狀態
    4. 接收到的數據會自動保存到 Excel 文件
    5. 圖表會即時顯示歷史趨勢
    """)
