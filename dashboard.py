"""
Stories Coffee — Analytics Dashboard
Run: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re, os, io

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="Stories Coffee Analytics",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .block-container { padding-top: 1.5rem; }
    
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a1d2b 0%, #232738 100%);
        border: 1px solid #2a2d3e;
        border-radius: 12px;
        padding: 16px 20px;
    }
    div[data-testid="stMetric"] label { font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
    
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 20px;
        font-weight: 600;
    }
    
    h1 { letter-spacing: -0.5px; }
    h2, h3 { letter-spacing: -0.3px; }
    
    .insight-box {
        background: rgba(34,211,167,0.08);
        border-left: 3px solid #22D3A7;
        border-radius: 0 8px 8px 0;
        padding: 12px 16px;
        margin: 8px 0;
        font-size: 0.9rem;
    }
    .warning-box {
        background: rgba(239,68,68,0.08);
        border-left: 3px solid #EF4444;
        border-radius: 0 8px 8px 0;
        padding: 12px 16px;
        margin: 8px 0;
        font-size: 0.9rem;
    }
    .opportunity-box {
        background: rgba(245,158,66,0.08);
        border-left: 3px solid #F59E42;
        border-radius: 0 8px 8px 0;
        padding: 12px 16px;
        margin: 8px 0;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

COLORS = {
    'accent': '#22D3A7',
    'blue': '#3B82F6',
    'warm': '#F59E42',
    'red': '#EF4444',
    'purple': '#A78BFA',
    'teal': '#2DD4BF',
    'pink': '#F472B6',
}
PALETTE = ['#22D3A7', '#3B82F6', '#F59E42', '#A78BFA', '#EF4444', '#2DD4BF', '#F472B6', '#FBBF24', '#6366F1', '#10B981']


# ============================================================
# DATA PARSING
# ============================================================
def normalize_branch(name):
    if pd.isna(name): return name
    name = str(name).strip()
    name = re.sub(r'^Stories\s*[-]?\s*', '', name, flags=re.IGNORECASE).strip().title()
    fixes = {'Alay': 'Aley', 'Lau': 'LAU', '.': 'Closed/Temp', '': 'Closed/Temp'}
    return fixes.get(name, name)

def parse_num(val):
    if pd.isna(val): return 0.0
    try: return float(str(val).replace(',', '').strip())
    except: return 0.0

@st.cache_data
def load_data(f1_path, f2_path, f3_path, f4_path):
    """Parse all 4 CSV files and return structured DataFrames."""
    data = {}
    
    # ---- FILE 1: Monthly Sales ----
    with open(f1_path, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    
    lines = content.split('\n')
    branch_data = {}
    current_year = None
    section_months = None
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        parts = [p.strip().strip('"') for p in re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', line)]
        
        if 'Page ' in line or line.startswith('Stories,,,') or 'Comparative' in line or '22-Jan' in line:
            continue
        
        if 'January' in line or 'October' in line:
            if 'Total By Year' in line:
                section_months = ['October', 'November', 'December', 'Total By Year']
            elif 'January' in line:
                section_months = ['January','February','March','April','May','June','July','August','September']
            continue
        
        year_val = None
        branch_name = None
        data_start = None
        
        if parts[0] in ['2025', '2026']:
            current_year = int(parts[0])
            branch_name = parts[1] if len(parts) > 1 else None
            data_start = 2
        elif parts[0] == '' and len(parts) > 1 and parts[1]:
            branch_name = parts[1]
            data_start = 2
        else:
            continue
        
        if not branch_name or branch_name == 'Total': continue
        branch = normalize_branch(branch_name)
        
        if section_months is None:
            section_months = ['January','February','March','April','May','June','July','August','September']
        
        vals = []
        for p in parts[data_start:]:
            p_clean = p.replace(',', '').strip()
            if p_clean and p_clean not in ['Total By Year']:
                try: vals.append(float(p_clean))
                except: pass
        
        key = (current_year, branch)
        if key not in branch_data: branch_data[key] = {}
        for i, month in enumerate(section_months):
            if i < len(vals):
                branch_data[key][month] = vals[i]
    
    rows = []
    for (year, branch), months_dict in branch_data.items():
        row = {'Year': year, 'Branch': branch}
        row.update(months_dict)
        rows.append(row)
    
    df_monthly = pd.DataFrame(rows)
    df_monthly = df_monthly[df_monthly['Branch'] != 'Total']
    data['monthly'] = df_monthly
    
    # ---- FILE 4: Category Summary ----
    cat_records = []
    current_branch = None
    with open(f4_path, 'r', encoding='utf-8-sig') as f:
        for line in f:
            line = line.strip()
            if not line or 'Page ' in line or 'Theoretical' in line or '22-Jan' in line or line.startswith('Category,'): continue
            if 'Copyright' in line: continue
            
            parts = [p.strip().strip('"') for p in re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', line)]
            
            if parts[0].startswith('Stories') and (len(parts) < 3 or parts[1] == ''):
                current_branch = normalize_branch(parts[0])
                continue
            
            cat = parts[0].strip()
            if cat in ['BEVERAGES', 'FOOD'] or cat.startswith('Total By Branch'):
                qty = parse_num(parts[1])
                total_cost = parse_num(parts[4])
                cost_pct = parse_num(parts[5])
                total_profit = parse_num(parts[6])
                profit_pct = parse_num(parts[8])
                true_revenue = total_cost + total_profit
                
                label = cat if cat in ['BEVERAGES', 'FOOD'] else 'TOTAL'
                cat_records.append({
                    'Branch': current_branch, 'Category': label,
                    'Qty': qty, 'Revenue': true_revenue,
                    'Total Cost': total_cost, 'Cost %': cost_pct,
                    'Total Profit': total_profit, 'Profit %': profit_pct
                })
    
    data['category'] = pd.DataFrame(cat_records)
    
    # ---- FILE 2: Product Profitability ----
    product_records = []
    current_branch = current_service = current_category = current_section = None
    
    with open(f2_path, 'r', encoding='utf-8-sig') as f:
        for line in f:
            line = line.strip()
            if not line or 'Page ' in line or 'Theoretical' in line or '22-Jan' in line or line.startswith('Product Desc,'): continue
            if 'Copyright' in line: continue
            
            parts = [p.strip().strip('"') for p in re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', line)]
            name = parts[0].strip()
            
            if name.startswith('Stories') and (len(parts) < 3 or parts[1] == ''):
                current_branch = normalize_branch(name); continue
            if name in ['TAKE AWAY', 'TABLE']: current_service = name; continue
            if name in ['BEVERAGES', 'FOOD']: current_category = name; continue
            if 'SECTION' in name or name in ['HOT BAR SECTION', 'COLD BAR SECTION', 'DONUTS', 'FOOD SECTION', 'GRAB AND GO']:
                current_section = name; continue
            if name.startswith('Total By') or name.startswith('Total:'): continue
            
            if len(parts) >= 9:
                qty = parse_num(parts[1])
                total_cost = parse_num(parts[4])
                total_profit = parse_num(parts[6])
                profit_pct = parse_num(parts[8])
                
                if qty > 0:
                    product_records.append({
                        'Branch': current_branch, 'Service': current_service,
                        'Category': current_category, 'Section': current_section,
                        'Product': name, 'Qty': qty,
                        'Total Cost': total_cost, 'Total Profit': total_profit,
                        'Profit %': profit_pct, 'Revenue': total_cost + total_profit
                    })
    
    data['products'] = pd.DataFrame(product_records)
    
    # ---- FILE 3: Sales by Groups ----
    group_records = []
    current_branch = current_division = current_group = None
    
    with open(f3_path, 'r', encoding='utf-8-sig') as f:
        for line in f:
            line = line.strip()
            if not line or 'Page ' in line or 'Sales by Items' in line or '19-Jan' in line or line.startswith('Description,'): continue
            if 'Copyright' in line: continue
            
            parts = [p.strip().strip('"') for p in re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', line)]
            name = parts[0].strip()
            
            if name.startswith('Branch:'): current_branch = normalize_branch(name.replace('Branch:', '').strip()); continue
            if name.startswith('Division:'): current_division = name.replace('Division:', '').strip(); continue
            if name.startswith('Group:'): current_group = name.replace('Group:', '').strip(); continue
            if name.startswith('Total by'): continue
            
            if len(parts) >= 4:
                qty = parse_num(parts[2])
                total_amount = parse_num(parts[3])
                if qty > 0:
                    group_records.append({
                        'Branch': current_branch, 'Division': current_division,
                        'Group': current_group, 'Product': name,
                        'Qty': qty, 'Total Amount': total_amount
                    })
    
    data['groups'] = pd.DataFrame(group_records)
    
    return data

# ============================================================
# LOAD DATA — try uploaded files, then fall back to default paths
# ============================================================

# Check for uploaded files in sidebar
st.sidebar.markdown("## ☕ Stories Coffee")
st.sidebar.markdown("---")

use_upload = st.sidebar.checkbox("📂 Upload custom CSV files", value=False)

if use_upload:
    st.sidebar.markdown("Upload all 4 POS export files:")
    f1_up = st.sidebar.file_uploader("Monthly Sales (REP_S_00134)", type="csv", key="f1")
    f2_up = st.sidebar.file_uploader("Product Profitability (rep_s_00014)", type="csv", key="f2")
    f3_up = st.sidebar.file_uploader("Sales by Groups (rep_s_00191)", type="csv", key="f3")
    f4_up = st.sidebar.file_uploader("Category Summary (rep_s_00673)", type="csv", key="f4")
    
    if all([f1_up, f2_up, f3_up, f4_up]):
        # Save uploaded files temporarily
        os.makedirs('/tmp/stories_data', exist_ok=True)
        paths = {}
        for name, upfile in [('f1', f1_up), ('f2', f2_up), ('f3', f3_up), ('f4', f4_up)]:
            path = f'/tmp/stories_data/{name}.csv'
            with open(path, 'wb') as f:
                f.write(upfile.getvalue())
            paths[name] = path
        data = load_data(paths['f1'], paths['f2'], paths['f3'], paths['f4'])
        st.sidebar.success("✅ Files loaded successfully!")
    else:
        st.info("⬆️ Upload all 4 CSV files in the sidebar to proceed.")
        st.stop()
else:
    # Default file paths — adjust as needed
    default_paths = [
        ('data/REP_S_00134_SMRY.csv', 'data/rep_s_00014_SMRY.csv', 'data/rep_s_00191_SMRY-3.csv', 'data/rep_s_00673_SMRY.csv'),
        ('../data/REP_S_00134_SMRY.csv', '../data/rep_s_00014_SMRY.csv', '../data/rep_s_00191_SMRY-3.csv', '../data/rep_s_00673_SMRY.csv'),
        ('REP_S_00134_SMRY.csv', 'rep_s_00014_SMRY.csv', 'rep_s_00191_SMRY-3.csv', 'rep_s_00673_SMRY.csv'),
        ('/mnt/user-data/uploads/REP_S_00134_SMRY.csv', '/mnt/user-data/uploads/rep_s_00014_SMRY.csv', '/mnt/user-data/uploads/rep_s_00191_SMRY-3.csv', '/mnt/user-data/uploads/rep_s_00673_SMRY.csv'),
    ]
    
    loaded = False
    for p1, p2, p3, p4 in default_paths:
        if all(os.path.exists(p) for p in [p1, p2, p3, p4]):
            data = load_data(p1, p2, p3, p4)
            loaded = True
            break
    
    if not loaded:
        st.warning("📂 CSV files not found in default locations. Enable **Upload custom CSV files** in the sidebar.")
        st.stop()


# ============================================================
# PRECOMPUTE ANALYTICS
# ============================================================
df_monthly = data['monthly']
df_category = data['category']
df_products = data['products']
df_groups = data['groups']

df_2025 = df_monthly[df_monthly['Year'] == 2025].copy()
df_2026 = df_monthly[df_monthly['Year'] == 2026].copy()

months_order = ['January','February','March','April','May','June','July','August','September','October','November','December']
month_cols = [m for m in months_order if m in df_2025.columns]

# Monthly totals
monthly_totals = {m: df_2025[m].sum() for m in month_cols}
total_2025 = df_2025['Total By Year'].sum() if 'Total By Year' in df_2025.columns else sum(monthly_totals.values())

# Branch totals
df_branch_totals = df_category[df_category['Category'] == 'TOTAL'].sort_values('Total Profit', ascending=False).copy()
df_branch_totals['Profit per Unit'] = df_branch_totals['Total Profit'] / df_branch_totals['Qty']

# Category
df_bev = df_category[df_category['Category'] == 'BEVERAGES']
df_food = df_category[df_category['Category'] == 'FOOD']
bev_profit = df_bev['Total Profit'].sum()
food_profit = df_food['Total Profit'].sum()
bev_rev = df_bev['Revenue'].sum()
food_rev = df_food['Revenue'].sum()
bev_margin = bev_profit / bev_rev * 100 if bev_rev > 0 else 0
food_margin = food_profit / food_rev * 100 if food_rev > 0 else 0

# Products aggregated
df_prod_agg = df_products.groupby('Product').agg({'Qty': 'sum', 'Total Cost': 'sum', 'Total Profit': 'sum', 'Revenue': 'sum'}).reset_index()
df_prod_agg['Profit Margin'] = np.where(df_prod_agg['Revenue'] > 0, df_prod_agg['Total Profit'] / df_prod_agg['Revenue'] * 100, -999)
df_prod_agg['Avg Price'] = np.where(df_prod_agg['Qty'] > 0, df_prod_agg['Revenue'] / df_prod_agg['Qty'], 0)

df_core_products = df_prod_agg[(~df_prod_agg['Product'].str.startswith('ADD ')) & (df_prod_agg['Qty'] >= 100)].copy()

# Groups
df_group_summary = df_groups.groupby('Group').agg({'Qty': 'sum', 'Total Amount': 'sum'}).reset_index().sort_values('Total Amount', ascending=False)

# YoY
jan_2025 = df_2025[['Branch', 'January']].rename(columns={'January': 'Jan_2025'})
jan_2026 = df_2026[['Branch', 'January']].rename(columns={'January': 'Jan_2026'})
jan_compare = jan_2025.merge(jan_2026, on='Branch', how='inner')
jan_compare = jan_compare[(jan_compare['Jan_2025'] > 0) & (jan_compare['Jan_2026'] > 0)].copy()
jan_compare['YoY %'] = (jan_compare['Jan_2026'] - jan_compare['Jan_2025']) / jan_compare['Jan_2025'] * 100

# Bev/Food mix
df_mix = df_category[df_category['Category'].isin(['BEVERAGES', 'FOOD'])].pivot_table(
    index='Branch', columns='Category', values='Revenue', aggfunc='sum').fillna(0)
df_mix['Bev %'] = df_mix['BEVERAGES'] / (df_mix['BEVERAGES'] + df_mix['FOOD']) * 100
df_mix = df_mix.sort_values('Bev %', ascending=False).reset_index()


# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.markdown("### 📊 Navigation")
page = st.sidebar.radio("", ["📈 Overview", "📍 Branch Analysis", "☕ Product Deep-Dive", "🚀 Growth & Expansion", "🎯 Recommendations"], label_visibility="collapsed")

st.sidebar.markdown("---")
st.sidebar.markdown(
    "<div style='font-size:0.75rem; color:#888;'>"
    "Built for Stories Coffee Hackathon<br>"
    "Data: 2025 Full Year + Jan 2026<br>"
    "All values in arbitrary units"
    "</div>", unsafe_allow_html=True
)


# ============================================================
# PAGE: OVERVIEW
# ============================================================
if page == "📈 Overview":
    st.markdown("# ☕ Stories Coffee Analytics Dashboard")
    st.markdown("*Transforming POS data into actionable growth insights across 25 branches and 300+ products*")
    
    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("2025 Total Revenue", f"{total_2025/1e6:.1f}M", help="Arbitrary units")
    c2.metric("Active Branches", f"{df_monthly['Branch'].nunique()}", "11 new in 2025")
    c3.metric("Beverage Margin", f"{bev_margin:.1f}%", f"+{bev_margin-food_margin:.0f}pp vs Food")
    
    avg_yoy = jan_compare['YoY %'].mean() if len(jan_compare) > 0 else 0
    c4.metric("Jan YoY Change", f"{avg_yoy:.0f}%", "All branches declining", delta_color="inverse")
    
    st.markdown("---")
    
    # Seasonality
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📅 Monthly Revenue Seasonality (2025)")
        
        df_season = pd.DataFrame({
            'Month': [m[:3] for m in months_order],
            'Revenue': [monthly_totals.get(m, 0) for m in months_order]
        })
        
        peak_val = df_season['Revenue'].max()
        trough_val = df_season[df_season['Revenue'] > 0]['Revenue'].min()
        
        colors = ['#22D3A7' if v == peak_val else '#EF4444' if v == trough_val else '#3B82F6' for v in df_season['Revenue']]
        
        fig = go.Figure(go.Bar(
            x=df_season['Month'], y=df_season['Revenue'],
            marker_color=colors, marker_line_width=0,
            text=[f"{v/1e6:.1f}M" for v in df_season['Revenue']],
            textposition='outside', textfont_size=10,
        ))
        fig.update_layout(
            height=380, template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            yaxis_title='Revenue', yaxis_tickformat='.0s',
            margin=dict(t=20, b=40),
        )
        st.plotly_chart(fig, use_container_width=True)
        
        peak_month = months_order[df_season['Revenue'].tolist().index(peak_val)]
        trough_month = months_order[df_season['Revenue'].tolist().index(trough_val)]
        
        st.markdown(f"""
        <div class="insight-box">
        💡 <b>5.9× peak-to-trough ratio</b> — {peak_month} (peak) generates 5.9× the revenue of {trough_month} (trough). 
        June drops to just 17% of peak, driven by Ramadan/off-season effects. Summer surge Jul-Sep powered by cold beverages.
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("🥤 Beverages vs Food")
        
        fig = go.Figure(go.Pie(
            labels=['Beverages', 'Food'],
            values=[bev_profit, food_profit],
            hole=0.55,
            marker_colors=[COLORS['accent'], COLORS['warm']],
            textinfo='percent+label',
            textfont_size=12,
        ))
        fig.update_layout(
            height=280, template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=10, b=10, l=10, r=10),
            showlegend=False,
            annotations=[dict(text='Profit<br>Split', x=0.5, y=0.5, font_size=13, showarrow=False)]
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown(f"**Beverage Margin:** `{bev_margin:.1f}%`")
        st.markdown(f"**Food Margin:** `{food_margin:.1f}%`")
        st.markdown(f"**Gap:** `{bev_margin - food_margin:.0f} percentage points`")
        
        st.markdown("""
        <div class="opportunity-box">
        🎯 Every 1% shift toward beverages adds meaningful profit due to the 14pp margin gap.
        </div>
        """, unsafe_allow_html=True)
    
    # Product Groups
    st.markdown("---")
    st.subheader("📦 Top Product Groups by Revenue")
    
    df_gs = df_group_summary.head(12).copy()
    fig = px.bar(df_gs, x='Total Amount', y='Group', orientation='h',
                 color_discrete_sequence=[COLORS['blue']],
                 text=[f"{v/1e6:.1f}M" for v in df_gs['Total Amount']])
    fig.update_layout(
        height=400, template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis_title='Revenue', yaxis_title='', yaxis_autorange='reversed',
        margin=dict(t=20),
    )
    fig.update_traces(textposition='outside', textfont_size=10)
    st.plotly_chart(fig, use_container_width=True)


