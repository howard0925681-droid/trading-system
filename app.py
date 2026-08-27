import datetime
import urllib.parse
import pandas as pd
import requests
import streamlit as st

# 1. 頁面配置
st.set_page_config(
    page_title="FX & Gold Tracker Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 🔗 請貼上你部署好的 Google Apps Script 網址 🔗
GAS_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbxhPaVglQaEZ-FtASX5Arp13kWgOFB28E2g-_NIfDlX_CykIx3dRtgitDH07JkE1g_uGA/exec"

# 2. CSS 樣式設定
st.markdown(
    """
<style>
    .stApp {
        background-color: #0B0E14 !important;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    header[data-testid="stHeader"] { background: transparent; }
    
    .title-container {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 2px;
    }
    .main-title {
        font-size: 2.6rem;
        font-weight: 900;
        letter-spacing: -0.5px;
        background: linear-gradient(90deg, #00F2FE 0%, #4FACFE 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    div[data-testid="stMarkdownContainer"] p, label[data-testid="stWidgetLabel"] p {
        font-size: 1.15rem !important;
        font-weight: 800 !important;
        color: #E2E8F0 !important;
    }
    
    div[data-baseweb="input"] > div, 
    div[data-baseweb="select"] > div {
        background-color: #151A23 !important;
        border: 1.5px solid #2A3241 !important;
        border-radius: 8px !important;
        min-height: 55px !important;
    }
    
    div[data-baseweb="input"] > div:focus-within, 
    div[data-baseweb="select"] > div:focus-within {
        border-color: #00F2FE !important;
        box-shadow: 0 0 10px rgba(0, 242, 254, 0.3) !important;
    }

    div[data-testid="stNumberInput"] input {
        font-size: 1.25rem !important;
        font-weight: 500 !important;
        color: #FFFFFF !important;
        height: 55px !important;
    }
    
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] div,
    div[data-baseweb="select"] input {
        font-size: 1.75rem !important;
        font-weight: 900 !important;
        color: #FFFFFF !important;
    }

    div[data-testid="stTextInput"] input {
        font-size: 1.15rem !important;
        font-weight: 400 !important;
        color: #FFFFFF !important;
        height: 55px !important;
    }

    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #131822 0%, #171D2A 100%);
        border: 1.5px solid #232D3F;
        padding: 20px 24px;
        border-radius: 14px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.35);
    }
    div[data-testid="stMetricLabel"] {
        color: #94A3B8 !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.8px;
    }
    div[data-testid="stMetricValue"] {
        color: #00F2FE !important;
        font-size: 2.3rem !important;
        font-weight: 900 !important;
    }

    .risk-card {
        background: linear-gradient(135deg, #111622 0%, #172030 100%);
        border: 1.5px solid #222F43;
        border-left: 6px solid #00F2FE;
        border-radius: 12px;
        padding: 22px 28px;
        margin: 22px 0;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
    }
    .risk-grid {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 18px;
        margin-top: 16px;
        width: 100%;
    }
    .risk-item {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        padding: 14px 10px;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }
    .risk-label {
        color: #94A3B8;
        font-size: 1rem;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    .risk-value {
        font-size: 1.65rem;
        font-weight: 900;
    }
    .rr-badge {
        display: inline-block;
        padding: 6px 18px;
        border-radius: 8px;
        font-weight: 800;
        font-size: 1.35rem;
    }
    .rr-good { background: rgba(16, 185, 129, 0.2); color: #10B981; border: 1.5px solid #10B981; }
    .rr-bad { background: rgba(239, 68, 68, 0.2); color: #EF4444; border: 1.5px solid #EF4444; }

    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #0052D4 0%, #4364F7 51%, #6FB1FC 100%);
        color: #FFFFFF !important;
        border: none;
        padding: 14px 28px;
        font-size: 1.2rem;
        font-weight: 800;
        border-radius: 10px;
        letter-spacing: 0.5px;
        box-shadow: 0 4px 18px rgba(67, 100, 247, 0.4);
        transition: all 0.25s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(67, 100, 247, 0.6);
    }
    
    button[data-baseweb="tab"] {
        font-size: 1.2rem !important;
        font-weight: 800 !important;
        padding: 12px 24px !important;
    }
    
    .stMarkdown h3 {
        font-size: 1.5rem !important;
        font-weight: 800 !important;
        color: #F8FAFC !important;
    }
</style>
""",
    unsafe_allow_html=True,
)


def get_sheet_id():
    try:
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        return url.split("/d/")[1].split("/")[0] if "/d/" in url else None
    except Exception:
        return None


SHEET_ID = get_sheet_id()


def load_data(sheet_name):
    if not SHEET_ID:
        return pd.DataFrame()
    try:
        timestamp = datetime.datetime.now().timestamp()
        csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sheet_name)}&t={timestamp}"
        df = pd.read_csv(csv_url)
        return df.fillna("")
    except Exception:
        return pd.DataFrame()


