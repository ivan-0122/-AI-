import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from ta.trend import SMAIndicator
from ta.momentum import RSIIndicator
from ta.volume import OnBalanceVolumeIndicator, MFIIndicator
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 頁面設定 ---
st.set_page_config(page_title="台股 AI 戰情室 V9.0", layout="wide", page_icon="🦅")

# --- CSS 優化 ---
st.markdown("""
<style>
    .metric-card {
        background-color: #ffffff;
        border-left: 5px solid #ff4b4b;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 10px;
    }
    .analysis-box {
        background-color: #e8f5e9;
        border-left: 5px solid #2e7d32;
        padding: 15px;
        margin-top: 10px;
        margin-bottom: 20px;
        border-radius: 5px;
        font-size: 1.05em;
    }
    .warning-box {
        background-color: #ffebee;
        border-left: 5px solid #c62828;
        padding: 15px;
        margin-top: 10px;
        margin-bottom: 20px;
        border-radius: 5px;
        font-size: 1.05em;
    }
</style>
""", unsafe_allow_html=True)

# --- 超級資料庫 (約230檔) ---
STOCK_DB = {
    "🔥 熱門 ETF (規模 Top 30)": {
        "0050.TW": "元大台灣50", "0056.TW": "元大高股息", "00878.TW": "國泰永續高股息", 
        "00929.TW": "復華台灣科技優息", "00919.TW": "群益台灣精選高息", "00940.TW": "元大台灣價值高息",
        "006208.TW": "富邦台50", "00713.TW": "元大台灣高息低波", "00881.TW": "國泰台灣5G+", 
        "00679B.TW": "元大美債20年", "00687B.TW": "國泰20年美債", "00939.TW": "統一台灣高息動能",
        "00830.TW": "國泰費城半導體", "00632R.TW": "元大台灣50反1", "00915.TW": "凱基優選高股息30",
        "00918.TW": "大華優利高填息30", "00692.TW": "富邦公司治理", "006203.TW": "元大MSCI台灣",
        "00751B.TW": "元大AAA至A公司債", "00772B.TW": "中信高評級公司債", "00882.TW": "中信中國高股息",
        "00631L.TW": "元大台灣50正2", "00662.TW": "富邦NASDAQ", "00646.TW": "元大S&P500",
        "00891.TW": "中信關鍵半導體", "00892.TW": "富邦台灣半導體", "00922.TW": "國泰台灣領袖50",
        "00923.TW": "群益台灣ESG低碳", "0051.TW": "元大中型100", "00733.TW": "富邦臺灣中小"
    },
    "💻 半導體/AI 供應鏈": {
        "2330.TW": "台積電", "2454.TW": "聯發科", "2317.TW": "鴻海", "2382.TW": "廣達", "3231.TW": "緯創",
        "2303.TW": "聯電", "2308.TW": "台達電", "3711.TW": "日月光", "2379.TW": "瑞昱", "3034.TW": "聯詠",
        "3661.TW": "世芯-KY", "3443.TW": "創意", "6669.TW": "緯穎", "2357.TW": "華碩", "2356.TW": "英業達",
        "2376.TW": "技嘉", "2301.TW": "光寶科", "3035.TW": "智原", "3037.TW": "欣興", "3017.TW": "奇鋐",
        "3324.TW": "雙鴻", "3044.TW": "健鼎", "6274.TW": "台燿", "8358.TW": "金居", "2383.TW": "台光電",
        "2449.TW": "京元電", "6239.TW": "力成", "3260.TWO": "威剛", "8299.TWO": "群聯", "2408.TW": "南亞科",
        "3529.TW": "力旺", "5274.TW": "信驊", "4966.TW": "譜瑞-KY", "6415.TW": "矽力-KY", "6770.TW": "力積電",
        "3006.TW": "晶豪科", "2344.TW": "華邦電", "3189.TW": "景碩", "8046.TW": "南電", "3105.TWO": "穩懋",
        "2368.TW": "金像電", "6213.TW": "聯茂", "5483.TWO": "中美晶", "6488.TW": "環球晶"
    },
    "⚡ 重電/綠能/網通": {
        "1513.TW": "中興電", "1519.TW": "華城", "1503.TW": "士電", "1504.TW": "東元", "1609.TW": "大亞",
        "2345.TW": "智邦", "5388.TWO": "中磊", "6285.TW": "啟碁", "3704.TW": "合勤控", "2332.TW": "友訊",
        "9958.TW": "世紀鋼", "3708.TW": "上緯投控", "6806.TW": "森崴能源", "6443.TW": "元晶", "6477.TW": "安集",
        "4919.TW": "新唐", "4958.TW": "臻鼎-KY", "2455.TW": "全新", "2498.TW": "宏達電"
    },
    "💰 金融/控股": {
        "2881.TW": "富邦金", "2882.TW": "國泰金", "2891.TW": "中信金", "2886.TW": "兆豐金", "5880.TW": "合庫金",
        "2884.TW": "玉山金", "2892.TW": "第一金", "2880.TW": "華南金", "2885.TW": "元大金", "5876.TW": "上海商銀",
        "2890.TW": "永豐金", "2883.TW": "開發金", "2887.TW": "台新金", "5871.TW": "中租-KY", "2834.TW": "臺企銀",
        "2812.TW": "台中銀", "2888.TW": "新光金", "2809.TW": "京城銀", "2801.TW": "彰銀", "6005.TW": "群益證"
    },
    "🚢 航運/汽車/原物料": {
        "2603.TW": "長榮", "2609.TW": "陽明", "2615.TW": "萬海", "2618.TW": "長榮航", "2610.TW": "華航",
        "2606.TW": "裕民", "2637.TW": "慧洋-KY", "2605.TW": "新興", "2612.TW": "中航", "5608.TW": "四維航",
        "2002.TW": "中鋼", "2014.TW": "中鴻", "2027.TW": "大成鋼", "1605.TW": "華新", "1101.TW": "台泥",
        "1102.TW": "亞泥", "1301.TW": "台塑", "1303.TW": "南亞", "1326.TW": "台化", "6505.TW": "台塑化",
        "2207.TW": "和泰車", "2201.TW": "裕隆", "2204.TW": "中華", "9904.TW": "寶成", "9910.TW": "豐泰",
        "9921.TW": "巨大", "9914.TW": "美利達"
    },
    "📱 光電/面板/零組件": {
        "3008.TW": "大立光", "3406.TW": "玉晶光", "2409.TW": "友達", "3481.TW": "群創", "6116.TW": "彩晶",
        "2327.TW": "國巨", "2492.TW": "華新科", "2428.TW": "興勤", "6209.TW": "今國光", "4915.TW": "致伸",
        "4938.TW": "和碩", "2353.TW": "宏碁", "2324.TW": "仁寶", "3293.TWO": "鈊象", "3532.TW": "台勝科",
        "6409.TW": "旭隼", "2395.TW": "研華", "2059.TW": "川湖", "3533.TW": "嘉澤"
    },
    "🛍️ 生活/生技/其他": {
        "2912.TW": "統一超", "5903.TW": "全家", "1216.TW": "統一", "1201.TW": "味全", "1227.TW": "佳格",
        "8454.TW": "富邦媒", "2412.TW": "中華電", "3045.TW": "台灣大", "4904.TW": "遠傳", "9945.TW": "潤泰新",
        "2542.TW": "興富發", "1722.TW": "台肥", "1760.TW": "寶齡富錦", "4128.TWO": "中天", "4743.TWO": "合一",
        "1707.TW": "葡萄王", "1795.TW": "美時", "4105.TWO": "東洋", "3257.TWO": "虹冠電"
    }
}

# 扁平化資料庫以供搜尋使用
FLAT_STOCK_DB = {}
for sector, stocks in STOCK_DB.items():
    for ticker, name in stocks.items():
        FLAT_STOCK_DB[ticker] = name

# --- 輔助函數 ---
def get_stock_name(ticker):
    return FLAT_STOCK_DB.get(ticker, ticker.replace(".TW", ""))

def get_name_online(ticker):
    name = FLAT_STOCK_DB.get(ticker)
    if name: return name
    try:
        t = yf.Ticker(ticker)
        return t.info.get('longName', ticker)
    except: return ticker

def get_forecast_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return info.get('forwardEps', None), info.get('targetMeanPrice', None)
    except: return None, None

# --- 核心分析邏輯 (新增主力成本與支撐) ---
def analyze_stock(ticker, strict_mode=False):
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if len(df) < 60: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        # 指標計算
        df['MA5'] = SMAIndicator(df['Close'], window=5).sma_indicator()
        df['MA20'] = SMAIndicator(df['Close'], window=20).sma_indicator()
        df['MA60'] = SMAIndicator(df['Close'], window=60).sma_indicator()
        df['RSI'] = RSIIndicator(df['Close'], window=14).rsi()
        df['Vol_MA5'] = SMAIndicator(df['Volume'], window=5).sma_indicator()
        df['OBV'] = OnBalanceVolumeIndicator(df['Close'], df['Volume']).on_balance_volume()
        df['OBV_MA10'] = SMAIndicator(df['OBV'], window=10).sma_indicator()
        df['MFI'] = MFIIndicator(df['High'], df['Low'], df['Close'], df['Volume'], window=14).money_flow_index()

        latest = df.iloc[-1]
        prev = df.iloc[-2]
        price = float(latest['Close'])
        
        # --- 計算主力成本與支撐 ---
        # 1. 支撐價：使用 20日均線 (生命線)
        support_price = float(latest['MA20'])
        
        # 2. 主力關鍵價：過去 20 天內「最大成交量」那天的均價 (Open+Close)/2
        recent_20_days = df.iloc[-20:]
        max_vol_date = recent_20_days['Volume'].idxmax()
        max_vol_row = recent_20_days.loc[max_vol_date]
        # 計算大量日的均價
        big_player_cost = float((max_vol_row['Open'] + max_vol_row['Close']) / 2)
        
        # 評分
        score = 0
        signals = []
        chip_status = "中性"

        if latest['MA5'] > latest['MA20'] > latest['MA60']: score += 30; signals.append("均線多排")
        elif price > latest['MA20']: score += 15
        
        vol_ratio = float(latest['Volume'] / latest['Vol_MA5']) if latest['Vol_MA5'] > 0 else 0
        threshold = 1.5 if strict_mode else 1.2
        if vol_ratio > threshold and price > prev['Close']: score += 20; signals.append(f"量增{round(vol_ratio,1)}倍")
        
        if latest['OBV'] > latest['OBV_MA10']:
            score += 20; chip_status = "主力吸籌"
            if latest['OBV'] > df['OBV'].iloc[-20:].max(): score += 10; signals.append("OBV創高"); chip_status = "🔥 主力拉抬"
        
        mfi = float(latest['MFI'])
        if 50 <= mfi <= 80: score += 10
        elif mfi > 80: signals.append("資金過熱")
        elif mfi < 20: signals.append("資金超賣")

        action = "觀望"
        if score >= 75: action = "🔥 強力買進"
        elif score >= 55: action = "📈 偏多操作"
        else: action = "📉 弱勢/賣出"

        return {
            "代號": ticker, "名稱": get_stock_name(ticker), "現價": price,
            "漲跌幅%": float((price - prev['Close']) / prev['Close'] * 100),
            "總分": score, "RSI": float(latest['RSI']), "MFI": mfi, "相對量能": vol_ratio,
            "籌碼狀態": chip_status, "訊號字串": ", ".join(signals), "訊號": signals,
            "建議": action, "History": df,
            "主力成本": big_player_cost, "支撐價": support_price # 新增欄位
        }
    except: return None

