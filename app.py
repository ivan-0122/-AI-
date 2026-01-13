import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests # 新增：爬蟲請求
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volume import OnBalanceVolumeIndicator, MFIIndicator
from ta.volatility import BollingerBands
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 頁面設定 ---
st.set_page_config(page_title="台股 AI 戰情室 V19.0", layout="wide", page_icon="🦅")

# --- CSS 優化 ---
st.markdown("""
<style>
    .metric-card { background-color: #ffffff; border-left: 5px solid #ff4b4b; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 10px; color: #000000; }
    .analysis-box { background-color: #e8f5e9; border-left: 5px solid #2e7d32; padding: 15px; margin-top: 10px; margin-bottom: 20px; border-radius: 5px; font-size: 1.05em; color: #1b5e20; }
    .warning-box { background-color: #ffebee; border-left: 5px solid #c62828; padding: 15px; margin-top: 10px; margin-bottom: 20px; border-radius: 5px; font-size: 1.05em; color: #b71c1c; }
    .indicator-box { background-color: #f3e5f5; border: 1px solid #ce93d8; padding: 10px; border-radius: 5px; text-align: center; color: #4a148c; font-weight: bold; font-size: 0.9em; height: 100%;}
    .chip-box { background-color: #e0f7fa; border: 1px solid #4dd0e1; padding: 10px; border-radius: 5px; text-align: center; color: #006064; font-weight: bold; font-size: 0.9em; height: 100%;}
    .stDataFrame th { color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- 資料庫 ---
STOCK_DB = {
    "💻 半導體權值": {"2330.TW": "台積電", "2454.TW": "聯發科", "2317.TW": "鴻海", "2303.TW": "聯電", "2308.TW": "台達電", "3711.TW": "日月光", "2379.TW": "瑞昱", "3034.TW": "聯詠", "3661.TW": "世芯-KY", "3443.TW": "創意", "6669.TW": "緯穎", "3035.TW": "智原", "3529.TW": "力旺", "5274.TW": "信驊", "3231.TW": "緯創", "2382.TW": "廣達", "2357.TW": "華碩", "2356.TW": "英業達", "2376.TW": "技嘉", "2324.TW": "仁寶"},
    "⚡ 重電/綠能": {"1519.TW": "華城", "1513.TW": "中興電", "1503.TW": "士電", "1504.TW": "東元", "1514.TW": "亞力", "1609.TW": "大亞", "1605.TW": "華新", "1618.TW": "合機", "1616.TW": "億泰", "6806.TW": "森崴能源", "9958.TW": "世紀鋼", "3708.TW": "上緯投控", "6443.TW": "元晶"},
    "🖥️ PCB/載板": {"3037.TW": "欣興", "8046.TW": "南電", "3189.TW": "景碩", "2368.TW": "金像電", "3044.TW": "健鼎", "6274.TW": "台燿", "2383.TW": "台光電", "6213.TW": "聯茂", "4958.TW": "臻鼎-KY", "2313.TW": "華通", "5469.TW": "瀚宇博", "8358.TW": "金居", "6269.TW": "台郡", "2355.TW": "敬鵬"},
    "🤖 機器人/散熱": {"3017.TW": "奇鋐", "3324.TW": "雙鴻", "3483.TW": "力致", "2421.TW": "建準", "2354.TW": "鴻準", "2059.TW": "川湖", "2049.TW": "上銀", "1590.TW": "亞德客-KY", "2359.TW": "所羅門", "6188.TW": "廣明", "8374.TW": "羅昇", "2464.TW": "盟立"},
    "📡 網通/低軌": {"2345.TW": "智邦", "5388.TWO": "中磊", "6285.TW": "啟碁", "3704.TW": "合勤控", "3596.TW": "智易", "4977.TW": "眾達-KY", "4906.TW": "正文", "3062.TW": "建漢", "2314.TW": "台揚", "3081.TW": "聯亞", "4979.TW": "華星光"},
    "💰 金融/控股": {"2881.TW": "富邦金", "2882.TW": "國泰金", "2891.TW": "中信金", "2886.TW": "兆豐金", "5880.TW": "合庫金", "2884.TW": "玉山金", "5871.TW": "中租-KY", "2892.TW": "第一金", "2885.TW": "元大金", "2890.TW": "永豐金", "2883.TW": "開發金", "2887.TW": "台新金", "2834.TW": "臺企銀", "2809.TW": "京城銀"},
    "🚢 航運/傳產": {"2603.TW": "長榮", "2609.TW": "陽明", "2615.TW": "萬海", "2618.TW": "長榮航", "2610.TW": "華航", "2606.TW": "裕民", "2637.TW": "慧洋-KY", "2002.TW": "中鋼", "1101.TW": "台泥", "1301.TW": "台塑", "1303.TW": "南亞", "1326.TW": "台化", "6505.TW": "台塑化", "2207.TW": "和泰車", "2912.TW": "統一超", "1216.TW": "統一", "2201.TW": "裕隆"},
    "📱 光電/其他": {"3008.TW": "大立光", "3406.TW": "玉晶光", "2409.TW": "友達", "3481.TW": "群創", "2327.TW": "國巨", "2492.TW": "華新科", "3260.TWO": "威剛", "8299.TWO": "群聯", "2395.TW": "研華", "8454.TW": "富邦媒", "2412.TW": "中華電", "3045.TW": "台灣大", "4904.TW": "遠傳"}
}
FLAT_STOCK_DB = {ticker: name for sector, stocks in STOCK_DB.items() for ticker, name in stocks.items()}

def get_stock_name(ticker): return FLAT_STOCK_DB.get(ticker, ticker.replace(".TW", ""))
def get_name_online(ticker):
    name = FLAT_STOCK_DB.get(ticker)
    if name: return name
    try: return yf.Ticker(ticker).info.get('longName', ticker)
    except: return ticker

def get_macro_data():
    try:
        tnx = yf.Ticker("^TNX"); hist = tnx.history(period="5d")
        return hist['Close'].iloc[-1], hist['Close'].iloc[-1] - hist['Close'].iloc[-2]
    except: return 0, 0

def calculate_correlation(ticker):
    try:
        benchmark = "^SOX" if any(x in ticker for x in ["2330","2454","2379","2303"]) else "^GSPC"
        stock = yf.download(ticker, period="3mo", progress=False)['Close']
        bench = yf.download(benchmark, period="3mo", progress=False)['Close']
        df = pd.concat([stock, bench], axis=1).dropna()
        return df.iloc[:,0].corr(df.iloc[:,1]), benchmark
    except: return 0, "N/A"

# --- V19.0 新增: 大戶籌碼爬蟲 (抓取 HiStock) ---
def get_chip_data_histock(ticker):
    """
    爬取 HiStock 網站的集保分佈資料，抓取400張與1000張大戶持股比例。
    注意：這需要網路請求，速度較慢。
    """
    clean_ticker = ticker.replace(".TW", "").replace(".TWO", "")
    url = f"https://histock.tw/stock/large.aspx?no={clean_ticker}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        # 使用 Pandas 直接讀取網頁中的表格
        tables = pd.read_html(requests.get(url, headers=headers).text)
        
        # 通常 HiStock 的大戶持股表是網頁中的第一個或第二個表格
        # 我們尋找包含 "週別" 和 "1000張以上" 的表格
        target_df = None
        for df in tables:
            if "週別" in df.columns.astype(str) or "日期" in df.columns.astype(str):
                target_df = df
                break
        
        if target_df is not None and len(target_df) >= 2:
            # 整理資料
            # 假設表格欄位有: 期數, 日期, 1000張以上(%), 400張以上(%), ...
            # 我們需要 mapping 正確的欄位名稱 (網站可能會變，這裡做模糊比對)
            
            col_1000 = [c for c in target_df.columns if "1000" in str(c) and "%" in str(c)]
            col_400 = [c for c in target_df.columns if "400" in str(c) and "%" in str(c)]
            
            if col_1000 and col_400:
                latest = target_df.iloc[0] # 最新一週
                prev = target_df.iloc[1]   # 上一週
                
                val_1000 = float(latest[col_1000[0]])
                val_400 = float(latest[col_400[0]])
                
                diff_1000 = val_1000 - float(prev[col_1000[0]])
                diff_400 = val_400 - float(prev[col_400[0]])
                
                return {
                    "400張": val_400,
                    "400張增減": diff_400,
                    "1000張": val_1000,
                    "1000張增減": diff_1000,
                    "日期": latest[0] # 通常第一欄是日期
                }
    except Exception as e:
        # st.error(f"爬取失敗: {e}") # Debug用
        pass
        
    return None

# --- 基本面分析 ---
def get_advanced_fundamentals(ticker):
    try:
        info = yf.Ticker(ticker).info
        rev_growth = info.get('revenueGrowth')
        trailing_eps = info.get('trailingEps')
        forward_eps = info.get('forwardEps')
        target_price = info.get('targetMeanPrice')
        
        cheap_price = 0; fair_price = 0; expensive_price = 0
        valuation_method = "PE模型"
        base_eps = None
        if target_price and target_price > 0:
            valuation_method = "法人共識"
            fair_price = target_price
        elif forward_eps and forward_eps > 0: base_eps = forward_eps
        elif trailing_eps and trailing_eps > 0:
            base_eps = trailing_eps
            valuation_method = "PE模型(歷史)"
            
        if fair_price == 0 and base_eps:
            pe_mult = 15
            fair_price = base_eps * pe_mult
            
        if fair_price > 0:
            cheap_price = fair_price * 0.8
            expensive_price = fair_price * 1.2

        risks = []
        if info.get('operatingCashflow', 0) is not None and info.get('operatingCashflow', 0) < 0: risks.append("🔴 營業現金流為負")
        if info.get('grossMargins', 0) < 0.1: risks.append("🟠 毛利率過低")

        return {
            "營收成長": f"{round(rev_growth*100, 2)}%" if rev_growth else "-",
            "EPS(預估)": round(forward_eps, 2) if forward_eps else "-",
            "本益比": round(info.get('forwardPE',0),2) if info.get('forwardPE') else "-",
            "股價淨值比": round(info.get('priceToBook',0),2) if info.get('priceToBook') else "-",
            "內部人持股": f"{round(info.get('heldPercentInsiders',0)*100,2)}%" if info.get('heldPercentInsiders') else "-",
            "便宜價": round(cheap_price, 2),
            "合理價": round(fair_price, 2),
            "昂貴價": round(expensive_price, 2),
            "估價法": valuation_method,
            "風險": risks
        }
    except: return None

# --- 核心分析 ---
def analyze_stock_strategy(ticker, strategy_mode, strict_mode, bypass_filter=False):
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if len(df) < 60: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        df['MA5'] = SMAIndicator(df['Close'], 5).sma_indicator()
        df['MA20'] = SMAIndicator(df['Close'], 20).sma_indicator()
        df['MA60'] = SMAIndicator(df['Close'], 60).sma_indicator()
        df['RSI'] = RSIIndicator(df['Close'], 14).rsi()
        df['Vol_MA5'] = SMAIndicator(df['Volume'], 5).sma_indicator()
        macd = MACD(df['Close']); df['MACD'] = macd.macd(); df['MACD_Signal'] = macd.macd_signal(); df['MACD_Hist'] = macd.macd_diff()
        df['OBV'] = OnBalanceVolumeIndicator(df['Close'], df['Volume']).on_balance_volume()
        df['OBV_MA10'] = SMAIndicator(df['OBV'], 10).sma_indicator()
        df['MFI'] = MFIIndicator(df['High'], df['Low'], df['Close'], df['Volume'], 14).money_flow_index()
        bb = BollingerBands(df['Close']); df['BB_High'] = bb.bollinger_hband(); df['BB_Low'] = bb.bollinger_lband(); df['BB_Width'] = (df['BB_High']-df['BB_Low'])/df['MA20']

        latest = df.iloc[-1]; price = float(latest['Close'])
        vol_ratio = float(latest['Volume']/latest['Vol_MA5']) if latest['Vol_MA5']>0 else 0
        bias_20 = (price - latest['MA20'])/latest['MA20']*100
        
        recent_20 = df.iloc[-20:]
        max_vol_idx = recent_20['Volume'].idxmax()
        big_player_cost = float((recent_20.loc[max_vol_idx]['Open'] + recent_20.loc[max_vol_idx]['Close']) / 2)

        score = 0; signals = []; is_selected = False; bb_status = "一般"

        if strategy_mode == "🚀 短線噴射 (飆股)":
            if vol_ratio > 1.5: score+=25; signals.append("爆量")
            if price > latest['BB_High']: score+=25; signals.append("布林突破")
            if latest['BB_Width'] < 0.15: score+=10; signals.append("壓縮")
            if latest['MACD_Hist']>0 and latest['MACD_Hist']>df['MACD_Hist'].iloc[-2]: score+=20; signals.append("MACD翻紅")
            min_score = 75 if strict_mode else 60
            min_vol = 2.0 if strict_mode else 1.5
            if (price > latest['BB_High'] or vol_ratio > min_vol) and score >= min_score: is_selected = True
            if price > latest['BB_High']: bb_status = "🚀 突破噴出"

        elif strategy_mode == "🌊 波段成長 (趨勢)":
            if latest['MA5']>latest['MA20']>latest['MA60']: score+=30; signals.append("均線多排")
            if latest['OBV']>latest['OBV_MA10']: score+=20; signals.append("籌碼吸納")
            if latest['MACD']>latest['MACD_Signal']: score+=20; signals.append("MACD金叉")
            if price > latest['MA20']: score+=10
            min_score = 75 if strict_mode else 60
            if latest['MA5']>latest['MA20'] and score >= min_score: is_selected = True

        elif strategy_mode == "💎 長線價值 (低接)":
            if abs(price-latest['MA20'])/latest['MA20']<0.03: score+=30; signals.append("回測月線")
            if 40<=latest['RSI']<=60: score+=20
            if bias_20 < -5: score+=20; signals.append("負乖離超跌")
            min_score = 65 if strict_mode else 50
            if price > latest['MA60'] and latest['RSI'] < 70 and score >= min_score: is_selected = True

        action = "觀察"
        if score >= 80: action = "🔥 強力買進"
        elif score >= 60: action = "✅ 建議佈局"
        
        # 集保分佈表連結
        clean_ticker = ticker.replace(".TW", "").replace(".TWO", "")
        chip_link = f"https://goodinfo.tw/tw/EquityDistributionClassHis.asp?STOCK_ID={clean_ticker}"

        if is_selected or bypass_filter:
            status_note = "" if is_selected else "⚠️ 未入選 (不符策略)"
            return {
                "代號": ticker, "名稱": get_stock_name(ticker), "現價": price,
                "漲跌幅%": float((price - df['Close'].iloc[-2]) / df['Close'].iloc[-2] * 100),
                "總分": score, "RSI": float(latest['RSI']), "相對量能": vol_ratio, "MFI": float(latest['MFI']),
                "BB寬度": float(latest['BB_Width']), "布林型態": bb_status,
                "MACD": "多頭" if latest['MACD'] > latest['MACD_Signal'] else "空頭",
                "乖離率": round(bias_20, 2), "訊號": signals, "建議": action, "History": df, 
                "主力成本": big_player_cost, "支撐價": float(latest['MA20']), "狀態": status_note,
                "大戶籌碼": chip_link
            }
        return None
    except: return None

# --- 繪圖函數 ---
def plot_gauge(value, title):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value, title={'text': title, 'font': {'size': 18, 'color': '#333'}},
        number={'font': {'size': 36}},
        gauge={'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#666"},
               'bar': {'color': "#222", 'thickness': 0.6}, 'bgcolor': "white", 'borderwidth': 1, 'bordercolor': "#ddd",
               'steps': [{'range': [0, 30], 'color': "#ffcdd2"}, {'range': [30, 70], 'color': "#fff9c4"}, {'range': [70, 100], 'color': "#c8e6c9"}],
               'threshold': {'line': {'color': "#d32f2f", 'width': 4}, 'thickness': 0.75, 'value': value}}))
    fig.update_layout(height=250, margin=dict(l=30, r=30, t=50, b=10), paper_bgcolor="rgba(0,0,0,0)", font={'family': "Arial"})
    return fig

def plot_chart(data):
    df = data['History']; name = data['名稱']
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, row_heights=[0.5, 0.15, 0.15, 0.2], subplot_titles=(f"{name} 走勢", "成交量", "MACD", "OBV"))
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='blue', width=1), name='月線'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_High'], line=dict(color='gray', width=1, dash='dot'), name='布林上'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Low'], line=dict(color='gray', width=1, dash='dot'), name='布林下'), row=1, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=['red' if o<c else 'green' for o,c in zip(df['Open'],df['Close'])], name='量'), row=2, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], marker_color=['red' if v>0 else 'green' for v in df['MACD_Hist']], name='MACD柱'), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], line=dict(color='orange', width=1), name='DIF'), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], line=dict(color='blue', width=1), name='DEA'), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['OBV'], line=dict(color='purple', width=2), name='OBV'), row=4, col=1)
    fig.update_layout(height=900, xaxis_rangeslider_visible=False, showlegend=True, margin=dict(l=10,r=10,t=30,b=10))
    return fig

# --- 主程式介面 ---
st.sidebar.header("🦅 V19.0 大戶籌碼解鎖版")
strategy_mode = st.sidebar.radio("🎯 選擇策略", ("🚀 短線噴射 (飆股)", "🌊 波段成長 (趨勢)", "💎 長線價值 (低接)"), index=1)
all_sectors = list(STOCK_DB.keys())
selected_sectors = st.sidebar.multiselect("板塊篩選", all_sectors, default=all_sectors)
strict_mode = st.sidebar.checkbox("嚴格篩選模式", value=False)

st.title("🦅 台股 AI 戰情室 V19.0")
rate, delta = get_macro_data()
st.metric("🇺🇸 美國 10 年期公債殖利率", f"{rate:.2f}%", f"{delta:.2f}", delta_color="inverse")

if 'scan_result_v19' not in st.session_state: st.session_state.scan_result_v19 = None

if st.sidebar.button("🚀 執行全市場掃描", type="primary"):
    scan_list = []
    for sector in selected_sectors: scan_list.extend(list(STOCK_DB[sector].keys()))
    total = len(scan_list); bar = st.progress(0); res = []
    st.toast(f"掃描 {total} 檔個股中...", icon="🦅")
    
    for i, t in enumerate(scan_list):
        d = analyze_stock_strategy(t, strategy_mode, strict_mode, bypass_filter=False)
        if d: res.append(d)
        bar.progress((i+1)/total)
    bar.empty()
    
    if res:
        st.session_state.scan_result_v19 = pd.DataFrame(res).sort_values(by="總分", ascending=False)
        st.success(f"掃描完成！找到 {len(res)} 檔符合策略個股。")
    else: st.warning("無符合標的，請嘗試關閉嚴格模式。")

# --- Tabs ---
tab1, tab2 = st.tabs(["📋 篩選結果", "🔍 12大指標深度透視"])

with tab1:
    if st.session_state.scan_result_v19 is not None:
        df = st.session_state.scan_result_v19
        def style_rows(row):
            if "強力" in row['建議']: return ['background-color: #ffebee; color: #c62828; font-weight: bold']*len(row)
            return ['background-color: #f1f8e9; color: #33691e']*len(row)
        
        cols = ["代號", "名稱", "現價", "漲跌幅%", "總分", "主力成本", "大戶籌碼", "建議", "訊號"]
        if strategy_mode == "🚀 短線噴射 (飆股)": cols.insert(6, "布林型態")
        
        display_df = df.copy(); display_df['訊號'] = display_df['訊號'].apply(lambda x: ", ".join(x))
        st.dataframe(
            display_df[cols].style.apply(style_rows, axis=1).format("{:.2f}", subset=["現價", "漲跌幅%", "總分", "主力成本"]), 
            use_container_width=True, 
            height=600,
            column_config={
                "大戶籌碼": st.column_config.LinkColumn("集保籌碼", help="點擊查看Goodinfo籌碼分佈", display_text="查看增減")
            }
        )
    else: st.info("👈 請點擊「執行全市場掃描」。")

with tab2:
    c_search, c_or, c_sel = st.columns([3, 0.5, 3])
    with c_search: search_ticker = st.text_input("🔍 輸入任意代號 (如 2330)", "")
    with c_sel: 
        opts = ["請選擇..."] + ((st.session_state.scan_result_v19['代號'] + " - " + st.session_state.scan_result_v19['名稱']).tolist() if st.session_state.scan_result_v19 is not None else [])
        sel_opt = st.selectbox("或從結果選擇:", opts)

    target = None
    if search_ticker: target = search_ticker.strip().upper(); target = target + ".TW" if target.isdigit() and len(target)==4 else target
    elif sel_opt != "請選擇...": target = sel_opt.split(" - ")[0]

    if target:
        with st.spinner(f"正在分析 {target} 並爬取大戶籌碼..."):
            data = analyze_stock_strategy(target, strategy_mode, strict_mode, bypass_filter=True)
            if data:
                if data['名稱'] == target: data['名稱'] = get_name_online(target)
                fund_data = None; corr_data = (0, "N/A"); chip_data = None
                
                if "00" not in target[:2]:
