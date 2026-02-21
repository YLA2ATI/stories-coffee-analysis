import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import re
import os
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['font.size'] = 10
sns.set_theme(style="whitegrid")

DATA_DIR = '/mnt/user-data/uploads'
OUT_DIR = '/home/claude/output'
os.makedirs(OUT_DIR, exist_ok=True)

# ============================================================
# UTILITY: Branch name normalization
# ============================================================
def normalize_branch(name):
    if pd.isna(name):
        return name
    name = str(name).strip()
    # Remove "Stories" prefix variants
    name = re.sub(r'^Stories\s*[-]?\s*', '', name, flags=re.IGNORECASE)
    name = name.strip()
    # Title case
    name = name.title()
    # Fix specific names
    replacements = {
        'Alay': 'Aley',
        'Sin El Fil': 'Sin El Fil',
        'Ain El Mreisseh': 'Ain El Mreisseh',
        'Ramlet El Bayda': 'Ramlet El Bayda',
        'Stories.': 'Closed/Temp',
        '.': 'Closed/Temp',
        '': 'Closed/Temp',
        'Bir Hasan': 'Bir Hasan',
        'Sour 2': 'Sour 2',
        'Le Mall': 'Le Mall',
        'Centro Mall': 'Centro Mall',
        'Event Starco': 'Event Starco',
        'Lau': 'LAU',
    }
    if name in replacements:
        return replacements[name]
    return name

def parse_num(val):
    if pd.isna(val):
        return 0.0
    val = str(val).replace(',', '').strip()
    try:
        return float(val)
    except:
        return 0.0

# ============================================================
# FILE 1: Monthly Sales (REP_S_00134_SMRY.csv)
# ============================================================
print("=" * 60)
print("PARSING FILE 1: Monthly Sales")
print("=" * 60)

with open(f'{DATA_DIR}/REP_S_00134_SMRY.csv', 'r', encoding='utf-8-sig') as f:
    lines = f.readlines()

months_order = ['January','February','March','April','May','June',
                'July','August','September','October','November','December']

records = []
current_year = None

for line in lines:
    line = line.strip()
    if not line:
        continue
    # Skip headers
    if 'Page ' in line and ' of' in line:
        continue
    if line.startswith('Stories,,,') or line.startswith('Comparative'):
        continue
    if line.startswith('22-Jan'):
        continue
    
    # Parse column headers to detect month offsets
    parts = line.split(',')
    
    # Check if it's a header row with month names
    if any(m in line for m in ['January','February']):
        # These are column alignment rows — skip
        continue
    
    # Check for year at start
    if parts[0].strip() in ['2025', '2026']:
        current_year = int(parts[0].strip())
    
    # Skip total rows
    if 'Total' in parts[0] or 'Total' in (parts[1] if len(parts) > 1 else ''):
        if 'Total By Year' not in line:
            continue
    
    # Try to parse branch data
    # Branch name is in parts[1] (or parts[0] for some rows)
    branch_raw = parts[1].strip() if len(parts) > 1 else ''
    if not branch_raw or branch_raw == 'Total':
        # Could be in parts[0]
        if parts[0].strip() not in ['2025', '2026', '']:
            continue
        continue
    
    if branch_raw == 'Total':
        continue
    
    branch = normalize_branch(branch_raw)
    
    # Now we need to figure out which columns have data
    # The CSV has varying column structures. Let me just grab all numeric values
    # and the Total By Year
    numeric_vals = []
    for p in parts[2:]:
        numeric_vals.append(parse_num(p))
    
    # Remove trailing zeros and 'Total By Year' label
    # Check if 'Total By Year' appears in line
    if 'Total By Year' in line:
        # This is the Oct-Dec + Total section
        # Format: branch, Oct, Nov, Dec, TotalByYear
        # Find the numeric values
        vals = [parse_num(p) for p in parts[2:] if p.strip() and p.strip() != 'Total By Year']
        vals = [v for v in vals if True]  # keep all including 0
        if len(vals) >= 4:
            records.append({
                'Year': current_year,
                'Branch': branch,
                'Section': 'oct_dec_total',
                'October': vals[0],
                'November': vals[1],
                'December': vals[2],
                'Total By Year': vals[3]
            })
    else:
        # Jan-Sep section or Jan 2026
        vals = [parse_num(p) for p in parts[2:]]
        # Filter out empty/label cols
        vals = vals[:12]  # max 12 months
        records.append({
            'Year': current_year,
            'Branch': branch,
            'Section': 'jan_sep',
            'Values': vals
        })

# Now reconstruct the monthly data properly by re-parsing more carefully
# Let me do a cleaner parse
monthly_data = []
current_year = None

