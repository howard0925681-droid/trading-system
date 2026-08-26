import datetime
import urllib.parse
import pandas as pd
import streamlit as st

# 1. 頁面配置
st.set_page_config(
    page_title="FX & Gold Tracker Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. CSS：全域強行粗體穿透樣式
st.markdown(
    """
<style>
    /* 全局背景 */
    .stApp {
        background-color: #0B0E14 !important;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    header[data-testid="stHeader"] { background: transparent; }
    
    /* 頂部標題 */
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
    
    /* 小標題 (Labels) */
    div[data-testid="stMarkdownContainer"] p, label[data-testid="stWidgetLabel"] p {
        font-size: 1.15rem !important;
        font-weight: 800 !important;
        color: #E2E8F0 !important;
    }
    
    /* 統一外框底色與邊框 */
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

    /* 🔵 藍框：數字輸入框 */
    div[data-testid="stNumberInput"] input {
        font-size: 1.5rem !important;
        font-weight: 900 !important;
        color: #FFFFFF !important;
        height: 55px !important;
        text-shadow: 0px 0px 1px #FFFFFF !important; /* 視覺增粗 */
    }
    
    /* 🔴 紅框：全域穿透強行加粗下拉選單與純文字框 🔴 */
    div[data-testid="stTextInput"] input,
    div[data-baseweb="select"] *,
    div[data-baseweb="popover"] * {
        font-size: 1.5rem !important;
        font-weight: 900 !important; /* 極致加粗 */
        color: #FFFFFF !important;
        -webkit-text-stroke: 0.6px #FFFFFF !important; /* 強制描邊增粗 */
        text-shadow: 0px 0px 1px #FFFFFF !important; /* 視覺加粗特效 */
    }

    /* KPI 頂部卡片 */
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

    /* 酷炫風控試算面板卡片 */
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

    /* 按鈕 (Main Submit Button) */
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
    
    /* Tab 分頁標題 */
    button[data-baseweb="tab"] {
        font-size: 1.2rem !important;
        font-weight: 800 !important;
        padding: 12px 24px !important;
    }
    
    /* 次標題 */
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
        csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sheet_name)}"
        df = pd.read_csv(csv_url)
        return df.dropna(how="all")
    except Exception:
        return pd.DataFrame()


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

if "history_list" not in st.session_state:
    st.session_state["history_list"] = []
if "temp_trades" not in st.session_state:
    st.session_state["temp_trades"] = []

cloud_history = load_data("history")
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
    entry_price = c5.number_input("進場價位", value=2600.00, format="%.2f")
    exit_price = c6.number_input(
        "預期止盈 (TP)", value=2620.00, format="%.2f"
    )
    stop_loss = c7.number_input("預定止損 (SL)", value=2590.00, format="%.2f")
    swap = c8.number_input("隔夜利息 (USD)", value=0.0, step=0.5)

    c9, c10 = st.columns([1, 2])
    strategy = c9.selectbox(
        "策略標籤",
        ["突破進場", "回檔接單", "指標交叉", "左側摸底/猜頂", "其他"],
    )
    notes = c10.text_input("備註 (交易心態/進場條件)")

    # 動態風控試算
    if direction == "BUY":
        risk_per_unit = entry_price - stop_loss
        reward_per_unit = exit_price - entry_price
        margin = (entry_price * lots * contract_size) / leverage
    else:
        risk_per_unit = stop_loss - entry_price
        reward_per_unit = entry_price - exit_price
        margin = (entry_price * lots * contract_size) / leverage

    risk_usd = (
        risk_per_unit * lots * contract_size if risk_per_unit > 0 else 0
    )
    reward_usd = (
        reward_per_unit * lots * contract_size if reward_per_unit > 0 else 0
    )
    rr_ratio = (reward_per_unit / risk_per_unit) if risk_per_unit > 0 else 0

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
        st.session_state["temp_trades"].append({
            "ID": len(st.session_state["temp_trades"]) + 1,
            "開倉時間": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "商品": symbol,
            "方向": direction,
            "手數": lots,
            "進場價": entry_price,
            "預定止損價": stop_loss,
            "預估出場價": exit_price,
            "策略": strategy,
            "備註": notes,
            "保證金(USD)": round(margin, 2),
            "隔夜利息(USD)": swap,
            "合約乘數": contract_size,
            "預估盈虧(USD)": round(reward_usd + swap, 2),
            "預估盈虧(TWD)": round((reward_usd + swap) * usdtwd, 2),
        })
        st.success("已成功加入未平倉清單！")
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📌 當前未平倉試算單")

    if st.session_state["temp_trades"]:
        for idx, item in enumerate(st.session_state["temp_trades"]):
            dir_color = "🟢" if item["方向"] == "BUY" else "🔴"
            with st.expander(
                f"{dir_color} 單號 #{item['ID']} | {item['商品']} {item['方向']} | 手數: {item['手數']} | 策略: {item['策略']}"
            ):
                st.write(item)
                final_exit = st.number_input(
                    f"最終平倉價 (單號 #{item['ID']})",
                    value=float(item["預估出場價"]),
                    key=f"exit_{idx}",
                )

                if st.button(
                    f"✅ 結算平倉轉入歷史 (單號 #{item['ID']})", key=f"btn_{idx}"
                ):
                    if item["方向"] == "BUY":
                        final_pnl = (
                            (final_exit - item["進場價"])
                            * item["手數"]
                            * item["合約乘數"]
                        ) + item["隔夜利息(USD)"]
                    else:
                        final_pnl = (
                            (item["進場價"] - final_exit)
                            * item["手數"]
                            * item["合約乘數"]
                        ) + item["隔夜利息(USD)"]

                    st.session_state["history_list"].append({
                        "ID": item["ID"],
                        "開倉時間": item["開倉時間"],
                        "結算時間": datetime.datetime.now().strftime(
                            "%Y-%m-%d %H:%M"
                        ),
                        "商品": item["商品"],
                        "方向": item["方向"],
                        "手數": item["手數"],
                        "進場價": item["進場價"],
                        "預定止損價": item["預定止損價"],
                        "出場價": final_exit,
                        "策略": item["策略"],
                        "備註": item["備註"],
                        "保證金(USD)": item["保證金(USD)"],
                        "隔夜利息(USD)": item["隔夜利息(USD)"],
                        "盈虧(USD)": round(final_pnl, 2),
                        "盈虧(TWD)": round(final_pnl * usdtwd, 2),
                    })

                    st.session_state["temp_trades"].pop(idx)
                    st.success("平倉成功！資料已寫入歷史。")
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
