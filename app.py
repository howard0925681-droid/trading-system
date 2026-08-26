import datetime
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# 頁面配置
st.set_page_config(page_title="FX & Gold Tracker", layout="wide")

# 建立 Google Sheets 連線
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(worksheet_name):
    try:
        df = conn.read(worksheet=worksheet_name, ttl=0)
        return df.dropna(how="all")
    except Exception:
        return pd.DataFrame()

# --- 頂部參數 ---
st.title("📈 FX & Gold Tracker")

col_rate, col_lev, col_pnl_usd, col_pnl_twd = st.columns(4)
with col_rate:
    usdtwd = st.number_input("USD/TWD 匯率", value=32.0, step=0.1)
with col_lev:
    leverage = st.number_input("帳戶槓桿倍數", value=100, step=10)

# 讀取雲端資料
history_df = load_data("history")
active_df = load_data("active_trades")

# 計算歷史總統計
total_usd = 0.0
if not history_df.empty and "盈虧(USD)" in history_df.columns:
    history_df["盈虧(USD)"] = pd.to_numeric(history_df["盈虧(USD)"], errors="coerce").fillna(0)
    total_usd = history_df["盈虧(USD)"].sum()

total_twd = total_usd * usdtwd

with col_pnl_usd:
    st.metric("歷史累計總盈虧 (USD)", f"${total_usd:,.2f}")
with col_pnl_twd:
    st.metric("歷史累計總盈虧 (TWD)", f"NT${total_twd:,.0f}")

st.divider()

# --- 分頁規劃 ---
tab1, tab2 = st.tabs(["📊 即時持倉與試算", "📜 歷史交易紀錄 & 績效分析"])

CONTRACT_SIZES = {"XAUUSD": 100, "USDJPY": 100000, "GBPUSD": 100000, "EURUSD": 100000, "其他/自訂": 100000}