with open(f'{DATA_DIR}/REP_S_00134_SMRY.csv', 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Split into logical sections
lines = content.split('\n')
branch_data = {}

current_year = None
section_months = None  # which months the current columns represent

for line in lines:
    line = line.strip()
    if not line:
        continue
    
    parts = [p.strip().strip('"') for p in re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', line)]
    
    # Skip non-data rows
    if 'Page ' in line:
        continue
    if line.startswith('Stories,,,') or 'Comparative' in line or '22-Jan' in line:
        continue
    
    # Detect column headers
    if 'January' in line or 'October' in line:
        if 'Total By Year' in line:
            section_months = ['October', 'November', 'December', 'Total By Year']
        elif 'January' in line:
            section_months = ['January','February','March','April','May','June',
                             'July','August','September']
        continue
    
    # Detect year
    year_match = None
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
    
    if not branch_name or branch_name == 'Total':
        continue
    
    branch = normalize_branch(branch_name)
    
    if section_months is None:
        section_months = ['January','February','March','April','May','June',
                         'July','August','September']
    
    # Extract values
    vals = []
    for p in parts[data_start:]:
        p_clean = p.replace(',', '').strip()
        if p_clean and p_clean not in ['Total By Year']:
            try:
                vals.append(float(p_clean))
            except:
                pass
    
    key = (current_year, branch)
    if key not in branch_data:
        branch_data[key] = {}
    
    for i, month in enumerate(section_months):
        if i < len(vals):
            branch_data[key][month] = vals[i]

# Convert to DataFrame
rows = []
for (year, branch), months in branch_data.items():
    row = {'Year': year, 'Branch': branch}
    row.update(months)
    rows.append(row)

df_monthly = pd.DataFrame(rows)

# Filter out Total rows
df_monthly = df_monthly[df_monthly['Branch'] != 'Total'].copy()

print(f"Branches found: {df_monthly['Branch'].nunique()}")
print(f"Years: {df_monthly['Year'].unique()}")

# Separate 2025 and 2026
df_2025 = df_monthly[df_monthly['Year'] == 2025].copy()
df_2026 = df_monthly[df_monthly['Year'] == 2026].copy()

print(f"\n2025 branches: {len(df_2025)}")
print(f"2026 branches (Jan only): {len(df_2026)}")

# Calculate total annual revenue for 2025
if 'Total By Year' in df_2025.columns:
    df_2025_sorted = df_2025.sort_values('Total By Year', ascending=False)
    print("\n--- 2025 Annual Revenue by Branch (Top 10) ---")
    for _, row in df_2025_sorted.head(10).iterrows():
        print(f"  {row['Branch']:25s}: {row['Total By Year']:>15,.0f}")
    
    total_2025 = df_2025['Total By Year'].sum()
    print(f"\n  {'TOTAL':25s}: {total_2025:>15,.0f}")

# ============================================================
# FILE 4: Category Summary (rep_s_00673_SMRY.csv)
# ============================================================
print("\n" + "=" * 60)
print("PARSING FILE 4: Category Profit Summary")
print("=" * 60)

cat_records = []
current_branch = None

with open(f'{DATA_DIR}/rep_s_00673_SMRY.csv', 'r', encoding='utf-8-sig') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        if 'Page ' in line or 'Theoretical' in line or '22-Jan' in line:
            continue
        if line.startswith('Category,'):
            continue
        if 'Copyright' in line or 'REP_S' in line:
            continue
        
        parts = [p.strip().strip('"') for p in re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', line)]
        
        # Branch header
        if parts[0].startswith('Stories') and (len(parts) < 3 or parts[1] == ''):
            current_branch = normalize_branch(parts[0])
            continue
        
        cat = parts[0].strip()
        if cat in ['BEVERAGES', 'FOOD']:
            qty = parse_num(parts[1])
            total_price = parse_num(parts[2])
            # parts[3] is empty
            total_cost = parse_num(parts[4])
            cost_pct = parse_num(parts[5])
            total_profit = parse_num(parts[6])
            # parts[7] is empty
            profit_pct = parse_num(parts[8])
            
            # Fix Total Price: use Cost + Profit as true revenue
            true_revenue = total_cost + total_profit
            
            cat_records.append({
                'Branch': current_branch,
                'Category': cat,
                'Qty': qty,
                'Total Price (Raw)': total_price,
                'Revenue (Cost+Profit)': true_revenue,
                'Total Cost': total_cost,
                'Cost %': cost_pct,
                'Total Profit': total_profit,
                'Profit %': profit_pct
            })
        elif cat.startswith('Total By Branch'):
            qty = parse_num(parts[1])
            total_price = parse_num(parts[2])
            total_cost = parse_num(parts[4])
            cost_pct = parse_num(parts[5])
            total_profit = parse_num(parts[6])
            profit_pct = parse_num(parts[8])
            true_revenue = total_cost + total_profit
            
            cat_records.append({
                'Branch': current_branch,
                'Category': 'TOTAL',
                'Qty': qty,
                'Total Price (Raw)': total_price,
                'Revenue (Cost+Profit)': true_revenue,
                'Total Cost': total_cost,
                'Cost %': cost_pct,
                'Total Profit': total_profit,
                'Profit %': profit_pct
            })

df_category = pd.DataFrame(cat_records)
print(f"Category records: {len(df_category)}")
print(f"Branches: {df_category['Branch'].nunique()}")

# Branch totals
df_branch_totals = df_category[df_category['Category'] == 'TOTAL'].copy()
df_branch_totals = df_branch_totals.sort_values('Total Profit', ascending=False)

print("\n--- Branch Profitability (Top 10) ---")
for _, row in df_branch_totals.head(10).iterrows():
    print(f"  {row['Branch']:25s}: Profit={row['Total Profit']:>15,.0f}  Margin={row['Profit %']:.1f}%")

# Beverages vs Food
df_bev = df_category[df_category['Category'] == 'BEVERAGES']
df_food = df_category[df_category['Category'] == 'FOOD']

total_bev_profit = df_bev['Total Profit'].sum()
total_food_profit = df_food['Total Profit'].sum()
total_bev_cost = df_bev['Total Cost'].sum()
total_food_cost = df_food['Total Cost'].sum()
total_bev_rev = df_bev['Revenue (Cost+Profit)'].sum()
total_food_rev = df_food['Revenue (Cost+Profit)'].sum()

print(f"\n--- Category Comparison ---")
print(f"  BEVERAGES: Revenue={total_bev_rev:>15,.0f}  Profit={total_bev_profit:>15,.0f}  Margin={total_bev_profit/total_bev_rev*100:.1f}%")
print(f"  FOOD:      Revenue={total_food_rev:>15,.0f}  Profit={total_food_profit:>15,.0f}  Margin={total_food_profit/total_food_rev*100:.1f}%")

# ============================================================
# FILE 2: Product Profitability (rep_s_00014_SMRY.csv)
# ============================================================
print("\n" + "=" * 60)
print("PARSING FILE 2: Product Profitability")
print("=" * 60)

product_records = []
current_branch = None
current_service = None
current_category = None
current_section = None

with open(f'{DATA_DIR}/rep_s_00014_SMRY.csv', 'r', encoding='utf-8-sig') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        if 'Page ' in line or 'Theoretical' in line or '22-Jan' in line:
            continue
        if line.startswith('Product Desc,'):
            continue
        if 'Copyright' in line or 'REP_S' in line:
            continue
        
        parts = [p.strip().strip('"') for p in re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', line)]
        
        name = parts[0].strip()
        
        # Detect hierarchy
        if name.startswith('Stories') and (len(parts) < 3 or parts[1] == ''):
            current_branch = normalize_branch(name)
            continue
        if name in ['TAKE AWAY', 'TABLE']:
            current_service = name
            continue
        if name in ['BEVERAGES', 'FOOD']:
            current_category = name
            continue
        if 'SECTION' in name or name in ['HOT BAR SECTION', 'COLD BAR SECTION', 'DONUTS', 
                                          'FOOD SECTION', 'GRAB AND GO']:
            current_section = name
            continue
        
        # Skip subtotals
        if name.startswith('Total By') or name.startswith('Total:'):
            continue
        
        # Parse product data
        if len(parts) >= 9:
            qty = parse_num(parts[1])
            total_price = parse_num(parts[2])
            # parts[3] empty
            total_cost = parse_num(parts[4])
            cost_pct = parse_num(parts[5])
            total_profit = parse_num(parts[6])
            # parts[7] empty
            profit_pct = parse_num(parts[8])
            
            if qty > 0:
                product_records.append({
                    'Branch': current_branch,
                    'Service': current_service,
                    'Category': current_category,
                    'Section': current_section,
                    'Product': name,
                    'Qty': qty,
                    'Total Price': total_price,
                    'Total Cost': total_cost,
                    'Cost %': cost_pct,
                    'Total Profit': total_profit,
                    'Profit %': profit_pct,
                    'Revenue': total_cost + total_profit  # True revenue
                })

df_products = pd.DataFrame(product_records)
print(f"Product records: {len(df_products)}")
print(f"Unique products: {df_products['Product'].nunique()}")

# Aggregate products across all branches
df_prod_agg = df_products.groupby('Product').agg({
    'Qty': 'sum',
    'Total Cost': 'sum',
    'Total Profit': 'sum',
    'Revenue': 'sum'
}).reset_index()
df_prod_agg['Profit Margin'] = df_prod_agg['Total Profit'] / df_prod_agg['Revenue'] * 100
df_prod_agg['Avg Price'] = df_prod_agg['Revenue'] / df_prod_agg['Qty']

# Filter out modifiers (ADD ...) for top products
df_products_only = df_prod_agg[~df_prod_agg['Product'].str.startswith('ADD ')].copy()
df_products_only = df_products_only[df_products_only['Qty'] >= 100]  # meaningful volume

print("\n--- Top 15 Products by Total Profit ---")
top_profit = df_products_only.sort_values('Total Profit', ascending=False).head(15)
for _, row in top_profit.iterrows():
    print(f"  {row['Product']:40s}: Qty={row['Qty']:>8,.0f}  Profit={row['Total Profit']:>12,.0f}  Margin={row['Profit Margin']:.1f}%")

print("\n--- Top 15 Products by Volume ---")
top_vol = df_products_only.sort_values('Qty', ascending=False).head(15)
for _, row in top_vol.iterrows():
    print(f"  {row['Product']:40s}: Qty={row['Qty']:>8,.0f}  Profit={row['Total Profit']:>12,.0f}  Margin={row['Profit Margin']:.1f}%")

# Modifiers analysis
df_modifiers = df_prod_agg[df_prod_agg['Product'].str.startswith('ADD ')].copy()
df_modifiers = df_modifiers.sort_values('Total Profit', ascending=False)
print("\n--- Top 10 Modifiers by Profit ---")
for _, row in df_modifiers.head(10).iterrows():
    print(f"  {row['Product']:40s}: Qty={row['Qty']:>8,.0f}  Profit={row['Total Profit']:>12,.0f}  Margin={row['Profit Margin']:.1f}%")

# Loss-making items
df_loss = df_products_only[df_products_only['Total Profit'] < 0].sort_values('Total Profit')
print(f"\n--- Loss-Making Products: {len(df_loss)} items ---")
for _, row in df_loss.head(10).iterrows():
    print(f"  {row['Product']:40s}: Qty={row['Qty']:>8,.0f}  Loss={row['Total Profit']:>12,.0f}")

# ============================================================
# FILE 3: Sales by Groups (rep_s_00191_SMRY-3.csv)
# ============================================================
print("\n" + "=" * 60)
print("PARSING FILE 3: Sales by Groups")
print("=" * 60)

group_records = []
current_branch = None
current_division = None
current_group = None

with open(f'{DATA_DIR}/rep_s_00191_SMRY-3.csv', 'r', encoding='utf-8-sig') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        if 'Page ' in line or 'Sales by Items' in line or '19-Jan' in line:
            continue
        if line.startswith('Description,'):
            continue
        if 'Copyright' in line:
            continue
        
        parts = [p.strip().strip('"') for p in re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', line)]
        
        name = parts[0].strip()
        
        # Hierarchy detection
        if name.startswith('Branch:'):
            current_branch = normalize_branch(name.replace('Branch:', '').strip())
            continue
        if name.startswith('Division:'):
            current_division = name.replace('Division:', '').strip()
            continue
        if name.startswith('Group:'):
            current_group = name.replace('Group:', '').strip()
            continue
        
        # Skip totals
        if name.startswith('Total by'):
            continue
        
        # Parse product data
        if len(parts) >= 4:
            qty = parse_num(parts[2])
            total_amount = parse_num(parts[3])
            
            if qty > 0:
                group_records.append({
                    'Branch': current_branch,
                    'Division': current_division,
                    'Group': current_group,
                    'Product': name,
                    'Qty': qty,
                    'Total Amount': total_amount
                })

df_groups = pd.DataFrame(group_records)
print(f"Group records: {len(df_groups)}")

# Group-level summary
df_group_summary = df_groups.groupby('Group').agg({
    'Qty': 'sum',
    'Total Amount': 'sum'
}).reset_index()
df_group_summary = df_group_summary.sort_values('Total Amount', ascending=False)

print("\n--- Product Groups by Revenue ---")
for _, row in df_group_summary.iterrows():
    print(f"  {row['Group']:35s}: Qty={row['Qty']:>10,.0f}  Revenue={row['Total Amount']:>15,.0f}")

# Division summary
df_div_summary = df_groups.groupby('Division').agg({
    'Qty': 'sum',
    'Total Amount': 'sum'
}).reset_index()
df_div_summary = df_div_summary.sort_values('Total Amount', ascending=False)

print("\n--- Division Summary ---")
for _, row in df_div_summary.iterrows():
    print(f"  {row['Division']:35s}: Qty={row['Qty']:>10,.0f}  Revenue={row['Total Amount']:>15,.0f}")

# ============================================================
# ANALYSIS & INSIGHTS
# ============================================================
print("\n" + "=" * 60)
print("KEY ANALYSES")
print("=" * 60)

# 1. Seasonality Analysis
print("\n--- Seasonality (2025 Monthly Totals) ---")
month_cols = [m for m in months_order if m in df_2025.columns]
monthly_totals = {}
for m in month_cols:
    monthly_totals[m] = df_2025[m].sum()
    print(f"  {m:12s}: {monthly_totals[m]:>15,.0f}")

# Peak/trough
peak_month = max(monthly_totals, key=monthly_totals.get)
trough_month = min(monthly_totals, key=monthly_totals.get)
print(f"\n  Peak: {peak_month} ({monthly_totals[peak_month]:,.0f})")
print(f"  Trough: {trough_month} ({monthly_totals[trough_month]:,.0f})")
print(f"  Ratio: {monthly_totals[peak_month]/monthly_totals[trough_month]:.1f}x")

# 2. Branch efficiency: profit per unit sold
print("\n--- Branch Efficiency (Profit per Unit) ---")
df_branch_eff = df_branch_totals.copy()
df_branch_eff['Profit per Unit'] = df_branch_eff['Total Profit'] / df_branch_eff['Qty']
df_branch_eff = df_branch_eff.sort_values('Profit per Unit', ascending=False)
for _, row in df_branch_eff.iterrows():
    print(f"  {row['Branch']:25s}: {row['Profit per Unit']:>8,.1f} per unit  (Margin: {row['Profit %']:.1f}%)")

# 3. YoY comparison (Jan 2025 vs Jan 2026)
print("\n--- YoY January Comparison (branches with both years) ---")
jan_2025 = df_2025[['Branch', 'January']].rename(columns={'January': 'Jan_2025'})
jan_2026 = df_2026[['Branch', 'January']].rename(columns={'January': 'Jan_2026'})
jan_compare = jan_2025.merge(jan_2026, on='Branch', how='inner')
jan_compare = jan_compare[(jan_compare['Jan_2025'] > 0) & (jan_compare['Jan_2026'] > 0)]
jan_compare['YoY Change %'] = (jan_compare['Jan_2026'] - jan_compare['Jan_2025']) / jan_compare['Jan_2025'] * 100
jan_compare = jan_compare.sort_values('YoY Change %', ascending=False)

for _, row in jan_compare.iterrows():
    direction = "📈" if row['YoY Change %'] > 0 else "📉"
    print(f"  {row['Branch']:25s}: {row['YoY Change %']:>+7.1f}%  ({row['Jan_2025']:>12,.0f} → {row['Jan_2026']:>12,.0f})")

# 4. New branches (opened mid-2025)
print("\n--- New Branches (opened during 2025) ---")
for _, row in df_2025.iterrows():
    first_month = None
    for m in months_order:
        if m in row and row[m] > 0:
            first_month = m
            break
    if first_month and first_month != 'January':
        print(f"  {row['Branch']:25s}: First sales in {first_month}")

# 5. Food vs Beverage mix by branch
print("\n--- Food vs Beverage Mix by Branch ---")
df_cat_pivot = df_category[df_category['Category'].isin(['BEVERAGES', 'FOOD'])].pivot_table(
    index='Branch', columns='Category', values='Revenue (Cost+Profit)', aggfunc='sum'
).fillna(0)
df_cat_pivot['Bev %'] = df_cat_pivot['BEVERAGES'] / (df_cat_pivot['BEVERAGES'] + df_cat_pivot['FOOD']) * 100
df_cat_pivot = df_cat_pivot.sort_values('Bev %', ascending=False)
for branch, row in df_cat_pivot.iterrows():
    print(f"  {branch:25s}: Bev={row['Bev %']:.0f}%  Food={100-row['Bev %']:.0f}%")

# ============================================================
# GENERATE VISUALIZATIONS
# ============================================================
print("\n" + "=" * 60)
print("GENERATING VISUALIZATIONS")
print("=" * 60)

# Color palette
COLORS = {
    'primary': '#2E4057',
    'accent': '#048A81',
    'warm': '#D4A574',
    'highlight': '#E76F51',
    'light': '#F4A261',
    'bev': '#264653',
    'food': '#E9C46A',
}

# --- CHART 1: Monthly Seasonality ---
fig, ax = plt.subplots(figsize=(12, 5))
month_vals = [monthly_totals.get(m, 0) for m in months_order]
bars = ax.bar(range(len(months_order)), month_vals, color=[COLORS['accent'] if v == max(month_vals) else COLORS['highlight'] if v == min(month_vals) else COLORS['primary'] for v in month_vals], edgecolor='white', linewidth=0.5)
ax.set_xticks(range(len(months_order)))
ax.set_xticklabels([m[:3] for m in months_order], fontsize=9)
ax.set_title('Monthly Revenue Seasonality (2025)', fontsize=14, fontweight='bold', pad=15)
ax.set_ylabel('Total Revenue (Arbitrary Units)')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.0f}M'))
# Annotate peak/trough
peak_idx = months_order.index(peak_month)
trough_idx = months_order.index(trough_month)
ax.annotate('PEAK', xy=(peak_idx, month_vals[peak_idx]), ha='center', va='bottom', fontweight='bold', color=COLORS['accent'], fontsize=9)
ax.annotate('TROUGH', xy=(trough_idx, month_vals[trough_idx]), ha='center', va='bottom', fontweight='bold', color=COLORS['highlight'], fontsize=9)
plt.tight_layout()
plt.savefig(f'{OUT_DIR}/01_seasonality.png', bbox_inches='tight')
plt.close()
print("  ✓ 01_seasonality.png")

# --- CHART 2: Branch Revenue Ranking ---
fig, ax = plt.subplots(figsize=(12, 8))
df_plot = df_branch_totals.sort_values('Total Profit', ascending=True)
colors = [COLORS['accent'] if i >= len(df_plot)-5 else COLORS['primary'] for i in range(len(df_plot))]
ax.barh(range(len(df_plot)), df_plot['Total Profit'], color=colors, edgecolor='white', linewidth=0.3)
ax.set_yticks(range(len(df_plot)))
ax.set_yticklabels(df_plot['Branch'], fontsize=8)
ax.set_title('Annual Gross Profit by Branch (2025)', fontsize=14, fontweight='bold', pad=15)
ax.set_xlabel('Total Gross Profit')
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.0f}M'))
plt.tight_layout()
plt.savefig(f'{OUT_DIR}/02_branch_profit.png', bbox_inches='tight')
plt.close()
print("  ✓ 02_branch_profit.png")

# --- CHART 3: Profit Margin by Branch ---
fig, ax = plt.subplots(figsize=(12, 8))
df_plot = df_branch_totals.sort_values('Profit %', ascending=True)
colors = [COLORS['highlight'] if v < 70 else COLORS['accent'] if v > 73 else COLORS['primary'] for v in df_plot['Profit %']]
ax.barh(range(len(df_plot)), df_plot['Profit %'], color=colors, edgecolor='white', linewidth=0.3)
ax.set_yticks(range(len(df_plot)))
ax.set_yticklabels(df_plot['Branch'], fontsize=8)
ax.set_title('Gross Profit Margin by Branch (2025)', fontsize=14, fontweight='bold', pad=15)
ax.set_xlabel('Profit Margin (%)')
ax.axvline(x=df_branch_totals['Profit %'].mean(), color='red', linestyle='--', alpha=0.7, label=f"Avg: {df_branch_totals['Profit %'].mean():.1f}%")
ax.legend()
plt.tight_layout()
plt.savefig(f'{OUT_DIR}/03_margin_by_branch.png', bbox_inches='tight')
plt.close()
print("  ✓ 03_margin_by_branch.png")

# --- CHART 4: Beverages vs Food ---
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Revenue split
labels = ['Beverages', 'Food']
rev_vals = [total_bev_rev, total_food_rev]
axes[0].pie(rev_vals, labels=labels, colors=[COLORS['bev'], COLORS['food']], 
            autopct='%1.1f%%', startangle=90, textprops={'fontsize': 11})
axes[0].set_title('Revenue Split', fontsize=13, fontweight='bold')

# Profit split
profit_vals = [total_bev_profit, total_food_profit]
axes[1].pie(profit_vals, labels=labels, colors=[COLORS['bev'], COLORS['food']], 
            autopct='%1.1f%%', startangle=90, textprops={'fontsize': 11})
axes[1].set_title('Profit Split', fontsize=13, fontweight='bold')

fig.suptitle('Beverages vs Food: Revenue & Profit Distribution', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(f'{OUT_DIR}/04_bev_vs_food.png', bbox_inches='tight')
plt.close()
print("  ✓ 04_bev_vs_food.png")

# --- CHART 5: Top Products by Profit ---
fig, ax = plt.subplots(figsize=(12, 7))
top15 = df_products_only.sort_values('Total Profit', ascending=False).head(15)
top15 = top15.sort_values('Total Profit', ascending=True)
colors = [COLORS['accent'] if 'FRAPP' in p or 'LATTE' in p else COLORS['primary'] for p in top15['Product']]
ax.barh(range(len(top15)), top15['Total Profit'], color=colors, edgecolor='white', linewidth=0.3)
ax.set_yticks(range(len(top15)))
ax.set_yticklabels(top15['Product'], fontsize=8)
ax.set_title('Top 15 Products by Gross Profit', fontsize=14, fontweight='bold', pad=15)
ax.set_xlabel('Total Gross Profit')
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.0f}M'))
plt.tight_layout()
plt.savefig(f'{OUT_DIR}/05_top_products.png', bbox_inches='tight')
plt.close()
print("  ✓ 05_top_products.png")

# --- CHART 6: Product Groups Revenue ---
fig, ax = plt.subplots(figsize=(12, 7))
df_gs = df_group_summary.head(15).sort_values('Total Amount', ascending=True)
ax.barh(range(len(df_gs)), df_gs['Total Amount'], color=COLORS['primary'], edgecolor='white', linewidth=0.3)
ax.set_yticks(range(len(df_gs)))
ax.set_yticklabels(df_gs['Group'], fontsize=8)
ax.set_title('Top Product Groups by Revenue', fontsize=14, fontweight='bold', pad=15)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.0f}M'))
plt.tight_layout()
plt.savefig(f'{OUT_DIR}/06_product_groups.png', bbox_inches='tight')
plt.close()
print("  ✓ 06_product_groups.png")

# --- CHART 7: YoY January Comparison ---
if len(jan_compare) > 0:
    fig, ax = plt.subplots(figsize=(12, 7))
    jan_compare_plot = jan_compare.sort_values('YoY Change %', ascending=True)
    colors = [COLORS['accent'] if v > 0 else COLORS['highlight'] for v in jan_compare_plot['YoY Change %']]
    ax.barh(range(len(jan_compare_plot)), jan_compare_plot['YoY Change %'], color=colors, edgecolor='white', linewidth=0.3)
    ax.set_yticks(range(len(jan_compare_plot)))
    ax.set_yticklabels(jan_compare_plot['Branch'], fontsize=8)
    ax.set_title('Year-over-Year Change: January 2025 → January 2026', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Change (%)')
    ax.axvline(x=0, color='black', linewidth=0.5)
    plt.tight_layout()
    plt.savefig(f'{OUT_DIR}/07_yoy_comparison.png', bbox_inches='tight')
    plt.close()
    print("  ✓ 07_yoy_comparison.png")

# --- CHART 8: Menu Engineering Matrix (BCG-style) ---
fig, ax = plt.subplots(figsize=(10, 8))
# Use products with enough volume AND valid margins
df_menu = df_products_only[(df_products_only['Qty'] >= 500) & 
                            (df_products_only['Revenue'] > 0) &
                            (df_products_only['Profit Margin'].between(-200, 200))].copy()
median_qty = df_menu['Qty'].median()
median_margin = df_menu['Profit Margin'].median()

for _, row in df_menu.iterrows():
    color = COLORS['accent'] if row['Qty'] >= median_qty and row['Profit Margin'] >= median_margin else \
            COLORS['light'] if row['Qty'] >= median_qty else \
            COLORS['primary'] if row['Profit Margin'] >= median_margin else \
            COLORS['highlight']
    ax.scatter(row['Qty'], row['Profit Margin'], s=max(abs(row['Total Profit'])/5000, 10), 
               color=color, alpha=0.6, edgecolors='white', linewidth=0.5)

ax.axhline(y=median_margin, color='gray', linestyle='--', alpha=0.5)
ax.axvline(x=median_qty, color='gray', linestyle='--', alpha=0.5)

# Quadrant labels
ax.text(0.95, 0.95, '⭐ STARS\nHigh Vol + High Margin', transform=ax.transAxes, ha='right', va='top', fontsize=9, color=COLORS['accent'], fontweight='bold')
ax.text(0.05, 0.95, '💎 PUZZLES\nLow Vol + High Margin', transform=ax.transAxes, ha='left', va='top', fontsize=9, color=COLORS['primary'], fontweight='bold')
ax.text(0.95, 0.05, '🐎 WORKHORSES\nHigh Vol + Low Margin', transform=ax.transAxes, ha='right', va='bottom', fontsize=9, color=COLORS['light'], fontweight='bold')
ax.text(0.05, 0.05, '🐕 DOGS\nLow Vol + Low Margin', transform=ax.transAxes, ha='left', va='bottom', fontsize=9, color=COLORS['highlight'], fontweight='bold')

# Label some notable products
for _, row in df_menu.nlargest(8, 'Total Profit').iterrows():
    label = row['Product'][:20]
    ax.annotate(label, (row['Qty'], row['Profit Margin']), fontsize=6, alpha=0.8,
                xytext=(5, 5), textcoords='offset points')

ax.set_title('Menu Engineering Matrix\n(Bubble size = Total Profit)', fontsize=14, fontweight='bold', pad=15)
ax.set_xlabel('Units Sold (Volume)')
ax.set_ylabel('Profit Margin (%)')
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1000:.0f}K'))
plt.tight_layout()
plt.savefig(f'{OUT_DIR}/08_menu_engineering.png', bbox_inches='tight')
plt.close()
print("  ✓ 08_menu_engineering.png")

# --- CHART 9: Beverage/Food Mix by Branch ---
fig, ax = plt.subplots(figsize=(12, 8))
df_mix = df_cat_pivot.sort_values('Bev %', ascending=True)
ax.barh(range(len(df_mix)), df_mix['Bev %'], color=COLORS['bev'], label='Beverages', edgecolor='white', linewidth=0.3)
ax.barh(range(len(df_mix)), 100 - df_mix['Bev %'], left=df_mix['Bev %'], color=COLORS['food'], label='Food', edgecolor='white', linewidth=0.3)
ax.set_yticks(range(len(df_mix)))
ax.set_yticklabels(df_mix.index, fontsize=8)
ax.set_title('Revenue Mix: Beverages vs Food by Branch', fontsize=14, fontweight='bold', pad=15)
ax.set_xlabel('Share (%)')
ax.legend(loc='lower right')
plt.tight_layout()
plt.savefig(f'{OUT_DIR}/09_bev_food_mix.png', bbox_inches='tight')
plt.close()
print("  ✓ 09_bev_food_mix.png")

# --- CHART 10: Modifier Profitability ---
fig, ax = plt.subplots(figsize=(12, 6))
top_mods = df_modifiers.head(12).sort_values('Total Profit', ascending=True)
ax.barh(range(len(top_mods)), top_mods['Total Profit'], color=COLORS['accent'], edgecolor='white', linewidth=0.3)
ax.set_yticks(range(len(top_mods)))
ax.set_yticklabels(top_mods['Product'], fontsize=8)
ax.set_title('Top Modifiers by Profit (Upsell Opportunities)', fontsize=14, fontweight='bold', pad=15)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.1f}M'))
plt.tight_layout()
plt.savefig(f'{OUT_DIR}/10_modifiers.png', bbox_inches='tight')
plt.close()
print("  ✓ 10_modifiers.png")

# --- CHART 11: New Branch Ramp-up ---
new_branches = ['Airport', 'Mansourieh', 'Sour 2', 'Aley', 'Jbeil', 'Amioun', 'Sin El Fil', 'Kaslik', 'Raouche']
fig, ax = plt.subplots(figsize=(12, 6))
for branch in new_branches:
    branch_row = df_2025[df_2025['Branch'] == branch]
    if len(branch_row) > 0:
        vals = []
        for m in months_order:
            if m in branch_row.columns:
                vals.append(branch_row[m].values[0])
            else:
                vals.append(0)
        if max(vals) > 0:
            ax.plot(range(len(months_order)), vals, marker='o', markersize=3, label=branch, linewidth=1.5)

ax.set_xticks(range(len(months_order)))
ax.set_xticklabels([m[:3] for m in months_order], fontsize=9)
ax.set_title('New Branch Ramp-Up Curves (2025)', fontsize=14, fontweight='bold', pad=15)
ax.set_ylabel('Monthly Revenue')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.0f}M'))
ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
plt.tight_layout()
plt.savefig(f'{OUT_DIR}/11_new_branches.png', bbox_inches='tight')
plt.close()
print("  ✓ 11_new_branches.png")