def sync_to_cloud(payload):
    if "script.google.com" in GAS_WEBAPP_URL:
        try:
            res = requests.post(GAS_WEBAPP_URL, json=payload, timeout=8)
            if res.status_code == 200:
                return True
            else:
                st.error(f"⚠️ 雲端寫入回應狀態碼: {res.status_code}")
                return False
        except Exception as e:
            st.error(f"⚠️ 無法同步至 Google Sheet，原因: {e}")
            return False
    return False


# --- Header 區域 ---
st.markdown(
    """
<div class="title-container">
    <span class="main-title">⚡ FX & Gold Tracker Pro</span>
</div>
""",
    unsafe_allow_html=True,
)
st.caption("專業交易員風控試算與戰術檢討儀表板")

col_rate, col_lev, col_pnl_usd, col_pnl_twd = st.columns(4)
with col_rate:
    usdtwd = st.number_input("USD/TWD 匯率", value=32.0, step=0.1)
with col_lev:
    leverage = st.number_input("帳戶槓桿倍數", value=100, step=10)

cloud_active = load_data("active")
cloud_history = load_data("history")

if "history_list" not in st.session_state:
    st.session_state["history_list"] = []

local_history = pd.DataFrame(st.session_state["history_list"])

if not cloud_history.empty and not local_history.empty:
    history_df = pd.concat([cloud_history, local_history], ignore_index=True)
elif not local_history.empty:
    history_df = local_history
else:
    history_df = cloud_history

total_usd = 0.0
if not history_df.empty and "盈虧(USD)" in history_df.columns:
    history_df["盈虧(USD)"] = (
        pd.to_numeric(history_df["盈虧(USD)"], errors="coerce").fillna(0)
    )
    total_usd = history_df["盈虧(USD)"].sum()

total_twd = total_usd * usdtwd

with col_pnl_usd:
    st.metric("歷史累計總盈虧 (USD)", f"${total_usd:,.2f}")
with col_pnl_twd:
    st.metric("歷史累計總盈虧 (TWD)", f"NT${total_twd:,.0f}")

st.markdown("<br>", unsafe_allow_html=True)

# --- 主 Tabs ---
tab1, tab2 = st.tabs(["📊 即時持倉與風控試算", "📜 歷史紀錄與績效分析"])

CONTRACT_SIZES = {
    "XAUUSD": 100,
    "USDJPY": 100000,
    "GBPUSD": 100000,
    "EURUSD": 100000,
    "其他/自訂": 100000,
}

