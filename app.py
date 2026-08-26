import datetime
import urllib.parse
import pandas as pd
import streamlit as st

st.set_page_config(page_title="FX & Gold Tracker", layout="wide")


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


st.title("📈 FX & Gold Tracker")

col_rate, col_lev, col_pnl_usd, col_pnl_twd = st.columns(4)
with col_rate:
    usdtwd = st.number_input("USD/TWD 匯率", value=32.0, step=0.1)
with col_lev:
    leverage = st.number_input("帳戶槓桿倍數", value=100, step=10)

# 初始化 Session State 紀錄
if "history_list" not in st.session_state:
    st.session_state["history_list"] = []
if "temp_trades" not in st.session_state:
    st.session_state["temp_trades"] = []

# 讀取雲端歷史資料並與本地平倉合併
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
    total_usd = (
        pd.to_numeric(history_df["盈虧(USD)"], errors="coerce")
        .fillna(0)
        .sum()
    )

total_twd = total_usd * usdtwd

with col_pnl_usd:
    st.metric("歷史累計總盈虧 (USD)", f"${total_usd:,.2f}")
with col_pnl_twd:
    st.metric("歷史累計總盈虧 (TWD)", f"NT${total_twd:,.0f}")

st.divider()

tab1, tab2 = st.tabs(["📊 即時持倉與試算", "📜 歷史交易紀錄 & 績效分析"])

CONTRACT_SIZES = {
    "XAUUSD": 100,
    "USDJPY": 100000,
    "GBPUSD": 100000,
    "EURUSD": 100000,
    "其他/自訂": 100000,
}

with tab1:
    st.subheader("新增持倉 / 動態風控試算")
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
        f"**💡 試算結果：** 預佔保證金 `${margin:,.2f}` | 預估虧損 `${risk_usd:,.2f}` | 預估獲利 `${reward_usd:,.2f}` | **風報比 1 : {rr_ratio:.2f}**"
    )

    if st.button("＋ 暫存至持倉清單"):
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
        st.success("已新增至當前持倉清單！")
        st.rerun()

    st.subheader("當前未平倉單")
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
                    st.success("已平倉並轉入歷史紀錄！")
                    st.rerun()
    else:
        st.info("目前尚無未平倉單。")

with tab2:
    st.subheader("雲端與本地歷史紀錄")
    if not history_df.empty:
        st.dataframe(history_df, use_container_width=True)
    else:
        st.info("尚無結算歷史紀錄。")
