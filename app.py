import streamlit as st
import requests
import locale

st.set_page_config(page_title="Drifter: Strategy Recommendation Bot", layout="wide")

locale.setlocale(locale.LC_ALL, 'en_IE.UTF-8')  # European style commas

# Sidebar Inputs
with st.sidebar:
    st.header("🔐 Enter API Request Parameters")
    api_key = st.text_input("🔐 API Key", type="password")  # Hardcoded for now
    coin = st.selectbox("🌍 Coin", ["BTC", "ETH", "SOL"])
    # interval = st.selectbox("⏱️ Interval", ["1m", "15m", "1h"])
    # look_back = st.number_input("📘 Look Back (minutes)", min_value=1, value=180)
    trade_margin = st.number_input("📊 Trade Margin (%)", min_value=0.1, value=1.0)
    get_reco = st.button("🚀 Get Recommendation")

# Get recommendation and display UI
if get_reco:
    with st.spinner("Fetching recommendation..."):
        try:
            response = requests.get(
                "https://crypto-strategy-bot-1vst.onrender.com/recommendation",
                params={
                    "api_key": api_key,
                    "coin": coin,
                    "scrapping_interval": '1m',
                    "look_back": 240,
                    "trade_margin": trade_margin
                }
            )
            data = response.json()
            if data.get("status") == "success":
                result = data["data"][0]
                st.success("✅ Recommendation Fetched Successfully!")

                st.markdown(f"""
                <h1 style='font-size: 32px; background-color:#e0e0e0; padding:10px; border-radius:8px;'>📈 {coin} Strategy Recommendation</h1>
                """, unsafe_allow_html=True)

                col1, col2 = st.columns([2, 3], gap="small")
                with col1:
                    st.markdown("""
                        <h2 style='font-size: 28px; background-color:#f0f2f6; padding:10px; border-radius:8px;'>🧠 Recommendation Overview</h2>
                    """, unsafe_allow_html=True)

                    recommendation = result.get("recommendation", "NA").upper()
                    take_profit = result.get("take_profit")
                    stop_loss = result.get("stop_loss")
                    limit_order_price = result.get("limit_order_price")

                    color_map = {
                        "LONG": "#c8f7c5",
                        "HOLD": "#fdf3c9",
                        "SHORT": "#f7c5c5"
                    }
                    bg_color = color_map.get(recommendation, "#f9f9f9")

                    st.markdown(f"""
                        <div style='padding: 1rem; border-radius: 10px; background-color: {bg_color}; text-align:center;'>
                            <div style='font-size: 0.8rem; color: #888;'>Strategy Recommendation</div>
                            <div style='font-size: 2rem; font-weight: bold; margin: 0.5rem 0;'>{recommendation}</div>
                            <hr/>
                            <div style='font-size: 0.9rem;'>
                                <strong>Take Profit:</strong> {locale.format_string("%.1f", take_profit, grouping=True) if take_profit is not None else "-"}<br/>
                                <strong>Stop Loss:</strong> {locale.format_string("%.1f", stop_loss, grouping=True) if stop_loss is not None else "-"}<br/>
                                <strong>Limit Order:</strong> {locale.format_string("%.1f", limit_order_price, grouping=True) if limit_order_price is not None else "-"}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown("""
                        <h2 style='font-size: 28px; background-color:#f0f2f6; padding:10px; border-radius:8px;'>📊 Price & Technical Indicator Summary</h2>
                    """, unsafe_allow_html=True)

                    st.markdown("### 💰 Price Summary")
                    price_cols = st.columns(3)
                    price_cols[0].metric("Opening", locale.format_string("%.1f", result['opening_price'], grouping=True))
                    price_cols[1].metric("Closing", locale.format_string("%.1f", result['closing_price'], grouping=True))
                    price_cols[2].metric("Volume", locale.format_string("%.1f", result['volume_traded'], grouping=True))

                    price_cols_2 = st.columns(3)
                    price_cols_2[0].metric("High", locale.format_string("%.1f", result['highest_price'], grouping=True))
                    price_cols_2[1].metric("Low", locale.format_string("%.1f", result['lowest_price'], grouping=True))
                    price_cols_2[2].metric("Trades", locale.format_string("%.1f", result['trade_count'], grouping=True))

                    st.markdown("### 📈 Technical Indicators")
                    indicator_data = [
                        ("RSI", result['RSI'], "Overbought" if result['RSI'] > 70 else ("Oversold" if result['RSI'] < 30 else "Neutral")),
                        ("MACD", result['MACD'], "Positive" if result['MACD'] > 0 else "Negative"),
                        ("MACD Signal", result['MACD_signal'], "Above 0" if result['MACD_signal'] > 0 else "Below 0"),
                        ("SMA 20", result['SMA_20'], "Short-Term Avg"),
                        ("SMA 50", result['SMA_50'], "Medium-Term Avg"),
                        ("EMA 9", result['EMA_9'], "Fast EMA"),
                        ("EMA 21", result['EMA_21'], "Slow EMA"),
                        ("VWAP", result['VWAP'], "Volume-Weighted Avg"),
                        ("ATR (14)", result['ATR_14'], "Volatility"),
                        ("OBV", result['OBV'], "Volume Flow"),
                        ("Boll Upper", result['Bollinger_upper'], "Upper Band"),
                        ("Boll Lower", result['Bollinger_lower'], "Lower Band")
                    ]

                    st.markdown("""
                    <style>
                        .custom-table td, .custom-table th {
                            padding: 0.5rem 1rem;
                            border-bottom: 1px solid #ccc;
                        }
                        .custom-table {
                            border-collapse: collapse;
                            width: 100%;
                            margin-top: 1rem;
                        }
                        .custom-table th {
                            background-color: #f0f2f6;
                            text-align: left;
                        }
                    </style>
                    """, unsafe_allow_html=True)

                    table_html = """
                    <table class="custom-table">
                        <thead>
                            <tr><th>Indicator</th><th>Value</th><th>Remarks</th></tr>
                        </thead>
                        <tbody>
                    """
                    for name, val, remark in indicator_data:
                        table_html += f"<tr><td>{name}</td><td>{locale.format_string('%.1f', val, grouping=True)}</td><td>{remark}</td></tr>"
                    table_html += "</tbody></table>"
                    st.markdown(table_html, unsafe_allow_html=True)

            else:
                st.error("❌ Failed to fetch recommendation.")

        except Exception as e:
            st.error(f"🚨 Error: {str(e)}")
