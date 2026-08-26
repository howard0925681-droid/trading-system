import datetime
import pandas as pd
import streamlit as st
from st_gsheets_connection import GSheetsConnection

# 頁面配置
st.set_page_config(
    page_title="多商品交易盈虧與歷史紀錄系統", layout="wide"
)

# 建立 Google Sheets 連線
conn = st.connection("gsheets", type=GSheetsConnection)


# 讀取資料函式
def load_data(worksheet_name):
    try:
        df = conn.read(worksheet=worksheet_name, ttl=0)
        return df.dropna(how="all")
    except Exception:
        return pd.DataFrame()


# --- 頂部參數 ---
st.title("📈 多商品即時盈虧與歷史交易管理系統")

col_rate, col_lev, col_pnl_usd, col_pnl_twd = st.columns(4)
with col_rate:
    usdtwd = st.number_input("USD/TWD 匯率", value=32.0, step=0.1)
with col_lev:
    leverage = st.number_input("帳戶槓桿倍數", value=100, step=10)

# 讀取歷史資料庫與持倉
history_df = load_data("history")
active_df = load_data("active_trades")

# 計算歷史總統計
total_usd = (
    history_df["盈虧(USD)"].astype(float).sum()
    if not history_df.empty and "盈虧(USD)" in history_df.columns
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

        submit = st.form_submit_button("＋ 新增至持倉列表 (同步至雲端)")

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

            new_trade = pd.DataFrame([
                {
                    "ID": len(history_df) + len(active_df) + 1,
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
            ])

            updated_active = pd.concat(
                [active_df, new_trade], ignore_index=True
            )
            conn.update(worksheet="active_trades", data=updated_active)
            st.success("已成功同步新增至雲端持倉！")
            st.rerun()

    st.subheader("當前未平倉單 (雲端同步)")
    if not active_df.empty:
        for idx, row in active_df.iterrows():
            with st.expander(
                f"單號 #{row['ID']} | {row['商品']} | {row['方向']} | 手數: {row['手數']} | 預估盈虧: ${row['預估盈虧(USD)']} USD"
            ):
                st.write(row.to_dict())
                final_exit = st.number_input(
                    f"最終平倉價 (單號 #{row['ID']})",
                    value=float(row["預估出場價"]),
                    key=f"exit_{idx}",
                )

                if st.button(f"✅ 一鍵結算平倉 (單號 #{row['ID']})"):
                    if row["方向"] == "BUY":
                        final_pnl = (
                            (final_exit - row["進場價"])
                            * row["手數"]
                            * row["合約乘數"]
                        ) + row["隔夜利息(USD)"]
                    else:
                        final_pnl = (
                            (row["進場價"] - final_exit)
                            * row["手數"]
                            * row["合約乘數"]
                        ) + row["隔夜利息(USD)"]

                    history_row = pd.DataFrame([
                        {
                            "ID": row["ID"],
                            "開倉時間": row["開倉時間"],
                            "結算時間": datetime.datetime.now().strftime(
                                "%Y-%m-%d %H:%M"
                            ),
                            "商品": row["商品"],
                            "方向": row["方向"],
                            "手數": row["手數"],
                            "進場價": row["進場價"],
                            "出場價": final_exit,
                            "保證金(USD)": row["保證金(USD)"],
                            "隔夜利息(USD)": row["隔夜利息(USD)"],
                            "合約乘數": row["合約乘數"],
                            "盈虧(USD)": round(final_pnl, 2),
                            "盈虧(TWD)": round(final_pnl * usdtwd, 2),
                        }
                    ])

                    # 寫入 history，並從 active_trades 移除
                    updated_history = pd.concat(
                        [history_df, history_row], ignore_index=True
                    )
                    conn.update(worksheet="history", data=updated_history)

                    updated_active = active_df.drop(idx)
                    conn.update(worksheet="active_trades", data=updated_active)

                    st.success("平倉成功！資料已永久轉入雲端歷史紀錄。")
                    st.rerun()
    else:
        st.info("目前無未平倉單。")

with tab2:
    st.subheader("歷史已結算交易日誌 (永久保存)")
    if not history_df.empty:
        st.dataframe(history_df, use_container_width=True)
    else:
        st.info("尚無歷史結算紀錄。")