# --- 繪圖函數 ---
def plot_gauge(value, title, thresholds=[30, 70]):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title, 'font': {'size': 18, 'color': '#333'}},
        number={'font': {'size': 36}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#666"},
            'bar': {'color': "#222", 'thickness': 0.6},
            'bgcolor': "white",
            'borderwidth': 1,
            'bordercolor': "#ddd",
            'steps': [
                {'range': [0, thresholds[0]], 'color': "#ffcdd2"},
                {'range': [thresholds[0], thresholds[1]], 'color': "#fff9c4"},
                {'range': [thresholds[1], 100], 'color': "#c8e6c9"}
            ],
            'threshold': {'line': {'color': "#d32f2f", 'width': 4}, 'thickness': 0.75, 'value': value}
        }
    ))
    fig.update_layout(
        height=250, 
        margin=dict(l=30, r=30, t=50, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font={'family': "Arial"}
    )
    return fig

def plot_chip_chart(data):
    df = data['History']; name = data['名稱']
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[0.5, 0.25, 0.25],
                        subplot_titles=(f"{name} 走勢", "成交量", "OBV 主力籌碼"))
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線'), row=1, col=1)
    
    # 藍色線是技術支撐 (MA20)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='blue', width=1.5), name='月線支撐'), row=1, col=1)
    
    colors = ['red' if r['Open'] < r['Close'] else 'green' for i, r in df.iterrows()]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='量'), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['OBV'], line=dict(color='purple', width=2), name='OBV'), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['OBV_MA10'], line=dict(color='orange', width=1, dash='dot'), name='OBV均'), row=3, col=1)
    fig.update_layout(height=650, xaxis_rangeslider_visible=False, showlegend=True, margin=dict(l=10,r=10,t=30,b=10))
    return fig

