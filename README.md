## 🌐 [▶ Live Dashboard](https://stories-coffee-analysis-tobsjfqs6ghjdt4seqfk8g.streamlit.app/)
# Stories Coffee: Data-Driven Growth Strategy

## 📋 Business Problem

Stories is one of Lebanon's fastest-growing coffee chains with **25 branches** and **300+ products**. With a full year of POS sales data (2025 + January 2026), the founder asked: **"I have all this data… tell me how to make more money."**

We analyzed ~920M units in annual revenue across four data exports to uncover hidden profit leaks, evaluate the 2025 expansion wave, and identify the highest-impact growth levers.

## 🔍 Approach & Methodology

### Data Sources
| File | Contents | Records |
|------|----------|---------|
| `REP_S_00134_SMRY.csv` | Monthly sales by branch (YoY) | ~110 rows |
| `rep_s_00014_SMRY.csv` | Product-level profitability | ~14,600 rows |
| `rep_s_00191_SMRY-3.csv` | Sales by product groups | ~14,100 rows |
| `rep_s_00673_SMRY.csv` | Category profit by branch | ~110 rows |

### Data Cleaning
- Filtered repeated POS page headers throughout CSVs
- Normalized inconsistent branch names (e.g., "Stories alay" → "Aley")
- Addressed Total Price truncation bug using `Total Cost + Total Profit` as true revenue
- Parsed hierarchical structure: Branch → Service Type → Category → Section → Product

### Analysis Techniques
- **Seasonality decomposition**: Monthly revenue trends identifying peak/trough cycles
- **Menu engineering matrix**: BCG-style quadrant analysis (volume × margin) for 300+ products
- **Year-over-Year comparative**: January 2025 vs 2026 branch performance
- **Branch efficiency scoring**: Profit per unit sold, margin analysis, category mix
- **Product profitability audit**: Identifying loss-making items and high-margin upsell opportunities
- **New branch ramp-up analysis**: Growth curves for 11 branches opened in 2025

## 🏆 Key Findings

### 1. 🔴 Combo Toppings Are a Hidden 23M Profit Drain
The frozen yoghurt combo toppings (strawberry, blueberry, mango, etc.) are **all loss-making** — the top 10 money-losing items are exclusively combo add-ons. While yoghurt combos are the #1 revenue category, the topping costs aren't covered by combo pricing.

### 2. ☕ Beverages Deliver 77% Margins vs Food at 63%
Every percentage point shifted toward beverages in the product mix adds significant profit. Branches with >60% beverage share consistently outperform.

### 3. 📉 January 2026: ~42% Average YoY Decline
Every established branch declined in January 2026. Potential causes include cannibalization from 11 new branches, macro factors, or competitive pressure — requires urgent investigation.

### 4. 📊 5.9× Seasonal Revenue Swing
August (peak) generates 5.9× the revenue of June (trough). June represents a massive underutilization of fixed costs.

### 5. 🚀 Jbeil & Airport Are Expansion Stars
Among 11 new branches in 2025, Jbeil and Airport showed the fastest ramp-ups to profitability within 2-3 months.

## 📁 Repository Structure

```
├── README.md                           # This file
├── requirements.txt                    # Python dependencies
├── analysis.py                         # Main data parsing & analysis script
├── exec_summary.py                     # Executive summary PDF generator
├── output/
│   ├── Executive_Summary_Stories_Coffee.pdf  # 2-page executive summary
│   ├── 01_seasonality.png              # Monthly revenue seasonality
│   ├── 02_branch_profit.png            # Branch profit ranking
│   ├── 03_margin_by_branch.png         # Profit margins by branch
│   ├── 04_bev_vs_food.png              # Beverages vs Food split
│   ├── 05_top_products.png             # Top 15 products by profit
│   ├── 06_product_groups.png           # Product group revenue
│   ├── 07_yoy_comparison.png           # YoY January comparison
│   ├── 08_menu_engineering.png         # Menu engineering matrix
│   ├── 09_bev_food_mix.png             # Bev/Food mix by branch
│   ├── 10_modifiers.png               # Modifier profitability
│   └── 11_new_branches.png             # New branch ramp-up curves
└── data/                               # Place CSV files here
    ├── REP_S_00134_SMRY.csv
    ├── rep_s_00014_SMRY.csv
    ├── rep_s_00191_SMRY-3.csv
    └── rep_s_00673_SMRY.csv
```

## 🚀 How to Run

```bash
# Clone and setup
git clone <repo-url>
cd stories-coffee-analysis

# Install dependencies
pip install -r requirements.txt

# Place CSV files in data/ directory, then run:
python analysis.py        # Generates all charts + analysis output
python exec_summary.py    # Generates the executive summary PDF
```

## 📊 Key Visualizations

### Seasonality Pattern
![Seasonality](output/01_seasonality.png)

### Branch Profitability
![Branch Profit](output/02_branch_profit.png)

### Menu Engineering Matrix
![Menu Engineering](output/08_menu_engineering.png)

### YoY January Performance
![YoY](output/07_yoy_comparison.png)

## 💡 Recommendations Summary

| # | Action | Expected Impact | Effort |
|---|--------|----------------|--------|
| 1 | Restructure combo pricing | +23M profit recovery | Low |
| 2 | Push beverage upsells at food-heavy branches | +15-30M profit | Medium |
| 3 | Seasonal revenue smoothing (June focus) | +28M revenue | Medium |
| 4 | Investigate Jan 2026 decline urgently | Prevent further erosion | High |
| 5 | Double down on star products | +5-10M availability gains | Low |

## ⚙️ Tech Stack
- **Python 3.12** with pandas, numpy, matplotlib, seaborn
- **ReportLab** for PDF generation
- Analysis runs on raw POS CSV exports without manual preprocessing

---
*Built for the Stories Coffee Hackathon — 12-Hour Data Challenge*