with tab1:
    st.subheader("⚡ 建立新交易與風控評估")

    c1, c2, c3, c4 = st.columns(4)
    symbol = c1.selectbox("商品名稱", list(CONTRACT_SIZES.keys()))
    direction = c2.selectbox("方向", ["BUY", "SELL"])
    lots = c3.number_input("下單手數", value=0.02, step=0.01, format="%.2f")
    contract_size = c4.number_input(
        "合約乘數", value=CONTRACT_SIZES[symbol]
    )

    c5, c6, c7, c8 = st.columns(4)
    entry_price = c5.number_input("進場價位", value=158.93, format="%.2f")
    exit_price = c6.number_input(
        "預期止盈 (TP)", value=158.10, format="%.2f"
    )
    stop_loss = c7.number_input("預定止損 (SL)", value=159.45, format="%.2f")
    swap = c8.number_input("隔夜利息 (USD)", value=0.0, step=0.5)

    c9, c10 = st.columns([1, 2])
    strategy = c9.selectbox(
        "策略標籤",
        ["突破進場", "回檔接單", "指標交叉", "左側摸底/猜頂", "其他"],
    )
    notes = c10.text_input("備註 (交易心態/進場條件)")

    # 風控計算核心
    if direction == "BUY":
        risk_points = entry_price - stop_loss
        reward_points = exit_price - entry_price
    else:
        risk_points = stop_loss - entry_price
        reward_points = entry_price - exit_price

    risk_points = max(0.0, risk_points)
    reward_points = max(0.0, reward_points)

    if symbol == "USDJPY":
        margin = (lots * contract_size) / leverage
        risk_usd = (risk_points * lots * contract_size) / entry_price
        reward_usd = (reward_points * lots * contract_size) / entry_price
    elif symbol == "XAUUSD":
        margin = (entry_price * lots * contract_size) / leverage
        risk_usd = risk_points * lots * contract_size
        reward_usd = reward_points * lots * contract_size
    else:
        margin = (entry_price * lots * contract_size) / leverage
        risk_usd = risk_points * lots * contract_size
        reward_usd = reward_points * lots * contract_size

    rr_ratio = (reward_points / risk_points) if risk_points > 0 else 0

    # 渲染風控面板
    rr_class = "rr-good" if rr_ratio >= 1.5 else "rr-bad"
    st.markdown(
        f"""
    <div class="risk-card">
        <div style="font-weight: 800; color: #94A3B8; font-size: 1.05rem; text-transform: uppercase; text-align: center; letter-spacing: 1px;">💡 即時風控試算面板</div>
        <div class="risk-grid">
            <div class="risk-item">
                <span class="risk-label">預佔保證金</span>
                <span class="risk-value" style="color: #38BDF8;">${margin:,.2f}</span>
            </div>
            <div class="risk-item">
                <span class="risk-label">預估最大虧損</span>
                <span class="risk-value" style="color: #F87171;">-${risk_usd:,.2f}</span>
            </div>
            <div class="risk-item">
                <span class="risk-label">預估目標獲利</span>
                <span class="risk-value" style="color: #34D399;">+${reward_usd:,.2f}</span>
            </div>
            <div class="risk-item">
                <span class="risk-label">風報比 (R:R)</span>
                <div style="margin-top: 2px;"><span class="rr-badge {rr_class}">1 : {rr_ratio:.2f}</span></div>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    if rr_ratio < 1.5 and risk_usd > 0:
        st.warning(
            "⚠️ **交易紀律提醒：** 當前風報比低於 1:1.5，請評估是否符合系統進場條件！"
        )

    if st.button("🚀 暫存至未平倉持倉清單"):
        new_id = 1
        if not cloud_active.empty and "ID" in cloud_active.columns:
            valid_ids = pd.to_numeric(cloud_active["ID"], errors="coerce").dropna()
            if not valid_ids.empty:
                new_id = int(valid_ids.max()) + 1

        trade_data = {
            "action": "add",
            "id": int(new_id),
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "symbol": symbol,
            "direction": direction,
            "lots": float(lots),
            "entry": float(entry_price),
            "sl": float(stop_loss),
            "tp": float(exit_price),
            "strategy": strategy,
            "notes": str(notes),
            "margin": float(round(margin, 2)),
            "swap": float(swap),
            "contract": float(contract_size),
            "pnl_usd": float(round(reward_usd + swap, 2)),
            "pnl_twd": float(round((reward_usd + swap) * usdtwd, 2)),
        }

        # 優先寫入雲端 Google Sheet，成功後才刷頁面
        if sync_to_cloud(trade_data):
            st.success("✅ 已成功同步存入 Google Sheet！")
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📌 當前未平倉試算單")

    # 渲染雲端未平倉單
    if not cloud_active.empty and "ID" in cloud_active.columns and len(cloud_active) > 0:
        for idx, item in cloud_active.iterrows():
            item_id = item.get("ID", idx + 1)
            sym = item.get("商品", symbol)
            dir_val = item.get("方向", direction)
            lots_val = item.get("手數", lots)
            strat_val = item.get("策略", strategy)

            dir_color = "🟢" if str(dir_val) == "BUY" else "🔴"

            with st.expander(
                f"{dir_color} 單號 #{item_id} | {sym} {dir_val} | 手數: {lots_val} | 策略: {strat_val}"
            ):
                st.write(item.to_dict())

                tp_val = item.get("預估出場價", entry_price)
                try:
                    default_exit = float(tp_val)
                except Exception:
                    default_exit = 0.0

                final_exit = st.number_input(
                    f"最終平倉價 (單號 #{item_id})",
                    value=default_exit,
                    key=f"exit_{idx}",
                )

                if st.button(
                    f"✅ 結算平倉轉入歷史 (單號 #{item_id})", key=f"btn_{idx}"
                ):
                    try:
                        entry_v = float(item.get("進場價", entry_price))
                    except Exception:
                        entry_v = entry_price
                        
                    try:
                        swap_v = float(item.get("隔夜利息(USD)", 0))
                    except Exception:
                        swap_v = 0.0
                        
                    try:
                        contract_v = float(item.get("合約乘數", 100000))
                    except Exception:
                        contract_v = 100000.0

                    if str(dir_val) == "BUY":
                        diff = final_exit - entry_v
                    else:
                        diff = entry_v - final_exit

                    if str(sym) == "USDJPY":
                        final_pnl = ((diff * float(lots_val) * contract_v) / final_exit) + swap_v
                    else:
                        final_pnl = (diff * float(lots_val) * contract_v) + swap_v

                    st.session_state["history_list"].append({
                        "ID": item_id,
                        "開倉時間": item.get("開倉時間", ""),
                        "結算時間": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "商品": sym,
                        "方向": dir_val,
                        "手數": lots_val,
                        "進場價": entry_v,
                        "預定止損價": item.get("預定止損價", 0),
                        "出場價": final_exit,
                        "策略": strat_val,
                        "備註": item.get("備註", ""),
                        "保證金(USD)": item.get("保證金(USD)", 0),
                        "隔夜利息(USD)": swap_v,
                        "盈虧(USD)": round(final_pnl, 2),
                        "盈虧(TWD)": round(final_pnl * usdtwd, 2),
                    })

                    sync_to_cloud({"action": "delete", "id": item_id})
                    st.success("平倉成功！單號已移至歷史紀錄。")
                    st.rerun()
    else:
        st.info("目前尚無未平倉持倉單。")

with tab2:
    st.subheader("📊 營運指標與戰術檢討")

    if not history_df.empty and len(history_df) > 0:
        pnl_series = pd.to_numeric(
            history_df["盈虧(USD)"], errors="coerce"
        ).fillna(0)

        winning_trades = pnl_series[pnl_series > 0]
        losing_trades = pnl_series[pnl_series < 0]

        win_rate = (
            (len(winning_trades) / len(pnl_series)) * 100
            if len(pnl_series) > 0
            else 0
        )
        gross_profit = winning_trades.sum()
        gross_loss = abs(losing_trades.sum())
        profit_factor = (
            (gross_profit / gross_loss)
            if gross_loss > 0
            else (float("inf") if gross_profit > 0 else 0.0)
        )

        cum_pnl = pnl_series.cumsum()
        peak = cum_pnl.cummax()
        drawdown = cum_pnl - peak
        max_drawdown = abs(drawdown.min()) if not drawdown.empty else 0.0

        m1, m2, m3 = st.columns(3)
        m1.metric("勝率 (Win Rate)", f"{win_rate:.1f}%")
        m2.metric(
            "獲利因子 (Profit Factor)",
            f"{profit_factor:.2f}" if profit_factor != float("inf") else "∞",
        )
        m3.metric("最大拉回 (Max Drawdown)", f"${max_drawdown:,.2f} USD")

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📈 資金成長曲線 (USD)")
        st.line_chart(cum_pnl, use_container_width=True)

        st.divider()

        st.subheader("📜 歷史已結算交易清單")
        st.dataframe(history_df, use_container_width=True)
    else:
        st.info("目前尚無歷史結算紀錄。")