def generate_summary(data):
    score = data['總分']; mfi = data['MFI']; signals = data['訊號']
    summary = f"**【{data['名稱']} ({data['代號']}) 戰情摘要】**\n\n"
    if score >= 75: summary += "🚀 **多頭強勢**：技術與籌碼同步轉強，OBV 顯示大戶心態偏多，順勢操作首選。"
    elif score >= 50: summary += "⚖️ **多方震盪**：股價沿均線整理，結構偏多但動能待爆發。"
    else: summary += "🌧️ **弱勢修正**：均線蓋頭反壓或量能不足，建議保守。"
    if "OBV創高" in signals: summary += " 留意 **OBV 創高**，大戶正積極掃貨。"
    if mfi > 80: summary += "\n\n⚠️ **風險提醒**：MFI 顯示市場**過熱**，短線恐回檔。"
    return summary

# --- 主程式介面 ---
st.sidebar.header("🦅 掃描設定 (大數據版)")
selected_sectors = st.sidebar.multiselect("選擇板塊", list(STOCK_DB.keys()), default=["🔥 熱門 ETF (規模 Top 30)", "💻 半導體/AI 供應鏈"])
strict_mode = st.sidebar.checkbox("嚴格篩選模式", value=False)
include_forecast_scan = st.sidebar.checkbox("載入財報預估 (ETF無此項)", value=False, help="勾選會大幅增加掃描時間，建議只在掃描少量股票時開啟。")

st.title("🦅 台股 AI 戰情室 V9.0")
st.caption("上市櫃熱門股約 230 檔 + 規模前 30 大 ETF | 新增：主力關鍵價與技術支撐")

if 'scan_result' not in st.session_state: st.session_state.scan_result = None

if st.sidebar.button("🚀 啟動掃描", type="primary"):
    scan_list = []
    for sector in selected_sectors: scan_list.extend(list(STOCK_DB[sector].keys()))
    
    total = len(scan_list)
    st.toast(f"開始掃描 {total} 檔標的，請耐心等候...", icon="⏳")
    
    bar = st.progress(0); status = st.empty(); res = []
    for i, t in enumerate(scan_list):
        status.text(f"({i+1}/{total}) 分析中: {get_stock_name(t)}...")
        d = analyze_stock(t, strict_mode)
        if d:
            if include_forecast_scan and "ETF" not in get_stock_name(t) and "00" not in t[:2]:
                f_eps, target_price = get_forecast_data(t)
                d['預估EPS'] = round(f_eps, 2) if f_eps else "-"
                d['目標價'] = target_price if target_price else "-"
                if isinstance(target_price, (int, float)) and target_price > 0:
                    upside = (target_price - d['現價']) / d['現價'] * 100
                    d['潛在空間%'] = round(upside, 1)
                else: d['潛在空間%'] = "-"
            else: d['預估EPS']="-"; d['目標價']="-"; d['潛在空間%']="-"
            res.append(d)
        bar.progress((i+1)/total)
    
    status.empty(); bar.empty()
    if res: st.session_state.scan_result = pd.DataFrame(res).sort_values(by="總分", ascending=False)

# --- Tabs ---
tab1, tab2 = st.tabs(["📋 掃描排行榜", "🔍 個股/ETF 籌碼透視"])