with tab1:
    st.subheader("新增持倉 / 動態風控試算")
    # 移除 form 使數值能「即時試算」
    c1, c2, c3, c4 = st.columns(4)
    symbol = c1.selectbox("商品名稱", list(CONTRACT_SIZES.keys()))
    direction = c2.selectbox("方向", ["BUY", "SELL"])
    lots = c3.number_input("下單手數", value=0.02, step=0.01, format="%.2f")
    contract_size = c4.number_input("合約乘數", value=CONTRACT_SIZES[symbol])

    c5, c6, c7, c8 = st.columns(4)
    entry_price = c5.number_input("進場價位", value=2600.00, format="%.2f")
    exit_price = c6.number_input("預期止盈 (TP)", value=2620.00, format="%.2f")
    stop_loss = c7.number_input("預定止損 (SL)", value=2590.00, format="%.2f")
    swap = c8.number_input("隔夜利息 (USD)", value=0.0, step=0.5)

    c9, c10 = st.columns([1, 2])
    strategy = c9.selectbox("策略標籤", ["突破進場", "回檔接單", "指標交叉", "左側摸底/猜頂", "其他"])
    notes = c10.text_input("備註 (交易心態/進場條件)")

    # 動態計算風報比與保證金
    if direction == "BUY":
        risk_per_unit = entry_price - stop_loss
        reward_per_unit = exit_price - entry_price
        margin = (entry_price * lots * contract_size) / leverage
    else:
        risk_per_unit = stop_loss - entry_price
        reward_per_unit = entry_price - exit_price
        margin = (entry_price * lots * contract_size) / leverage

    risk_usd = risk_per_unit * lots * contract_size if risk_per_unit > 0 else 0
    reward_usd = reward_per_unit * lots * contract_size if reward_per_unit > 0 else 0
    rr_ratio = (reward_per_unit / risk_per_unit) if risk_per_unit > 0 else 0

    # 顯示動態結果與防呆警告
    st.info(f"**💡 試算結果：** 預佔保證金 `${margin:,.2f}` | 預估虧損 `${risk_usd:,.2f}` | 預估獲利 `${reward_usd:,.2f}` | **風報比 1 : {rr_ratio:.2f}**")
    
    if rr_ratio < 1.5 and risk_usd > 0:
        st.warning("⚠️ 系統警告：此單風報比 (R:R) 低於 1:1.5，長期期望值較低，請確認是否符合您的交易紀律！")

    if st.button("＋ 確認下單並同步至雲端"):
        new_trade = pd.DataFrame([{
            "ID": len(history_df) + len(active_df) + 1,
            "開倉時間": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "商品": symbol, "方向": direction, "手數": lots,
            "進場價": entry_price, "預定止損價": stop_loss, "預估出場價": exit_price,
            "策略": strategy, "備註": notes,
            "保證金(USD)": round(margin, 2), "隔夜利息(USD)": swap, "合約乘數": contract_size,
            "預估盈虧(USD)": round(reward_usd + swap, 2), "預估盈虧(TWD)": round((reward_usd + swap) * usdtwd, 2)
        }])
        updated_active = pd.concat([active_df, new_trade], ignore_index=True)
        conn.update(worksheet="active_trades", data=updated_active)
        st.success("已成功同步新增至雲端持倉！")
        st.rerun()

    st.subheader("當前未平倉單 (雲端同步)")
    if not active_df.empty:
        for idx, row in active_df.iterrows():
            with st.expander(f"單號 #{row['ID']} | {row['商品']} {row['方向']} | 手數: {row['手數']} | 策略: {row.get('策略', '')}"):
                st.write(row.to_dict())
                final_exit = st.number_input(f"最終平倉價 (單號 #{row['ID']})", value=float(row["預估出場價"]), key=f"exit_{idx}")

                if st.button(f"✅ 結算平倉並轉入歷史 (單號 #{row['ID']})"):
                    if row["方向"] == "BUY":
                        final_pnl = ((final_exit - row["進場價"]) * row["手數"] * row["合約乘數"]) + row["隔夜利息(USD)"]
                    else:
                        final_pnl = ((row["進場價"] - final_exit) * row["手數"] * row["合約乘數"]) + row["隔夜利息(USD)"]

                    history_row = pd.DataFrame([{
                        "ID": row["ID"], "開倉時間": row["開倉時間"],
                        "結算時間": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "商品": row["商品"], "方向": row["方向"], "手數": row["手數"],
                        "進場價": row["進場價"], "預定止損價": row.get("預定止損價", 0), "出場價": final_exit,
                        "策略": row.get("策略", ""), "備註": row.get("備註", ""),
                        "保證金(USD)": row["保證金(USD)"], "隔夜利息(USD)": row["隔夜利息(USD)"], "合約乘數": row["合約乘數"],
                        "盈虧(USD)": round(final_pnl, 2), "盈虧(TWD)": round(final_pnl * usdtwd, 2)
                    }])
                    updated_history = pd.concat([history_df, history_row], ignore_index=True)
                    conn.update(worksheet="history", data=updated_history)
                    updated_active = active_df.drop(idx)
                    conn.update(worksheet="active_trades", data=updated_active)
                    st.success("平倉成功！已轉入歷史紀錄。")
                    st.rerun()
    else:
        st.info("目前無未平倉單。")

with tab2:
    st.subheader("營運指標與資金曲線")
    if not history_df.empty and len(history_df) > 0:
        # 計算營運指標
        winning_trades = history_df[history_df["盈虧(USD)"] > 0]
        losing_trades = history_df[history_df["盈虧(USD)"] <= 0]
        
        win_rate = (len(winning_trades) / len(history_df)) * 100
        gross_profit = winning_trades["盈虧(USD)"].sum()
        gross_loss = abs(losing_trades["盈虧(USD)"].sum())
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float('inf')
        
        history_df["累計盈虧"] = history_df["盈虧(USD)"].cumsum()
        history_df["最高點"] = history_df["累計盈虧"].cummax()
        history_df["拉回"] = history_df["累計盈虧"] - history_df["最高點"]
        max_drawdown = abs(history_df["拉回"].min())

        m1, m2, m3 = st.columns(3)
        m1.metric("勝率 (Win Rate)", f"{win_rate:.1f}%")
        m2.metric("獲利因子 (Profit Factor)", f"{profit_factor:.2f}" if profit_factor != float('inf') else "∞")
        m3.metric("最大拉回 (Max Drawdown)", f"${max_drawdown:,.2f}")

        st.line_chart(history_df["累計盈虧"])
        
        st.subheader("歷史已結算交易日誌")
        st.dataframe(history_df, use_container_width=True)
    else:
        st.info("目前雲端歷史資料庫尚無已結算紀錄。")