# ============================================================
# PAGE: BRANCH ANALYSIS
# ============================================================
elif page == "📍 Branch Analysis":
    st.markdown("# 📍 Branch Performance Analysis")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("🏆 Top Branch", df_branch_totals.iloc[0]['Branch'], f"{df_branch_totals.iloc[0]['Total Profit']/1e6:.1f}M profit")
    
    best_eff = df_branch_totals.sort_values('Profit per Unit', ascending=False).iloc[0]
    c2.metric("🎯 Most Efficient", best_eff['Branch'], f"{best_eff['Profit per Unit']:.0f} profit/unit")
    c3.metric("📊 Avg Margin", f"{df_branch_totals['Profit %'].mean():.1f}%", f"Range: {df_branch_totals['Profit %'].min():.1f}% – {df_branch_totals['Profit %'].max():.1f}%")
    
    st.markdown("---")
    
    # Sort control
    sort_metric = st.radio("Sort by:", ["Total Profit", "Profit Margin", "Profit per Unit", "Volume (Qty)"], horizontal=True)
    sort_map = {"Total Profit": "Total Profit", "Profit Margin": "Profit %", "Profit per Unit": "Profit per Unit", "Volume (Qty)": "Qty"}
    sort_col = sort_map[sort_metric]
    
    df_plot = df_branch_totals.sort_values(sort_col, ascending=True).tail(20)
    
    fig = px.bar(df_plot, x=sort_col, y='Branch', orientation='h',
                 color=sort_col, color_continuous_scale='tealgrn',
                 text=[f"{v:,.0f}" if sort_col != 'Profit %' else f"{v:.1f}%" for v in df_plot[sort_col]])
    fig.update_layout(
        height=600, template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis_title=sort_metric, yaxis_title='',
        margin=dict(t=20), coloraxis_showscale=False,
    )
    fig.update_traces(textposition='outside', textfont_size=10)
    st.plotly_chart(fig, use_container_width=True)
    
    # Two columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🥤 Beverage/Food Mix")
        
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Beverages %', y=df_mix['Branch'], x=df_mix['Bev %'], orientation='h', marker_color=COLORS['accent']))
        fig.add_trace(go.Bar(name='Food %', y=df_mix['Branch'], x=100 - df_mix['Bev %'], orientation='h', marker_color=COLORS['warm']))
        fig.update_layout(
            barmode='stack', height=550, template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis_title='Share (%)', yaxis_title='', yaxis_autorange='reversed',
            margin=dict(t=20), legend=dict(orientation='h', y=-0.1),
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📉 YoY January Change")
        
        if len(jan_compare) > 0:
            df_yoy_plot = jan_compare.sort_values('YoY %', ascending=True)
            colors_yoy = ['#EF4444' if v < -40 else '#F59E42' for v in df_yoy_plot['YoY %']]
            
            fig = go.Figure(go.Bar(
                y=df_yoy_plot['Branch'], x=df_yoy_plot['YoY %'],
                orientation='h', marker_color=colors_yoy,
                text=[f"{v:.1f}%" for v in df_yoy_plot['YoY %']],
                textposition='outside', textfont_size=10,
            ))
            fig.update_layout(
                height=550, template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                xaxis_title='YoY Change (%)', yaxis_title='',
                margin=dict(t=20),
            )
            fig.add_vline(x=0, line_dash="dash", line_color="white", opacity=0.3)
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("""
            <div class="warning-box">
            ⚠️ <b>Every established branch declined in January 2026.</b> Average drop: ~42%. 
            Saida (-66.5%) and LAU (-59.9%) need urgent investigation.
            </div>
            """, unsafe_allow_html=True)


# ============================================================
# PAGE: PRODUCT DEEP-DIVE
# ============================================================
elif page == "☕ Product Deep-Dive":
    st.markdown("# ☕ Product Profitability Deep-Dive")
    
    c1, c2, c3 = st.columns(3)
    top_prod = df_core_products.sort_values('Total Profit', ascending=False).iloc[0]
    c1.metric("🥇 #1 Product", top_prod['Product'][:25], f"{top_prod['Total Profit']/1e6:.1f}M profit")
    
    loss_total = df_core_products[df_core_products['Total Profit'] < 0]['Total Profit'].sum()
    c2.metric("🔴 Combo Losses", f"{loss_total/1e6:.0f}M", "10 loss-making toppings", delta_color="inverse")
    
    n_products = df_core_products['Product'].nunique()
    c3.metric("📦 Products Analyzed", f"{n_products}", f"{df_products['Product'].nunique()} total incl. modifiers")
    
    st.markdown("---")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🏆 Top Performers", "🔴 Loss Makers", "📊 Menu Matrix", "🔧 Modifiers"])
    
    with tab1:
        st.subheader("Top 15 Products by Gross Profit")
        
        top15 = df_core_products.sort_values('Total Profit', ascending=False).head(15)
        top15_plot = top15.sort_values('Total Profit', ascending=True)
        
        fig = px.bar(top15_plot, x='Total Profit', y='Product', orientation='h',
                     color='Profit Margin', color_continuous_scale='tealgrn',
                     text=[f"{v/1e3:.0f}K" for v in top15_plot['Total Profit']],
                     hover_data=['Qty', 'Profit Margin'])
        fig.update_layout(
            height=500, template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=20), coloraxis_colorbar_title='Margin %',
        )
        fig.update_traces(textposition='outside', textfont_size=10)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("""
        <div class="insight-box">
        💡 Yoghurt combos dominate the top 5. <b>Water</b> (588K units, 88% margin) is the silent profit champion. 
        <b>Double Espresso</b> at 89% margin is the most cost-efficient product.
        </div>
        """, unsafe_allow_html=True)
    
    with tab2:
        st.subheader("Top 10 Loss-Making Products")
        
        df_loss = df_core_products[df_core_products['Total Profit'] < 0].sort_values('Total Profit').head(10)
        df_loss_plot = df_loss.copy()
        df_loss_plot['Abs Loss'] = df_loss_plot['Total Profit'].abs()
        
        fig = px.bar(df_loss_plot, x='Abs Loss', y='Product', orientation='h',
                     color_discrete_sequence=[COLORS['red']],
                     text=[f"-{v/1e3:.0f}K" for v in df_loss_plot['Abs Loss']],
                     hover_data=['Qty'])
        fig.update_layout(
            height=420, template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis_title='Loss (absolute)', yaxis_title='', yaxis_autorange='reversed',
            margin=dict(t=20),
        )
        fig.update_traces(textposition='outside', textfont_size=10)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown(f"""
        <div class="warning-box">
        ⚠️ <b>All top losers are frozen yoghurt combo toppings.</b> Total loss: <b>{abs(loss_total)/1e6:.0f}M</b>. 
        These items have high volume but zero standalone revenue — their ingredient cost isn't covered by combo pricing.
        Restructuring combo prices could recover the full 23M.
        </div>
        """, unsafe_allow_html=True)
    
    with tab3:
        st.subheader("Menu Engineering Matrix (Volume × Margin)")
        st.markdown("*Bubble size = total profit. Only products with 500+ units and valid margins shown.*")
        
        df_menu = df_core_products[(df_core_products['Qty'] >= 500) & 
                                    (df_core_products['Revenue'] > 0) &
                                    (df_core_products['Profit Margin'].between(-50, 100))].copy()
        
        df_menu['Bubble Size'] = df_menu['Total Profit'].clip(lower=1)
        fig = px.scatter(df_menu, x='Qty', y='Profit Margin', size='Bubble Size',
                         hover_name='Product', hover_data=['Revenue', 'Total Profit'],
                         color='Profit Margin', color_continuous_scale='tealgrn',
                         size_max=40)
        
        med_qty = df_menu['Qty'].median()
        med_margin = df_menu['Profit Margin'].median()
        
        fig.add_hline(y=med_margin, line_dash="dash", line_color="rgba(255,255,255,0.3)")
        fig.add_vline(x=med_qty, line_dash="dash", line_color="rgba(255,255,255,0.3)")
        
        fig.add_annotation(x=0.98, y=0.98, xref='paper', yref='paper', text="⭐ STARS", showarrow=False, font=dict(size=12, color=COLORS['accent']))
        fig.add_annotation(x=0.02, y=0.98, xref='paper', yref='paper', text="💎 PUZZLES", showarrow=False, font=dict(size=12, color=COLORS['blue']))
        fig.add_annotation(x=0.98, y=0.02, xref='paper', yref='paper', text="🐎 WORKHORSES", showarrow=False, font=dict(size=12, color=COLORS['warm']))
        fig.add_annotation(x=0.02, y=0.02, xref='paper', yref='paper', text="🐕 DOGS", showarrow=False, font=dict(size=12, color=COLORS['red']))
        
        fig.update_layout(
            height=500, template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis_title='Units Sold (Volume)', yaxis_title='Profit Margin (%)',
            margin=dict(t=20),
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.subheader("Top Modifiers / Upsells by Profit")
        
        df_mods = df_prod_agg[df_prod_agg['Product'].str.startswith('ADD ')].sort_values('Total Profit', ascending=False).head(12)
        df_mods_plot = df_mods.sort_values('Total Profit', ascending=True)
        
        fig = px.bar(df_mods_plot, x='Total Profit', y='Product', orientation='h',
                     color='Profit Margin', color_continuous_scale='tealgrn',
                     text=[f"{v/1e3:.0f}K" for v in df_mods_plot['Total Profit']])
        fig.update_layout(
            height=420, template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=20), coloraxis_colorbar_title='Margin %',
        )
        fig.update_traces(textposition='outside', textfont_size=10)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("""
        <div class="opportunity-box">
        🎯 <b>ADD SHOT</b> alone drives 2.9M in profit at 73% margin. <b>Caramel Drizzle</b> has 90% margin. 
        Training baristas to suggest these add-ons is the highest-ROI upsell strategy.
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# PAGE: GROWTH & EXPANSION
# ============================================================
elif page == "🚀 Growth & Expansion":
    st.markdown("# 🚀 Growth & Expansion Analysis")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("New Branches in 2025", "11", "From 14 to 25 locations")
    c2.metric("⭐ Fastest Ramp-Up", "Jbeil", "10.2M in month 2")
    c3.metric("✈️ Airport Annual", "39.4M", "Top 10 by October")
    
    st.markdown("---")
    
    # New branch ramp-up
    st.subheader("📈 New Branch Ramp-Up Curves")
    
    new_branch_names = []
    for _, row in df_2025.iterrows():
        first_month = None
        for m in months_order:
            if m in row and row[m] > 0:
                first_month = m
                break
        if first_month and first_month != 'January':
            new_branch_names.append(row['Branch'])
    
    if new_branch_names:
        selected_branches = st.multiselect(
            "Select branches to compare:",
            new_branch_names,
            default=new_branch_names[:6] if len(new_branch_names) > 6 else new_branch_names
        )
        
        fig = go.Figure()
        for i, branch in enumerate(selected_branches):
            branch_row = df_2025[df_2025['Branch'] == branch]
            if len(branch_row) > 0:
                vals = [branch_row[m].values[0] if m in branch_row.columns else 0 for m in months_order]
                fig.add_trace(go.Scatter(
                    x=[m[:3] for m in months_order], y=vals,
                    mode='lines+markers', name=branch,
                    line=dict(color=PALETTE[i % len(PALETTE)], width=2.5),
                    marker=dict(size=6),
                ))
        
        fig.update_layout(
            height=420, template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis_title='Month', yaxis_title='Monthly Revenue',
            yaxis_tickformat='.2s', margin=dict(t=20),
            legend=dict(orientation='h', y=-0.15),
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("""
    <div class="insight-box">
    💡 <b>Jbeil</b> hit 10.2M in just its 2nd month (Oct) — the strongest opening in the portfolio. 
    <b>Airport</b> ramped steadily to 8.4M/mo by Oct, benefiting from captive passenger traffic. 
    <b>Aley</b> spiked in August (summer/mountain tourism) then stabilized at ~4M.
    </div>
    """, unsafe_allow_html=True)
    
    # Expansion scorecard
    st.markdown("---")
    st.subheader("📋 Expansion Scorecard")
    
    scorecard_data = []
    for _, row in df_2025.iterrows():
        first_month = None
        for m in months_order:
            if m in row and row[m] > 0:
                first_month = m
                break
        if first_month and first_month != 'January':
            dec_rev = row.get('December', 0)
            branch_cat = df_branch_totals[df_branch_totals['Branch'] == row['Branch']]
            margin = branch_cat['Profit %'].values[0] if len(branch_cat) > 0 else 0
            total = row.get('Total By Year', 0)
            
            if total > 30000000: assessment = "🟢 Star"
            elif total > 15000000: assessment = "🟡 Solid"
            elif total > 5000000: assessment = "🔵 Early"
            else: assessment = "⚪ Minimal"
            
            scorecard_data.append({
                'Branch': row['Branch'],
                'Opened': first_month[:3],
                'Dec Revenue': f"{dec_rev/1e6:.1f}M" if dec_rev > 0 else "—",
                'Annual': f"{total/1e6:.1f}M",
                'Margin': f"{margin:.1f}%",
                'Assessment': assessment,
            })
    
    df_score = pd.DataFrame(scorecard_data).sort_values('Annual', ascending=False)
    st.dataframe(df_score, use_container_width=True, hide_index=True)


# ============================================================
# PAGE: RECOMMENDATIONS
# ============================================================
elif page == "🎯 Recommendations":
    st.markdown("# 🎯 Strategic Recommendations")
    st.markdown("*5 prioritized actions to grow profitability, ordered by estimated impact*")
    
    st.markdown("---")
    
    recs = [
        ("R01", "Restructure Frozen Yoghurt Combo Pricing", "+23M profit recovery", "Low",
         COLORS['accent'],
         "The top 10 loss-making items are ALL combo toppings (blueberries, strawberry, mango, etc.) collectively losing ~23M. "
         "Raise combo base price 10-15% or limit included toppings to 2-3 with premium toppings as paid add-ons. "
         "Yoghurt combos are the #1 revenue category — demand is proven and inelastic."),
        
        ("R02", "Push Beverage Upsells at Food-Heavy Branches", "+15-30M incremental", "Medium",
         COLORS['blue'],
         "Branches where food >45% of revenue (Le Mall, Mansourieh, Antelias, LAU) have lower margins. "
         "Implement beverage-first promos, combo deals pairing food with specialty drinks, and barista add-on suggestions. "
         "Target: shift mix 5% toward beverages. Extra Shot alone drives 2.9M profit."),
        
        ("R03", "Seasonal Revenue Smoothing for June", "+28M incremental revenue", "Medium",
         COLORS['warm'],
         "June produces only 17% of peak-month revenue. Deploy Ramadan/Iftar promotions, loyalty double-points, "
         "and limited-time menu items. Target: lift June from 2% to 5% of annual revenue."),
        
        ("R04", "Investigate January 2026 Decline", "Prevent further erosion", "High",
         COLORS['red'],
         "Every established branch saw a YoY January decline averaging -42%. Saida (-67%) and LAU (-60%) are critical. "
         "Run cannibalization analysis mapping new branch catchment vs existing declines, competitive audit, "
         "and customer frequency survey. Pause expansion if cannibalization is confirmed."),
        
        ("R05", "Double Down on Star Products", "+5-10M from availability", "Low",
         COLORS['purple'],
         "Top 5 profit products contribute 107M in profit. Ensure zero stockouts, prominent display, and marketing. "
         "Water (588K units, 88% margin) is the silent champion. Double Espresso (89% margin) deserves prime menu placement."),
    ]
    
    for code, title, impact, effort, color, desc in recs:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(26,29,43,0.9), rgba(35,39,56,0.9)); 
                    border-left: 4px solid {color}; border-radius: 0 12px 12px 0; 
                    padding: 20px 24px; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                <div>
                    <span style="font-size: 0.75rem; font-weight: 700; color: {color}; 
                                 background: {color}22; padding: 2px 10px; border-radius: 4px;">{code}</span>
                    <span style="font-size: 1.1rem; font-weight: 700; margin-left: 10px;">{title}</span>
                </div>
                <div style="text-align: right;">
                    <span style="font-size: 0.85rem; font-weight: 700; color: {color}; 
                                 background: {color}15; padding: 4px 14px; border-radius: 6px;">{impact}</span>
                    <br><span style="font-size: 0.75rem; color: #888;">Effort: {effort}</span>
                </div>
            </div>
            <p style="margin-top: 10px; font-size: 0.88rem; color: #bbb; line-height: 1.6;">{desc}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("📊 Impact Summary")
    
    impact_data = pd.DataFrame({
        'Recommendation': ['Combo Pricing', 'Bev Upsells', 'June Smoothing', 'Star Products'],
        'Impact (M)': [23, 22.5, 28, 7.5],
    })
    
    fig = px.bar(impact_data, x='Recommendation', y='Impact (M)',
                 color='Recommendation', color_discrete_sequence=[COLORS['accent'], COLORS['blue'], COLORS['warm'], COLORS['purple']],
                 text='Impact (M)')
    fig.update_layout(
        height=350, template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False, margin=dict(t=20),
        yaxis_title='Estimated Annual Impact (M units)',
    )
    fig.update_traces(textposition='outside', textfont_size=12)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown(f"""
    <div class="insight-box">
    💡 <b>Combined potential impact: ~80M+ in incremental profit</b> — roughly 13% improvement on the current ~598M total gross profit.
    The combo pricing fix alone recovers 23M with minimal effort.
    </div>
    """, unsafe_allow_html=True)