with tab1:
    if st.session_state.scan_result is not None:
        df = st.session_state.scan_result
        def style_rows(row):
            action = row['建議']
            if "強力" in action: return ['background-color: #ffebee; color: #c62828; font-weight: bold']*len(row)
            elif "偏多" in action: return ['background-color: #fff3e0; color: #ef6c00']*len(row)
            return ['background-color: #f1f8e9; color: #33691e']*len(row)
        st.dataframe(df.drop(columns=['History', '訊號']).style.apply(style_rows, axis=1).format("{:.2f}", subset=["現價", "漲跌幅%", "MFI", "主力成本", "支撐價"]), use_container_width=True, height=600)
    else: st.info("👈 請在側邊欄選擇板塊並點擊「啟動掃描」。")

with tab2:
    c_search, c_or, c_sel = st.columns([3, 0.5, 3])
    with c_search: search_ticker = st.text_input("🔍 輸入代號 (如 2330, 00929)", "")
    with c_or: st.markdown("<div style='text-align: center; padding-top: 30px;'>或</div>", unsafe_allow_html=True)
    with c_sel: 
        opts = ["請選擇..."] + ((st.session_state.scan_result['代號'] + " - " + st.session_state.scan_result['名稱']).tolist() if st.session_state.scan_result is not None else [])
        sel_opt = st.selectbox("從清單選擇:", opts)

    target = None
    if search_ticker: 
        t = search_ticker.strip().upper()
        target = t + ".TW" if t.isdigit() and len(t) == 4 else t
    elif sel_opt != "請選擇...": target = sel_opt.split(" - ")[0]

    if target:
        with st.spinner(f"分析 {target}..."):
            data = analyze_stock(target, strict_mode)
            if data:
                if data['名稱'] == target: data['名稱'] = get_name_online(target)
                if "00" not in target[:2]:
                    f_eps, tgt = get_forecast_data(target)
                    data['預估EPS'] = f_eps if f_eps else "N/A"
                    data['目標價'] = tgt if tgt else "N/A"
                else: data['預估EPS']="N/A (ETF)"; data['目標價']="N/A"

                st.markdown("---")
                st.subheader(f"📊 {data['名稱']} ({target}) 籌碼戰情")
                
                with st.container():
                    g1, g2, g3 = st.columns(3)
                    with g1: st.plotly_chart(plot_gauge(data['總分'], "AI 綜合評分", [40, 70]), use_container_width=True)
                    with g2: st.plotly_chart(plot_gauge(data['RSI'], "RSI 動能", [30, 70]), use_container_width=True)
                    with g3: st.plotly_chart(plot_gauge(data['MFI'], "MFI 資金流", [20, 80]), use_container_width=True)

                ct, cc = st.columns([1, 2])
                with ct:
                    box = "analysis-box" if data['總分'] >= 50 else "warning-box"
                    st.markdown(f'<div class="{box}">{generate_summary(data)}</div>', unsafe_allow_html=True)
                    st.metric("現價", data['現價'], f"{data['漲跌幅%']:.2f}%")
                    
                    # --- 新增：主力關鍵數據顯示 ---
                    col_key1, col_key2 = st.columns(2)
                    col_key1.metric("主力關鍵成本", f"{data['主力成本']:.2f}", help="過去20天內最大量當日的均價")
                    col_key2.metric("月線支撐價", f"{data['支撐價']:.2f}", help="20日移動平均線")
                    
                    st.divider()
                    c_f1, c_f2 = st.columns(2)
                    c_f1.metric("預估EPS", data['預估EPS'])
                    c_f2.metric("目標價", data['目標價'])
                with cc: st.plotly_chart(plot_chip_chart(data), use_container_width=True)
                
                st.markdown("---")
                l1, l2 = st.columns(2)
                cl_t = target.replace(".TW", "").replace(".TWO", "")
                l1.link_button("Yahoo 法人買賣超", f"https://tw.stock.yahoo.com/quote/{cl_t}/institutional-trading")
                l2.link_button("Goodinfo 主力進出", f"https://goodinfo.tw/tw/StockDetail.asp?STOCK_ID={cl_t}")
            else: st.error(f"無法取得 {target} 資料，請確認代號是否正確。")