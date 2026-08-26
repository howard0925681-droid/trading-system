import datetime
import pandas as pd
import streamlit as st

# 頁面配置
st.set_page_config(
    page_title="多商品交易盈虧與歷史紀錄系統", layout="wide"
)

# 初始化 Session State (模組化歷史資料庫與持倉)
if "history" not in st_session:
    st.session_state["history"] = pd.DataFrame(
        columns=[
            "ID",
            "開倉時間",
            "結算時間",
            "商品",
            "方向",
            "手數",
            "進場價",
            "出場價",
            "保證金(USD)",
            "隔夜利息(USD)",
            "合約乘數",
            "盈虧(USD)",
            "盈虧(TWD)",
        ]
    )

if "active_trades" not in st.session_state:
    st.session_state["active_trades"] = []

# --- 頂部參數 ---
st.title("📈 多商品即時盈虧與歷史交易管理系統")

col_rate, col_lev, col_pnl_usd, col_pnl_twd = st.columns(4)
with col_rate:
    usdtwd = st.number_input("USD/TWD 匯率", value=32.0, step=0.1)
with col_lev:
    leverage = st.number_input("帳戶槓桿倍數", value=100, step=10)

# 計算歷史總統計
total_usd = (
    st.session_state["history"]["盈虧(USD)"].sum()
    if not st.session_state["history"].empty
    else 0.0
)
total_twd = total_usd * usdtwd

with col_pnl_usd:
    st.metric("歷史累計總盈虧 (USD)", f"${total_usd:,.2f}")
with col_pnl_twd:
    st.metric("歷史累計總盈虧 (TWD)", f"NT${total_twd:,.0f}")

st.divider()

# --- 分頁規劃 ---
tab1, tab2 = st.tabs(["📊 即時持倉與試算", "📜 歷史交易紀錄"])

# 預設合約乘數表
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

        submit = st.form_submit_button("＋ 新增至持倉列表")

        if submit:
            # 盈虧與保證金計算邏輯 (繼承原Excel邏輯)
            if direction == "BUY":
                pnl_usd = (
                    (exit_price - entry_price) * lots * contract_size
                ) + swap
                margin = (entry_price * lots * contract_size) / leverage
            else:
                pnl_usd = (
                    (entry_price - exit_price) * lots * contract_size
                ) + swap
                margin = (
                    (entry_price * lots * contract_size) / leverage
                    if "USD" in symbol[:3]
                    else (entry_price * lots * contract_size) / leverage
                )

            trade_item = {
                "ID": len(st.session_state["history"])
                + len(st.session_state["active_trades"])
                + 1,
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
            }
            st.session_state["active_trades"].append(trade_item)
            st.success("已新增持倉單！")

    st.subheader("當前未平倉單")
    if st.session_state["active_trades"]:
        for idx, trade in enumerate(st.session_state["active_trades"]):
            with st.expander(
                f"單號 #{trade['ID']} | {trade['商品']} | {trade['方向']} | 手數: {trade['手數']} | 預估盈虧: ${trade['預估盈虧(USD)']} USD"
            ):
                st.json(trade)
                final_exit = st.number_input(
                    f"最終平倉價 (單號 #{trade['ID']})",
                    value=float(trade["預估出場價"]),
                    key=f"exit_{idx}",
                )

                if st.button(f"✅ 一鍵結算平倉 (單號 #{trade['ID']})"):
                    # 重新計算最終盈虧
                    if trade["方向"] == "BUY":
                        final_pnl = (
                            (final_exit - trade["進場價"])
                            * trade["手數"]
                            * trade["合約乘數"]
                        ) + trade["隔夜利息(USD)"]
                    else:
                        final_pnl = (
                            (trade["進場價"] - final_exit)
                            * trade["手數"]
                            * trade["合約乘數"]
                        ) + trade["隔夜利息(USD)"]

                    # 轉入歷史資料庫
                    new_history_row = {
                        "ID": trade["ID"],
                        "開倉時間": trade["開倉時間"],
                        "結算時間": datetime.datetime.now().strftime(
                            "%Y-%m-%d %H:%M"
                        ),
                        "商品": trade["商品"],
                        "方向": trade["方向"],
                        "手數": trade["手數"],
                        "進場價": trade["進場價"],
                        "出場價": final_exit,
                        "保證金(USD)": trade["保證金(USD)"],
                        "隔夜利息(USD)": trade["隔夜利息(USD)"],
                        "合約乘數": trade["合約乘數"],
                        "盈虧(USD)": round(final_pnl, 2),
                        "盈虧(TWD)": round(final_pnl * usdtwd, 2),
                    }
                    st.session_state["history"] = pd.concat(
                        [
                            st.session_state["history"],
                            pd.DataFrame([new_history_row]),
                        ],
                        ignore_index=True,
                    )
                    st.session_state["active_trades"].pop(idx)
                    st.rerun()
    else:
        st.info("目前無未平倉單。")

with tab2:
    st.subheader("歷史已結算交易日誌")
    if not st.session_state["history"].empty:
        st.dataframe(st.session_state["history"], use_container_width=True)
    else:
        st.info("尚無歷史結算紀錄。")
