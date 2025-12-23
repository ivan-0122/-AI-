import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volume import OnBalanceVolumeIndicator, MFIIndicator
from ta.volatility import BollingerBands
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 頁面設定 ---
st.set_page_config(page_title="台股 AI 戰情室 V14.0", layout="wide", page_icon="🦅")

# --- CSS 優化 (深色模式修復) ---
st.markdown("""
<style>
    .metric-card { background-color: #ffffff; border-left: 5px solid #ff4b4b; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 10px; color: #000000; }
    .analysis-box { background-color: #e8f5e9; border-left: 5px solid #2e7d32; padding: 15px; margin-top: 10px; margin-bottom: 20px; border-radius: 5px; font-size: 1.05em; color: #1b5e20; }
    .warning-box { background-color: #ffebee; border-left: 5px solid #c62828; padding: 15px; margin-top: 10px; margin-bottom: 20px; border-radius: 5px; font-size: 1.05em; color: #b71c1c; }
    .indicator-box { background-color: #f3e5f5; border: 1px solid #ce93d8; padding: 10px; border-radius: 5px; text-align: center; color: #4a148c; font-weight: bold; font-size: 0.9em; height: 100%;}
    .strategy-tag { background-color: #3f51b5; color: white; padding: 4px 12px; border-radius: 15px; font-weight: bold; font-size: 0.9em; display: inline-block; margin-bottom: 10px; }
    .stDataFrame th { color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- 資料庫 ---
STOCK_DB = {
    "🔥 熱門 ETF": {"0050.TW":"元大台灣50","0056.TW":"元大高股息","00878.TW":"國泰永續高股息","00929.TW":"復華台灣科技優息","00919.TW":"群益台灣精選高息","00940.TW":"元大台灣價值高息","006208.TW":"富邦台50","00713.TW":"元大台灣高息低波","00679B.TW":"元大美債20年","00687B.TW":"國泰20年美債"},
    "💻 半導體/AI": {"2330.TW":"台積電","2454.TW":"聯發科","2317.TW":"鴻海","2382.TW":"廣達","3231.TW":"緯創","2303.TW":"聯電","2308.TW":"台達電","3711.TW":"日月光","2379.TW":"瑞昱","3034.TW":"聯詠","3661.TW":"世芯-KY","3443.TW":"創意","6669.TW":"緯穎","2357.TW":"華碩","2356.TW":"英業達","2376.TW":"技嘉","3035.TW":"智原","3037.TW":"欣興","3017.TW":"奇鋐","3324.TW":"雙鴻","3044.TW":"健鼎","6274.TW":"台燿","2383.TW":"台光電","2449.TW":"京元電","6239.TW":"力成","3260.TWO":"威剛","8299.TWO":"群聯","3529.TW":"力旺","5274.TW":"信驊","3006.TW":"晶豪科","2368.TW":"金像電"},
    "⚡ 重電/綠能": {"1513.TW":"中興電","1519.TW":"華城","1503.TW":"士電","1504.TW":"東元","1609.TW":"大亞","2345.TW":"智邦","5388.TWO":"中磊","6285.TW":"啟碁","9958.TW":"世紀鋼","6806.TW":"森崴能源"},
    "💰 金融/傳產": {"2881.TW":"富邦金","2882.TW":"國泰金","2891.TW":"中信金","2886.TW":"兆豐金","5880.TW":"合庫金","2884.TW":"玉山金","5871.TW":"中租-KY","2603.TW":"長榮","2609.TW":"陽明","2615.TW":"萬海","2618.TW":"長榮航","2610.TW":"華航","2002.TW":"中鋼","1605.TW":"華新","1101.TW":"台泥","1301.TW":"台塑","2207.TW":"和泰車"},
    "📱 光電/其他": {"3008.TW":"大立光","3406.TW":"玉晶光","2409.TW":"友達","3481.TW":"群創","2327.TW":"國巨","2395.TW":"研華","2912.TW":"統一超","1216.TW":"統一","8454.TW":"富邦媒","2412.TW":"中華電","3045.TW":"台灣大","4904.TW":"遠傳"}
}
FLAT_STOCK_DB = {ticker: name for sector, stocks in STOCK_DB.items() for ticker, name in stocks.items()}

# --- 輔助函數 ---
def get_stock_name(ticker): return FLAT_STOCK_DB.get(ticker, ticker.replace(".TW", ""))

def get_name_online(ticker):
    name = FLAT_STOCK_DB.get(ticker)
    if name: return name
    try: return yf.Ticker(ticker).info.get('longName', ticker)
    except: return ticker

# --- 1. 貨幣政策與利率 (抓取 US 10Y Bond) ---
def get_macro_data():
    try:
        # 抓取美國10年期公債殖利率 (^TNX) 作為無風險利率指標
        tnx = yf.Ticker("^TNX")
        hist = tnx.history(period="5d")
        latest_rate = hist['Close'].iloc[-1]
        delta = latest_rate - hist['Close'].iloc[-2]
        return latest_rate, delta
    except:
        return 0, 0

# --- 9. 美股連動性分析 ---
def calculate_correlation(ticker):
    try:
        # 簡單映射：半導體比對 SOX，其他比對 S&P500
        benchmark = "^SOX" if "2330" in ticker or "2454" in ticker or "2379" in ticker else "^GSPC"
        
        stock_df = yf.download(ticker, period="3mo", progress=False)['Close']
        bench_df = yf.download(benchmark, period="3mo", progress=False)['Close']
        
        # 合併並計算相關係數
        df_corr = pd.concat([stock_df, bench_df], axis=1).dropna()
        df_corr.columns = ['Stock', 'Benchmark']
        correlation = df_corr['Stock'].corr(df_corr['Benchmark'])
        return correlation, benchmark
    except:
        return 0, "N/A"

# --- 3, 8, 10. 進階基本面 (EPS/營收/本益比/內部人) ---
def get_advanced_fundamentals_v14(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # 營收與 EPS
        rev_growth = info.get('revenueGrowth', None) # 營收成長率
        trailing_eps = info.get('trailingEps', None)
        forward_eps = info.get('forwardEps', None)
        
        # 估值 (P/E, P/B)
        f_pe = info.get('forwardPE', None)
        pb = info.get('priceToBook', None)
        
        # 內部人持股
        insider = info.get('heldPercentInsiders', None)
        
        # 估價
        target_price = info.get('targetMeanPrice', None)
        cheap_price = 0; fair_price = 0; expensive_price = 0
        
        if target_price and target_price > 0:
            fair_price = target_price
            cheap_price = target_price * 0.8
            expensive_price = target_price * 1.2
        elif forward_eps and forward_eps > 0:
            pe_mult = 15
            fair_price = forward_eps * pe_mult
            cheap_price = fair_price * 0.75
            expensive_price = fair_price * 1.25
        
        # 風險
        risks = []
        if info.get('operatingCashflow', 0) is not None and info.get('operatingCashflow', 0) < 0: risks.append("🔴 營業現金流為負")
        if info.get('grossMargins', 0) < 0.1: risks.append("🟠 毛利率過低")

        return {
            "營收成長": f"{round(rev_growth*100, 2)}%" if rev_growth else "-",
            "EPS(預估)": round(forward_eps, 2) if forward_eps else "-",
            "本益比": round(f_pe, 2) if f_pe else "-",
            "股價淨值比": round(pb, 2) if pb else "-",
            "內部人持股": f"{round(insider*100, 2)}%" if insider else "-",
            "便宜價": round(cheap_price, 2),
            "合理價": round(fair_price, 2),
            "昂貴價": round(expensive_price, 2),
            "風險": risks
        }
    except: return None

# --- 4, 7, 11, 12. 技術與籌碼分析 (MACD/乖離/大戶成本) ---
def analyze_stock_strategy(ticker, strategy_mode):
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if len(df) < 60: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        # 基礎指標
        df['MA5'] = SMAIndicator(df['Close'], window=5).sma_indicator()
        df['MA20'] = SMAIndicator(df['Close'], window=20).sma_indicator()
        df['MA60'] = SMAIndicator(df['Close'], window=60).sma_indicator()
        df['RSI'] = RSIIndicator(df['Close'], window=14).rsi()
        df['Vol_MA5'] = SMAIndicator(df['Volume'], window=5).sma_indicator()
        
        # 4. MACD
        macd = MACD(close=df['Close'], window_slow=26, window_fast=12, window_sign=9)
        df['MACD'] = macd.macd()
        df['MACD_Signal'] = macd.macd_signal()
        df['MACD_Hist'] = macd.macd_diff()
        
        # 籌碼指標
        df['OBV'] = OnBalanceVolumeIndicator(df['Close'], df['Volume']).on_balance_volume()
        df['OBV_MA10'] = SMAIndicator(df['OBV'], window=10).sma_indicator()
        df['MFI'] = MFIIndicator(df['High'], df['Low'], df['Close'], df['Volume'], window=14).money_flow_index()

        # 布林通道
        bb = BollingerBands(close=df['Close'], window=20, window_dev=2)
        df['BB_High'] = bb.bollinger_hband()
        df['BB_Low'] = bb.bollinger_lband()
        df['BB_Width'] = (df['BB_High'] - df['BB_Low']) / df['MA20']

        latest = df.iloc[-1]; prev = df.iloc[-2]; price = float(latest['Close'])
        vol_ratio = float(latest['Volume'] / latest['Vol_MA5']) if latest['Vol_MA5'] > 0 else 0
        rsi = float(latest['RSI'])
        
        # 7. 均線乖離率 (Bias Ratio)
        bias_20 = (price - latest['MA20']) / latest['MA20'] * 100
        
        # 11. 大戶持有成本 (最大量日均價)
        recent_20 = df.iloc[-20:]
        max_vol_date = recent_20['Volume'].idxmax()
        big_player_cost = float((recent_20.loc[max_vol_date]['Open'] + recent_20.loc[max_vol_date]['Close']) / 2)
        
        score = 0; signals = []; is_selected = False; bb_status = "一般"

        # === 策略引擎 ===
        if strategy_mode == "🚀 短線噴射 (飆股)":
            if vol_ratio > 1.5: score += 25; signals.append("爆量")
            if price > latest['BB_High']: score += 25; signals.append("布林突破")
            if latest['BB_Width'] < 0.15: score += 10; signals.append("壓縮")
            if latest['MACD_Hist'] > 0 and latest['MACD_Hist'] > df['MACD_Hist'].iloc[-2]: score += 20; signals.append("MACD翻紅")
            if bias_20 > 10: signals.append("乖離過大")
            
            if (price > latest['BB_High'] or vol_ratio > 1.5) and score >= 60: is_selected = True
            if price > latest['BB_High']: bb_status = "🚀 突破噴出"

        elif strategy_mode == "🌊 波段成長 (趨勢)":
            if latest['MA5'] > latest['MA20'] > latest['MA60']: score += 30; signals.append("均線多排")
            if latest['OBV'] > latest['OBV_MA10']: score += 20; signals.append("籌碼吸納")
            if latest['MACD'] > latest['MACD_Signal']: score += 20; signals.append("MACD黃金交叉")
            if price > latest['MA20']: score += 10
            
            if latest['MA5'] > latest['MA20'] and score >= 60: is_selected = True

        elif strategy_mode == "💎 長線價值 (低接)":
            if abs(price - latest['MA20']) / latest['MA20'] < 0.03: score += 30; signals.append("回測月線")
            if 40 <= rsi <= 60: score += 20
            if bias_20 < -5: score += 20; signals.append("負乖離超跌")
            
            if price > latest['MA60'] and rsi < 70 and score >= 50: is_selected = True

        action = "觀察"
        if score >= 80: action = "🔥 強力買進"
        elif score >= 60: action = "✅ 建議佈局"
        
        if is_selected:
            return {
                "代號": ticker, "名稱": get_stock_name(ticker), "現價": price,
                "漲跌幅%": float((price - prev['Close']) / prev['Close'] * 100),
                "總分": score, "RSI": rsi, "相對量能": vol_ratio, "MFI": float(latest['MFI']),
                "BB寬度": float(latest['BB_Width']), "布林型態": bb_status,
                "MACD": "多頭" if latest['MACD'] > latest['MACD_Signal'] else "空頭", # 4. MACD
                "乖離率": round(bias_20, 2), # 7. 乖離率
                "訊號": signals, "建議": action, "History": df, 
                "主力成本": big_player_cost, "支撐價": float(latest['MA20'])
            }
        return None
    except: return None

# --- 繪圖函數 (新增 MACD) ---
def plot_gauge(value, title, thresholds=[30, 70]):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value, title={'text': title, 'font': {'size': 18, 'color': '#333'}},
        number={'font': {'size': 36}},
        gauge={'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#666"},
               'bar': {'color': "#222", 'thickness': 0.6}, 'bgcolor': "white", 'borderwidth': 1, 'bordercolor': "#ddd",
               'steps': [{'range': [0, thresholds[0]], 'color': "#ffcdd2"}, {'range': [thresholds[0], thresholds[1]], 'color': "#fff9c4"}, {'range': [thresholds[1], 100], 'color': "#c8e6c9"}],
               'threshold': {'line': {'color': "#d32f2f", 'width': 4}, 'thickness': 0.75, 'value': value}}))
    fig.update_layout(height=250, margin=dict(l=30, r=30, t=50, b=10), paper_bgcolor="rgba(0,0,0,0)", font={'family': "Arial"})
    return fig

def plot_chart(data):
    df = data['History']; name = data['名稱']
    # 增加一個 subplot 給 MACD
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, row_heights=[0.5, 0.15, 0.15, 0.2], 
                        subplot_titles=(f"{name} 走勢", "成交量", "MACD", "OBV 籌碼"))
    
    # K線 & MA
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='blue', width=1), name='月線'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_High'], line=dict(color='gray', width=1, dash='dot'), name='布林上'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Low'], line=dict(color='gray', width=1, dash='dot'), name='布林下'), row=1, col=1)
    
    # 量
    colors = ['red' if r['Open'] < r['Close'] else 'green' for i, r in df.iterrows()]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='量'), row=2, col=1)
    
    # MACD
    colors_macd = ['red' if v > 0 else 'green' for v in df['MACD_Hist']]
    fig.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], marker_color=colors_macd, name='MACD柱'), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], line=dict(color='orange', width=1), name='DIF'), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], line=dict(color='blue', width=1), name='DEA'), row=3, col=1)
    
    # OBV
    fig.add_trace(go.Scatter(x=df.index, y=df['OBV'], line=dict(color='purple', width=2), name='OBV'), row=4, col=1)
    
    fig.update_layout(height=900, xaxis_rangeslider_visible=False, showlegend=True, margin=dict(l=10,r=10,t=30,b=10))
    return fig

# --- 主程式介面 ---
st.sidebar.header("🦅 V14.0 戰情室")
strategy_mode = st.sidebar.radio("🎯 選擇策略", ("🚀 短線噴射 (飆股)", "🌊 波段成長 (趨勢)", "💎 長線價值 (低接)"), index=1)
selected_sectors = st.sidebar.multiselect("板塊篩選", list(STOCK_DB.keys()), default=["🔥 熱門 ETF", "💻 半導體/AI"])
strict_mode = st.sidebar.checkbox("嚴格模式", value=False)

st.title("🦅 台股 AI 戰情室 V14.0 (12大指標版)")

# 1. 顯示總經數據 (Fed/利率)
rate, delta = get_macro_data()
st.metric("🇺🇸 美國 10 年期公債殖利率 (無風險利率)", f"{rate:.2f}%", f"{delta:.2f}", delta_color="inverse")

if 'scan_result_v14' not in st.session_state: st.session_state.scan_result_v14 = None

if st.sidebar.button("🚀 執行全方位掃描", type="primary"):
    scan_list = []
    for sector in selected_sectors: scan_list.extend(list(STOCK_DB[sector].keys()))
    
    total = len(scan_list)
    st.toast(f"執行【{strategy_mode}】運算，包含 MACD/乖離/估值分析...", icon="🦅")
    
    bar = st.progress(0); res = []
    for i, t in enumerate(scan_list):
        d = analyze_stock_strategy(t, strategy_mode)
        if d: res.append(d)
        bar.progress((i+1)/total)
    
    bar.empty()
    if res:
        st.session_state.scan_result_v14 = pd.DataFrame(res).sort_values(by="總分", ascending=False)
        st.success(f"完成！找到 {len(res)} 檔標的。")
    else:
        st.warning("無符合標的。")

# --- Tabs ---
tab1, tab2 = st.tabs(["📋 篩選結果", "🔬 12大指標深度透視"])

with tab1:
    if st.session_state.scan_result_v14 is not None:
        df = st.session_state.scan_result_v14
        def style_rows(row):
            action = row['建議']
            if "強力" in action: return ['background-color: #ffebee; color: #c62828; font-weight: bold']*len(row)
            return ['background-color: #f1f8e9; color: #33691e']*len(row)
        
        cols = ["代號", "名稱", "現價", "漲跌幅%", "總分", "相對量能", "MACD", "乖離率", "建議", "訊號"]
        if strategy_mode == "🚀 短線噴射 (飆股)": cols.insert(6, "布林型態")
        
        display_df = df.copy()
        display_df['訊號'] = display_df['訊號'].apply(lambda x: ", ".join(x))
        st.dataframe(display_df[cols].style.apply(style_rows, axis=1).format("{:.2f}", subset=["現價", "漲跌幅%", "總分", "乖離率"]), use_container_width=True, height=600)
    else: st.info("👈 請點擊「執行全方位掃描」。")

with tab2:
    c_search, c_or, c_sel = st.columns([3, 0.5, 3])
    with c_search: search_ticker = st.text_input("🔍 搜尋代號", "")
    with c_sel: 
        opts = ["請選擇..."] + ((st.session_state.scan_result_v14['代號'] + " - " + st.session_state.scan_result_v14['名稱']).tolist() if st.session_state.scan_result_v14 is not None else [])
        sel_opt = st.selectbox("從結果選擇:", opts)

    target = None
    if search_ticker: target = search_ticker.strip().upper(); target = target + ".TW" if target.isdigit() and len(target)==4 else target
    elif sel_opt != "請選擇...": target = sel_opt.split(" - ")[0]

    if target:
        with st.spinner(f"正在計算 12 大指標數據: {target}..."):
            data = analyze_stock_strategy(target, strategy_mode)
            if data:
                if data['名稱'] == target: data['名稱'] = get_name_online(target)
                
                # 取得基本面 & 相關性
                fund_data = None
                corr_data = (0, "N/A")
                if "00" not in target[:2]: 
                    fund_data = get_advanced_fundamentals_v14(target)
                    corr_data = calculate_correlation(target)

                st.markdown("---")
                st.subheader(f"📊 {data['名稱']} ({target}) 12指標戰情牆")
                
                # 儀表板
                with st.container():
                    g1, g2, g3 = st.columns(3)
                    with g1: st.plotly_chart(plot_gauge(data['總分'], f"{strategy_mode} 評分"), use_container_width=True)
                    with g2: st.plotly_chart(plot_gauge(data['RSI'], "RSI 動能"), use_container_width=True)
                    with g3: st.plotly_chart(plot_gauge(data['MFI'], "MFI 資金流"), use_container_width=True)

                # 12大指標矩陣
                st.markdown("### 🦅 12 大關鍵指標透視")
                
                # 第一排：基本面 (3, 8, 10)
                m1, m2, m3, m4 = st.columns(4)
                if fund_data:
                    m1.markdown(f"<div class='indicator-box'>EPS / 營收<br><br><span style='font-size:1.5em'>{fund_data['EPS(預估)']} / {fund_data['營收成長']}</span></div>", unsafe_allow_html=True)
                    m2.markdown(f"<div class='indicator-box'>本益比 (P/E)<br><br><span style='font-size:1.5em'>{fund_data['本益比']}</span></div>", unsafe_allow_html=True)
                    m3.markdown(f"<div class='indicator-box'>股價淨值比 (P/B)<br><br><span style='font-size:1.5em'>{fund_data['股價淨值比']}</span></div>", unsafe_allow_html=True)
                    m4.markdown(f"<div class='indicator-box'>內部人持股<br><br><span style='font-size:1.5em'>{fund_data['內部人持股']}</span></div>", unsafe_allow_html=True)
                else: st.warning("ETF 不適用基本面指標")

                # 第二排：技術與籌碼 (4, 5, 7, 11)
                st.markdown("")
                t1, t2, t3, t4 = st.columns(4)
                t1.markdown(f"<div class='indicator-box'>MACD 趨勢<br><br><span style='font-size:1.5em'>{data['MACD']}</span></div>", unsafe_allow_html=True)
                t2.markdown(f"<div class='indicator-box'>均線乖離率<br><br><span style='font-size:1.5em'>{data['乖離率']}%</span></div>", unsafe_allow_html=True)
                t3.markdown(f"<div class='indicator-box'>大戶持有成本<br><br><span style='font-size:1.5em'>{data['主力成本']:.2f}</span></div>", unsafe_allow_html=True)
                t4.markdown(f"<div class='indicator-box'>籌碼集中 (OBV)<br><br><span style='font-size:1.5em'>{'🔥 吸籌' if '吸籌' in ','.join(data['訊號']) else '一般'}</span></div>", unsafe_allow_html=True)

                # 第三排：宏觀與外連 (1, 6, 9, 12)
                st.markdown("")
                o1, o2, o3, o4 = st.columns(4)
                o1.markdown(f"<div class='indicator-box'>美股連動 ({corr_data[1]})<br><br><span style='font-size:1.5em'>{corr_data[0]:.2f}</span></div>", unsafe_allow_html=True)
                o2.markdown(f"<div class='indicator-box'>Fed 利率環境<br><br><span style='font-size:1.5em'>{rate:.2f}%</span></div>", unsafe_allow_html=True)
                
                # 6. 融資融券 & 12. 外資動向 (外連)
                cl_t = target.replace(".TW", "").replace(".TWO", "")
                with o3:
                    st.markdown("<div class='indicator-box'>融資融券餘額</div>", unsafe_allow_html=True)
                    st.link_button("📊 查看信用交易 (Yahoo)", f"https://tw.stock.yahoo.com/quote/{cl_t}/margin-trading", use_container_width=True)
                with o4:
                    st.markdown("<div class='indicator-box'>外資/投信動向</div>", unsafe_allow_html=True)
                    st.link_button("⚖️ 查看法人買賣 (Goodinfo)", f"https://goodinfo.tw/tw/StockDetail.asp?STOCK_ID={cl_t}", use_container_width=True)

                # 估值紅綠燈
                if fund_data:
                    st.markdown("### 💰 估值區間")
                    vp = fund_data
                    st.markdown(f"""
                        <div style='background-color:#e3f2fd; padding:10px; border-radius:10px; text-align:center; color:#0d47a1;'>
                            便宜價: <b>{vp['便宜價']}</b> ◀ 現價: <b>{data['現價']}</b> ▶ 昂貴價: <b>{vp['昂貴價']}</b>
                        </div>
                    """, unsafe_allow_html=True)

                # 圖表區
                st.plotly_chart(plot_chart(data), use_container_width=True)
                
            else: st.error("查無資料。")
