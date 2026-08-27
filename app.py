import datetime

import pandas as pd
import requests
import streamlit as st

# 1. 頁面配置
st.set_page_config(
    page_title="FX & Gold Tracker Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 🔗 Google Apps Script 網址 (負責讀取 + 寫入) 🔗
GAS_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbxhPaVglQaEZ-FtASX5Arp13kWgOFB28E2g-_NIfDlX_CykIx3dRtgitDH07JkE1g_uGA/exec"

CONTRACT_SIZES = {
    "XAUUSD": 100,
    "USDJPY": 100000,
    "GBPUSD": 100000,
    "EURUSD": 100000,
    "其他/自訂": 100000,
}

STRATEGY_OPTIONS = ["突破進場", "回檔接單", "指標交叉", "左側摸底/猜頂", "其他"]

# 2. CSS 樣式設定
st.markdown(
    """
<style>
    .stApp {
        background-color: #0B0E14 !important;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    header[data-testid="stHeader"] { background: transparent; }

    /* ---------- 標題 ---------- */
    .title-container {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 2px;
    }
    .main-title {
        font-size: 2.4rem;
        font-weight: 900;
        letter-spacing: -0.5px;
        background: linear-gradient(90deg, #00F2FE 0%, #4FACFE 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .header-divider {
        height: 3px;
        border-radius: 3px;
        background: linear-gradient(90deg, #00F2FE 0%, rgba(79,172,254,0) 100%);
        margin: 10px 0 22px 0;
        opacity: 0.6;
    }

    /* ---------- 文字 / 標籤 ---------- */
    div[data-testid="stMarkdownContainer"] p, label[data-testid="stWidgetLabel"] p {
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        color: #E2E8F0 !important;
    }
    .stMarkdown h3 {
        font-size: 1.35rem !important;
        font-weight: 800 !important;
        color: #F8FAFC !important;
    }
    .section-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 6px 0 14px 0;
    }
    .section-header .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #00F2FE;
        box-shadow: 0 0 10px #00F2FE;
    }
    .section-header span.label {
        font-size: 1.25rem;
        font-weight: 800;
        color: #F8FAFC;
    }
    .section-caption {
        color: #64748B !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
        margin-top: -8px;
    }

    /* ---------- 輸入元件 ---------- */
    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div {
        background-color: #151A23 !important;
        border: 1.5px solid #2A3241 !important;
        border-radius: 8px !important;
        min-height: 48px !important;
    }
    div[data-baseweb="input"] > div:focus-within,
    div[data-baseweb="select"] > div:focus-within {
        border-color: #00F2FE !important;
        box-shadow: 0 0 10px rgba(0, 242, 254, 0.25) !important;
    }
    div[data-testid="stNumberInput"] input {
        font-size: 1.1rem !important;
        font-weight: 500 !important;
        color: #FFFFFF !important;
        height: 48px !important;
    }
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] div,
    div[data-baseweb="select"] input {
        font-size: 1.35rem !important;
        font-weight: 800 !important;
        color: #FFFFFF !important;
    }
    div[data-testid="stTextInput"] input {
        font-size: 1.05rem !important;
        font-weight: 400 !important;
        color: #FFFFFF !important;
        height: 48px !important;
    }
    div[data-testid="stDateInput"] input {
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: #FFFFFF !important;
    }

    /* ---------- 卡片式容器 ---------- */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 14px !important;
        border-color: #232D3F !important;
        background: linear-gradient(160deg, #10141C 0%, #131822 100%);
    }

    /* ---------- Metric ---------- */
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #131822 0%, #171D2A 100%);
        border: 1.5px solid #232D3F;
        padding: 18px 20px;
        border-radius: 14px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.35);
    }
    div[data-testid="stMetricLabel"] {
        color: #94A3B8 !important;
        font-size: 0.92rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.6px;
    }
    div[data-testid="stMetricValue"] {
        color: #00F2FE !important;
        font-size: 1.9rem !important;
        font-weight: 900 !important;
    }

    /* ---------- 風控試算面板 ---------- */
    .risk-card {
        background: linear-gradient(135deg, #111622 0%, #172030 100%);
        border: 1.5px solid #222F43;
        border-left: 6px solid #00F2FE;
        border-radius: 12px;
        padding: 20px 24px;
        margin: 18px 0;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
    }
    .risk-grid {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 14px;
        margin-top: 14px;
        width: 100%;
        flex-wrap: wrap;
    }
    .risk-item {
        flex: 1;
        min-width: 130px;
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        padding: 12px 8px;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }
    .risk-label {
        color: #94A3B8;
        font-size: 0.9rem;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .risk-value {
        font-size: 1.5rem;
        font-weight: 900;
    }
    .rr-badge {
        display: inline-block;
        padding: 5px 16px;
        border-radius: 8px;
        font-weight: 800;
        font-size: 1.25rem;
    }
    .rr-good { background: rgba(16, 185, 129, 0.2); color: #10B981; border: 1.5px solid #10B981; }
    .rr-bad { background: rgba(239, 68, 68, 0.2); color: #EF4444; border: 1.5px solid #EF4444; }

    /* ---------- 每日風控警示橫幅 ---------- */
    .daily-alert {
        border-radius: 12px;
        padding: 16px 22px;
        margin: 6px 0 18px 0;
        font-weight: 800;
        font-size: 1.05rem;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .daily-alert-danger {
        background: rgba(239, 68, 68, 0.12);
        border: 1.5px solid #EF4444;
        color: #FCA5A5;
    }
    .daily-alert-safe {
        background: rgba(16, 185, 129, 0.08);
        border: 1.5px solid #1F6E52;
        color: #6EE7B7;
    }

    /* ---------- 按鈕 ---------- */
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #0052D4 0%, #4364F7 51%, #6FB1FC 100%);
        color: #FFFFFF !important;
        border: none;
        padding: 12px 24px;
        font-size: 1.1rem;
        font-weight: 800;
        border-radius: 10px;
        letter-spacing: 0.5px;
        box-shadow: 0 4px 18px rgba(67, 100, 247, 0.4);
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(67, 100, 247, 0.6);
    }

    button[data-baseweb="tab"] {
        font-size: 1.1rem !important;
        font-weight: 800 !important;
        padding: 10px 20px !important;
    }

    /* ---------- Alert box 深色化 ---------- */
    div[data-testid="stAlert"] {
        border-radius: 10px !important;
    }

    /* ---------- 手機版響應式 ---------- */
    @media (max-width: 700px) {
        .main-title { font-size: 1.7rem; }
        div[data-testid="stHorizontalBlock"] {
            flex-wrap: wrap !important;
        }
        div[data-testid="stHorizontalBlock"] > div {
            min-width: 100% !important;
        }
        .risk-item { min-width: 100%; }
        div[data-testid="stMetricValue"] { font-size: 1.5rem !important; }
    }
</style>
""",
    unsafe_allow_html=True,
)


def section_header(icon_dot_label):
    """統一的區塊標題樣式（左側光點 + 標題文字）。"""
    st.markdown(
        f'<div class="section-header"><span class="dot"></span><span class="label">{icon_dot_label}</span></div>',
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=5)  # 5秒快取，防止重複讀取
def load_data(sheet_name):
    if "script.google.com" not in GAS_WEBAPP_URL:
        return pd.DataFrame()
    try:
        # 直接呼叫 GAS 的 doGet，即時讀取試算表當下內容，
        # 不透過「發布到網路」那個有快取延遲（約 5 分鐘）的公開連結。
        resp = requests.get(GAS_WEBAPP_URL, params={"sheet": sheet_name}, timeout=15)
        resp.raise_for_status()
        rows = resp.json()

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        return df.fillna("")
    except requests.exceptions.Timeout:
        st.error("⚠️ 讀取雲端資料逾時（超過 15 秒無回應），請檢查網路連線或稍後再試。")
        return pd.DataFrame()
    except ValueError as e:
        st.error(f"⚠️ 雲端資料格式錯誤，請確認 GAS 部署設定是否正確。錯誤訊息: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"讀取雲端資料發生錯誤: {e}")
        return pd.DataFrame()


def sync_to_cloud(payload):
    """
    同步寫入雲端 Google Sheet，並「等待」寫入完成才回傳結果。
    同步等待可避免寫入還沒完成、畫面就先重整讀到舊資料，導致剛新增的單子被覆蓋消失。
    """
    if "script.google.com" not in GAS_WEBAPP_URL:
        return False, "尚未設定有效的 GAS_WEBAPP_URL"
    try:
        resp = requests.post(GAS_WEBAPP_URL, json=payload, timeout=20)
        resp.raise_for_status()
        return True, resp.text
    except Exception as e:
        return False, str(e)


def merge_cloud_and_local(cloud_df, local_list, id_col="ID"):
    """
    以雲端資料為主，但保留「本機有、雲端還沒出現」的資料列，
    避免使用者剛新增的單子因雲端還沒同步完成而被誤判成不存在。
    """
    cloud_records = []
    cloud_ids = set()
    if not cloud_df.empty and id_col in cloud_df.columns:
        cloud_records = cloud_df.to_dict(orient="records")
        cloud_ids = {str(r.get(id_col)) for r in cloud_records}

    local_only = [t for t in local_list if str(t.get(id_col)) not in cloud_ids]
    return cloud_records + local_only


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
st.markdown('<div class="header-divider"></div>', unsafe_allow_html=True)

# --- 側邊欄：帳戶與風控設定（手機版可收合，節省主畫面空間） ---
with st.sidebar:
    st.markdown("### ⚙️ 帳戶設定")
    usdtwd = st.number_input("USD/TWD 匯率", value=32.0, step=0.1)
    leverage = st.number_input("帳戶槓桿倍數", value=100, step=10)

    st.divider()
    st.markdown("### 🛡️ 風控警示設定")
    daily_loss_limit = st.number_input(
        "每日虧損上限 (USD)",
        value=200.0,
        step=10.0,
        help="今日已實現虧損（依平倉單的開倉日期估算）超過這個金額時，畫面會跳出警示提醒你停手。",
    )

    st.divider()
    if st.button("🔄 手動重新整理雲端資料"):
        load_data.clear()
        st.rerun()

# --- 資料載入與合併 ---
cloud_active = load_data("active")
cloud_history = load_data("history")

if "active_trades" not in st.session_state:
    st.session_state["active_trades"] = []
if "history_list" not in st.session_state:
    st.session_state["history_list"] = []

st.session_state["active_trades"] = merge_cloud_and_local(
    cloud_active, st.session_state["active_trades"], id_col="ID"
)

if not cloud_history.empty and "盈虧(USD)" in cloud_history.columns:
    history_records = merge_cloud_and_local(
        cloud_history, st.session_state["history_list"], id_col="ID"
    )
    history_df = pd.DataFrame(history_records) if history_records else cloud_history
else:
    history_df = pd.DataFrame(st.session_state["history_list"])

if not history_df.empty and "盈虧(USD)" in history_df.columns:
    history_df["盈虧(USD)"] = pd.to_numeric(history_df["盈虧(USD)"], errors="coerce").fillna(0)

total_usd = history_df["盈虧(USD)"].sum() if not history_df.empty and "盈虧(USD)" in history_df.columns else 0.0
total_twd = total_usd * usdtwd

# --- 今日已實現盈虧（依開倉日期估算，用於每日虧損上限警示） ---
today_pnl = 0.0
if not history_df.empty and "開倉時間" in history_df.columns and "盈虧(USD)" in history_df.columns:
    parsed_dates = pd.to_datetime(history_df["開倉時間"], errors="coerce")
    today = datetime.datetime.now().date()
    today_mask = parsed_dates.dt.date == today
    today_pnl = history_df.loc[today_mask, "盈虧(USD)"].sum()

overall_win_rate = 0.0
if not history_df.empty and "盈虧(USD)" in history_df.columns and len(history_df) > 0:
    overall_win_rate = (history_df["盈虧(USD)"] > 0).sum() / len(history_df) * 100

# --- 每日風控警示橫幅 ---
if daily_loss_limit > 0 and today_pnl <= -daily_loss_limit:
    st.markdown(
        f'<div class="daily-alert daily-alert-danger">🚨 已達今日虧損上限！今日已實現虧損 ${abs(today_pnl):,.2f}（上限 ${daily_loss_limit:,.2f}），建議停止交易並檢討。</div>',
        unsafe_allow_html=True,
    )
elif today_pnl < 0:
    remaining = daily_loss_limit - abs(today_pnl)
    st.markdown(
        f'<div class="daily-alert daily-alert-safe">🛡️ 今日已實現虧損 ${abs(today_pnl):,.2f}，距離每日上限還有 ${remaining:,.2f} 空間。</div>',
        unsafe_allow_html=True,
    )

# --- KPI 卡片 ---
k1, k2, k3, k4 = st.columns(4)
k1.metric("歷史累計總盈虧 (USD)", f"${total_usd:,.2f}")
k2.metric("歷史累計總盈虧 (TWD)", f"NT${total_twd:,.0f}")
k3.metric("今日已實現盈虧 (USD)", f"${today_pnl:,.2f}")
k4.metric("整體勝率", f"{overall_win_rate:.1f}%")

st.markdown("<br>", unsafe_allow_html=True)

# --- 主 Tabs ---
tab1, tab2, tab3 = st.tabs(["⚡ 建倉與持倉", "📜 歷史紀錄", "📊 統計分析"])

with tab1:
    with st.container(border=True):
        section_header("建立新交易與風控評估")

        c1, c2 = st.columns(2)
        symbol = c1.selectbox("商品名稱", list(CONTRACT_SIZES.keys()))
        direction = c2.selectbox("方向", ["BUY", "SELL"])

        c3, c4 = st.columns(2)
        lots = c3.number_input("下單手數", value=0.02, step=0.01, format="%.2f")
        contract_size = c4.number_input("合約乘數", value=CONTRACT_SIZES[symbol])

        c5, c6 = st.columns(2)
        entry_price = c5.number_input("進場價位", value=158.93, format="%.2f")
        exit_price = c6.number_input("預期止盈 (TP)", value=158.10, format="%.2f")

        c7, c8 = st.columns(2)
        stop_loss = c7.number_input("預定止損 (SL)", value=159.45, format="%.2f")
        swap = c8.number_input("隔夜利息 (USD)", value=0.0, step=0.5)

        c9, c10 = st.columns([1, 2])
        strategy = c9.selectbox("策略標籤", STRATEGY_OPTIONS)
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
        else:
            margin = (entry_price * lots * contract_size) / leverage
            risk_usd = risk_points * lots * contract_size
            reward_usd = reward_points * lots * contract_size

        rr_ratio = (reward_points / risk_points) if risk_points > 0 else 0

        rr_class = "rr-good" if rr_ratio >= 1.5 else "rr-bad"
        st.markdown(
            f"""
        <div class="risk-card">
            <div style="font-weight: 800; color: #94A3B8; font-size: 1rem; text-transform: uppercase; text-align: center; letter-spacing: 1px;">💡 即時風控試算面板</div>
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
            st.warning("⚠️ **交易紀律提醒：** 當前風報比低於 1:1.5，請評估是否符合系統進場條件！")

        if st.button("🚀 暫存至未平倉持倉清單"):
            new_id = 1
            if st.session_state["active_trades"]:
                new_id = max([int(t.get("ID", 0)) for t in st.session_state["active_trades"]]) + 1

            trade_item = {
                "ID": new_id,
                "開倉時間": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "商品": symbol,
                "方向": direction,
                "手數": float(lots),
                "進場價": float(entry_price),
                "預定止損價": float(stop_loss),
                "預估出場價": float(exit_price),
                "策略": strategy,
                "備註": str(notes),
                "保證金(USD)": float(round(margin, 2)),
                "隔夜利息(USD)": float(swap),
                "合約乘數": float(contract_size),
                "預估盈虧(USD)": float(round(reward_usd + swap, 2)),
                "預估盈虧(TWD)": float(round((reward_usd + swap) * usdtwd, 2)),
            }

            sync_payload = {
                "action": "add",
                "sheet": "active",
                "id": new_id,
                "time": trade_item["開倉時間"],
                "symbol": symbol,
                "direction": direction,
                "lots": trade_item["手數"],
                "entry": trade_item["進場價"],
                "sl": trade_item["預定止損價"],
                "tp": trade_item["預估出場價"],
                "strategy": strategy,
                "notes": trade_item["備註"],
                "margin": trade_item["保證金(USD)"],
                "swap": trade_item["隔夜利息(USD)"],
                "contract": trade_item["合約乘數"],
                "pnl_usd": trade_item["預估盈虧(USD)"],
                "pnl_twd": trade_item["預估盈虧(TWD)"],
            }

            with st.spinner("正在寫入雲端資料庫，請稍候..."):
                ok, msg = sync_to_cloud(sync_payload)

            if ok:
                st.session_state["active_trades"].append(trade_item)
                load_data.clear()
                st.success("成功加入持倉清單，並已同步雲端！")
                st.rerun()
            else:
                st.error(f"⚠️ 雲端同步失敗，尚未加入清單。請確認 GAS 部署網址是否有效，並重試。錯誤訊息：{msg}")

    st.markdown("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        section_header(f"當前未平倉試算單（{len(st.session_state['active_trades'])} 筆）")

        if st.session_state["active_trades"]:
            for idx, item in enumerate(list(st.session_state["active_trades"])):
                item_id = item.get("ID", idx + 1)
                sym = item.get("商品", symbol)
                dir_val = item.get("方向", direction)
                lots_val = item.get("手數", lots)
                strat_val = item.get("策略", strategy)

                dir_color = "🟢" if str(dir_val) == "BUY" else "🔴"

                with st.expander(
                    f"{dir_color} 單號 #{item_id} | {sym} {dir_val} | 手數: {lots_val} | 策略: {strat_val}"
                ):
                    st.write(item)

                    try:
                        default_exit = float(item.get("預估出場價", entry_price))
                    except Exception:
                        default_exit = 0.0

                    final_exit = st.number_input(
                        f"最終平倉價 (單號 #{item_id})",
                        value=default_exit,
                        key=f"exit_{idx}",
                    )

                    if st.button(f"✅ 結算平倉轉入歷史 (單號 #{item_id})", key=f"btn_{idx}"):
                        try:
                            entry_v = float(item.get("進場價", entry_price))
                            swap_v = float(item.get("隔夜利息(USD)", 0))
                            contract_v = float(item.get("合約乘數", 100000))
                        except Exception:
                            entry_v, swap_v, contract_v = entry_price, 0.0, 100000.0

                        if str(dir_val) == "BUY":
                            diff = final_exit - entry_v
                        else:
                            diff = entry_v - final_exit

                        if str(sym) == "USDJPY":
                            final_pnl = ((diff * float(lots_val) * contract_v) / final_exit) + swap_v
                        else:
                            final_pnl = (diff * float(lots_val) * contract_v) + swap_v

                        history_item = {
                            "action": "add",
                            "sheet": "history",
                            "id": item_id,
                            "time": item.get("開倉時間", ""),
                            "symbol": sym,
                            "direction": dir_val,
                            "lots": lots_val,
                            "entry": entry_v,
                            "sl": item.get("預定止損價", 0),
                            "tp": final_exit,
                            "strategy": strat_val,
                            "notes": item.get("備註", ""),
                            "margin": item.get("保證金(USD)", 0),
                            "swap": swap_v,
                            "contract": contract_v,
                            "pnl_usd": round(final_pnl, 2),
                            "pnl_twd": round(final_pnl * usdtwd, 2),
                        }

                        with st.spinner("正在同步平倉結果至雲端，請稍候..."):
                            ok_add, msg_add = sync_to_cloud(history_item)
                            ok_del, msg_del = sync_to_cloud(
                                {"action": "delete", "sheet": "active", "id": item_id}
                            )

                        if ok_add and ok_del:
                            st.session_state["history_list"].append(history_item)
                            st.session_state["active_trades"].pop(idx)
                            load_data.clear()
                            st.success("平倉成功！已移至歷史紀錄。")
                            st.rerun()
                        else:
                            detail = [
                                "新增歷史紀錄: " + ("成功" if ok_add else f"失敗 ({msg_add})"),
                                "刪除持倉單: " + ("成功" if ok_del else f"失敗 ({msg_del})"),
                            ]
                            st.error("⚠️ 雲端同步發生問題，尚未變更清單，請重新嘗試：\n" + "\n".join(detail))
        else:
            st.info("目前尚無未平倉持倉單。")

with tab2:
    with st.container(border=True):
        section_header("歷史紀錄篩選")

        if history_df.empty:
            st.info("目前尚無歷史結算紀錄。")
        else:
            f1, f2 = st.columns(2)
            symbol_options = sorted(history_df["商品"].dropna().unique().tolist()) if "商品" in history_df.columns else []
            strategy_options_hist = sorted(history_df["策略"].dropna().unique().tolist()) if "策略" in history_df.columns else []

            selected_symbols = f1.multiselect("依商品篩選", symbol_options, default=[])
            selected_strategies = f2.multiselect("依策略篩選", strategy_options_hist, default=[])

            date_series = pd.to_datetime(history_df["開倉時間"], errors="coerce") if "開倉時間" in history_df.columns else pd.Series(dtype="datetime64[ns]")
            valid_dates = date_series.dropna()

            if not valid_dates.empty:
                min_date, max_date = valid_dates.min().date(), valid_dates.max().date()
                date_range = st.date_input(
                    "依開倉日期區間篩選",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date,
                )
            else:
                date_range = None

            keyword = st.text_input("關鍵字搜尋（備註）", value="")

            filtered_df = history_df.copy()
            if selected_symbols and "商品" in filtered_df.columns:
                filtered_df = filtered_df[filtered_df["商品"].isin(selected_symbols)]
            if selected_strategies and "策略" in filtered_df.columns:
                filtered_df = filtered_df[filtered_df["策略"].isin(selected_strategies)]
            if date_range and isinstance(date_range, tuple) and len(date_range) == 2 and "開倉時間" in filtered_df.columns:
                start_d, end_d = date_range
                fdates = pd.to_datetime(filtered_df["開倉時間"], errors="coerce")
                filtered_df = filtered_df[(fdates.dt.date >= start_d) & (fdates.dt.date <= end_d)]
            if keyword and "備註" in filtered_df.columns:
                filtered_df = filtered_df[filtered_df["備註"].astype(str).str.contains(keyword, case=False, na=False)]

    st.markdown("<br>", unsafe_allow_html=True)

    if not history_df.empty:
        with st.container(border=True):
            section_header(f"篩選結果（{len(filtered_df)} / {len(history_df)} 筆）")

            if filtered_df.empty:
                st.info("篩選條件下沒有符合的紀錄，請調整篩選條件。")
            else:
                pnl_series = pd.to_numeric(filtered_df["盈虧(USD)"], errors="coerce").fillna(0)
                winning_trades = pnl_series[pnl_series > 0]
                losing_trades = pnl_series[pnl_series < 0]

                win_rate = (len(winning_trades) / len(pnl_series)) * 100 if len(pnl_series) > 0 else 0
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
                section_header("資金成長曲線 (USD)")
                st.line_chart(cum_pnl, use_container_width=True)

                st.divider()
                section_header("已結算交易明細")
                st.dataframe(filtered_df, use_container_width=True)

with tab3:
    if history_df.empty:
        st.info("目前尚無歷史結算紀錄，累積幾筆平倉單後即可看到統計圖表。")
    else:
        stats_df = history_df.copy()
        stats_df["盈虧(USD)"] = pd.to_numeric(stats_df["盈虧(USD)"], errors="coerce").fillna(0)

        with st.container(border=True):
            section_header("依商品統計")
            if "商品" in stats_df.columns:
                by_symbol = stats_df.groupby("商品").agg(
                    總盈虧=("盈虧(USD)", "sum"),
                    交易筆數=("盈虧(USD)", "count"),
                    勝率=("盈虧(USD)", lambda s: (s > 0).sum() / len(s) * 100 if len(s) > 0 else 0),
                ).round(2)

                cc1, cc2 = st.columns(2)
                with cc1:
                    st.caption("各商品總盈虧 (USD)")
                    st.bar_chart(by_symbol["總盈虧"], use_container_width=True)
                with cc2:
                    st.caption("各商品勝率 (%)")
                    st.bar_chart(by_symbol["勝率"], use_container_width=True)

                st.dataframe(by_symbol, use_container_width=True)
            else:
                st.info("目前資料沒有「商品」欄位可供統計。")

        st.markdown("<br>", unsafe_allow_html=True)

        with st.container(border=True):
            section_header("依策略統計")
            if "策略" in stats_df.columns:
                by_strategy = stats_df.groupby("策略").agg(
                    總盈虧=("盈虧(USD)", "sum"),
                    交易筆數=("盈虧(USD)", "count"),
                    勝率=("盈虧(USD)", lambda s: (s > 0).sum() / len(s) * 100 if len(s) > 0 else 0),
                ).round(2)

                cc3, cc4 = st.columns(2)
                with cc3:
                    st.caption("各策略總盈虧 (USD)")
                    st.bar_chart(by_strategy["總盈虧"], use_container_width=True)
                with cc4:
                    st.caption("各策略勝率 (%)")
                    st.bar_chart(by_strategy["勝率"], use_container_width=True)

                st.dataframe(by_strategy, use_container_width=True)
            else:
                st.info("目前資料沒有「策略」欄位可供統計。")
