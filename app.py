import datetime
import urllib.parse
import pandas as pd
import streamlit as st

# 1. 頁面配置
st.set_page_config(
    page_title="FX & Gold Tracker Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. 自訂高質感 CSS 樣式
st.markdown(
    """
<style>
    /* 全局背景與字體優化 */
    .stApp {
        background-color: #0e1117;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    /* 隱藏預設頁眉與選單多餘邊框 */
    header[data-testid="stHeader"] {
        background: transparent;
    }
    
    /* 標題美化 */
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #4FACFE 0%, #00F2FE 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    /* KPI 數據卡片美化 */
    div[data-testid="stMetric"] {
        background: #161b22;
        border: 1px solid #30363d;
        padding: 18px 22px;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        border-color: #58a6ff;
    }
    div[data-testid="stMetricLabel"] {
        color: #8b949e !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div[data-testid="stMetricValue"] {
        color: #58a6ff !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }
    
    /* 按鈕美化 */
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #1f6feb 0%, #1158c7 100%);
        color: #ffffff !important;
        border: none;
        padding: 10px 20px;
        font-size: 0.95rem;
        font-weight: 600;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(31, 111, 235, 0.3);
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #388bfd 0%, #1f6feb 100%);
        box-shadow: 0 4px 15px rgba(56, 139, 253, 0.4);
        transform: translateY(-1px);
    }
    
    /* 折疊卡片 (Expander) 美化 */
    .streamlit-expanderHeader {
        background-color: #161b22 !important;
        border-radius: 8px !important;
        border: 1px solid #30363d !important;
        color: #c9d1d9 !important;
        font-weight: 600 !important;
    }
    .streamlit-expanderContent {
        background-color: #0d1117 !important;
        border: 1px solid #30363d !important;
        border-top: none !important;
        border-bottom-left-radius: 8px !important;
        border-bottom-right-radius: 8px !important;
    }
    
    /* Tab 頁籤標題美化 */
    button[data-baseweb="tab"] {
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: #8b949e !important;
        padding: 10px 20px !important;
    }
    button[aria-selected="true"] {
        color: #58a6ff !important;
        border-bottom-color: #58a6ff !important;
    }
    
    /* 提示訊息框美化 */
    .stAlert {
        border-radius: 10px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
</style>
""",
    unsafe_allow_html=True,
)


# 從 Secrets 取得 Google 試算表 ID
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


# --- 頂部區域 ---
st.markdown(
    '<div class="main-title">📈 FX & Gold Tracker Pro</div>',
    unsafe_allow_html=True,
)
st.caption("專業交易員風控試算與戰術檢討儀表板")

col_rate, col_lev, col_pnl_usd, col_pnl_twd = st.columns(4)
with col_rate:
    usdtwd = st.number_input("USD/TWD 匯率", value=32.0, step=0.1)
with col_lev:
    leverage = st.number_input("帳戶槓桿倍數", value=100, step=10)

# 初始化 Session State
if "history_list" not in st.session_state:
    st.session_state["history_list"] = []
if "temp_trades" not in st.session_state:
    st.session_state["temp_trades"] = []

# 讀取雲端與本地資料
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

# --- 主功能 Tabs ---
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

    # 風險計算
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

    st.info(
        f"**💡 風控試算卡：** 預佔保證金 `${margin:,.2f}` | 預估風險 `${risk_usd:,.2f}` | 預估獲利 `${reward_usd:,.2f}` | **風報比 1 : {rr_ratio:.2f}**"
    )

    if rr_ratio < 1.5 and risk_usd > 0:
        st.warning(
            "⚠️ **交易紀律提醒：** 當前風報比低於 1:1.5，請評估是否符合系統進場條件！"
        )

    if st.button("＋ 暫存至未平倉持倉清單"):
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
            with st.expander(
                f"單號 #{item['ID']} | {item['商品']} {item['方向']} | 手數: {item['手數']} | 策略: {item['策略']}"
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