print("\n✅ All visualizations generated!")

# Save key data for the report
import json
report_data = {
    'total_2025_revenue': float(df_2025['Total By Year'].sum()) if 'Total By Year' in df_2025.columns else 0,
    'num_branches': int(df_monthly['Branch'].nunique()),
    'num_products': int(df_products['Product'].nunique()),
    'peak_month': peak_month,
    'trough_month': trough_month,
    'peak_trough_ratio': float(monthly_totals[peak_month]/monthly_totals[trough_month]),
    'bev_profit_share': float(total_bev_profit / (total_bev_profit + total_food_profit) * 100),
    'food_profit_share': float(total_food_profit / (total_bev_profit + total_food_profit) * 100),
    'bev_margin': float(total_bev_profit/total_bev_rev*100),
    'food_margin': float(total_food_profit/total_food_rev*100),
    'avg_margin': float(df_branch_totals['Profit %'].mean()),
    'top_branch': df_branch_totals.iloc[0]['Branch'],
    'top_branch_profit': float(df_branch_totals.iloc[0]['Total Profit']),
    'yoy_avg_change': float(jan_compare['YoY Change %'].mean()) if len(jan_compare) > 0 else 0,
    'num_yoy_growing': int((jan_compare['YoY Change %'] < 0).sum()) if len(jan_compare) > 0 else 0,
    'new_branches_2025': len([b for b in new_branches if any(df_2025[df_2025['Branch']==b][m].values[0] > 0 for m in months_order if m in df_2025.columns) if len(df_2025[df_2025['Branch']==b]) > 0]),
}

with open(f'{OUT_DIR}/report_data.json', 'w') as f:
    json.dump(report_data, f, indent=2)

print(f"\n📊 Report data saved")
print("Done with analysis!")
