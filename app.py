import datetime
import urllib.parse
import pandas as pd
import streamlit as st

# 頁面配置
st.set_page_config(
    page_title="FX & Gold Tracker", layout="wide"
)


# 從 Secrets 取得 Google 試算表連結與 ID
def get_sheet_url():
    try:
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        # 提取 Sheet ID
        if "/d/" in url:
            sheet_id = url.split("/d/")[1].split("/")[0]
            return sheet_id
        return None
    except Exception:
        return None


SHEET_ID = get_sheet_url()


# 讀取 Google Sheets 分頁資料 (透過 CSV Export API)
def load_data(sheet_name):
    if not SHEET_ID:
        return pd.DataFrame()
    try:
        csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sheet_name)}"
        df = pd.read_csv(csv_url)
        return df.dropna(how="all")
    except Exception:
        return pd.DataFrame()


# --- 頂部參數 ---
st.title("📈 FX & Gold Tracker | 交易風控與紀錄系統")

if not SHEET_ID:
    st.error(
        "⚠️ 尚未在 Streamlit Secrets 設定 Google 試算表網址，請先完成 Secrets 設定！"
    )

col_rate, col_lev, col_pnl_usd, col_pnl_twd = st.columns(4)
with col_rate:
    usdtwd = st.number_input("USD/TWD 匯率", value=32.0, step=0.1)
with col_lev:
    leverage = st.number_input("帳戶槓桿倍數", value=100, step=10)

# 讀取歷史資料庫與持倉
history_df = load_data("history")
active_df = load_data("active_trades")

# 計算歷史總統計
total_usd = 0.0
if not history_df.empty:
    for col in history_df.columns:
        if "盈虧(USD)" in col:
            total_usd = (
                pd.to_numeric(history_df[col], errors="coerce").fillna(0).sum()
            )

total_twd = total_usd * usdtwd

with col_pnl_usd:
    st.metric("歷史累計總盈虧 (USD)", f"${total_usd:,.2f}")
with col_pnl_twd:
    st.metric("歷史累計總盈虧 (TWD)", f"NT${total_twd:,.0f}")

st.divider()

# --- 分頁規劃 ---
tab1, tab2 = st.tabs(["📊 即時持倉與試算", "📜 歷史交易紀錄"])

CONTRACT_SIZES = {
    "XAUUSD": 100,
    "USDJPY": 100000,
    "GBPUSD": 100000,
    "EURUSD": 100000,
    "其他/自訂": 100000,
}

with tab1:
    st.subheader("新增持倉 / 試算單")
    with st.form("trade_input_form"):
        c1, c2, c3, c4 = st.columns(4)
        symbol = c1.selectbox("商品名稱", list(CONTRACT_SIZES.keys()))
        direction = c2.selectbox("方向", ["BUY", "SELL"])
        lots = c3.number_input("下單手數", value=0.02, step=0.01, format="%.2f")
        contract_size = c4.number_input(
            "合約乘數", value=CONTRACT_SIZES[symbol]
        )

        c5, c6, c7 = st.columns(3)
        entry_price = c5.number_input(
            "進場價位", value=4635.86, format="%.2f"
        )
        exit_price = c6.number_input(
            "當前/預期出場價", value=4650.00, format="%.2f"
        )
        swap = c7.number_input("隔夜利息 (USD)", value=0.0, step=0.5)

        submit = st.form_submit_button("＋ 計算並暫存持倉")

        if submit:
            if direction == "BUY":
                pnl_usd = (
                    (exit_price - entry_price) * lots * contract_size
                ) + swap
                margin = (entry_price * lots * contract_size) / leverage
            else:
                pnl_usd = (
                    (entry_price - exit_price) * lots * contract_size
                ) + swap
                margin = (entry_price * lots * contract_size) / leverage

            if "active_trades_list" not in st.session_state:
                st.session_state["active_trades_list"] = []

            st.session_state["active_trades_list"].append({
                "ID": len(st.session_state["active_trades_list"]) + 1,
                "開倉時間": datetime.datetime.now().strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "商品": symbol,
                "方向": direction,
                "手數": lots,
                "進場價": entry_price,
                "預估出場價": exit_price,
                "保證金(USD)": round(margin, 2),
                "隔夜利息(USD)": swap,
                "合約乘數": contract_size,
                "預估盈虧(USD)": round(pnl_usd, 2),
                "預估盈虧(TWD)": round(pnl_usd * usdtwd, 2),
            })
            st.success("已新增至當前持倉！")

    st.subheader("當前未平倉單")
    if (
        "active_trades_list" in st.session_state
        and st.session_state["active_trades_list"]
    ):
        for idx, item in enumerate(st.session_state["active_trades_list"]):
            with st.expander(
                f"單號 #{item['ID']} | {item['商品']} | {item['方向']} | 手數: {item['手數']} | 預估盈虧: ${item['預估盈虧(USD)']} USD"
            ):
                st.json(item)
    else:
        st.info("目前尚無未平倉單。")

with tab2:
    st.subheader("雲端歷史已結算交易紀錄")
    if not history_df.empty:
        st.dataframe(history_df, use_container_width=True)
    else:
        st.info(
            "目前雲端歷史資料庫尚無已結算紀錄，或正在連線 Google Sheets..."
        )
