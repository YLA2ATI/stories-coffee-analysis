"""
Executive Summary PDF - Stories Coffee Data Consulting Report
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable
)
from reportlab.platypus.flowables import Flowable
import json
import os

OUT_DIR = '/home/claude/output'

# Load analysis data
with open(f'{OUT_DIR}/report_data.json', 'r') as f:
    data = json.load(f)

# Colors
PRIMARY = HexColor('#2E4057')
ACCENT = HexColor('#048A81')
WARM = HexColor('#D4A574')
HIGHLIGHT = HexColor('#E76F51')
LIGHT_BG = HexColor('#F8F6F3')
DARK_TEXT = HexColor('#1A1A2E')
GRAY = HexColor('#6B7280')
LIGHT_GRAY = HexColor('#E5E7EB')

# Create PDF
pdf_path = f'{OUT_DIR}/Executive_Summary_Stories_Coffee.pdf'
doc = SimpleDocTemplate(
    pdf_path,
    pagesize=letter,
    topMargin=0.6*inch,
    bottomMargin=0.6*inch,
    leftMargin=0.75*inch,
    rightMargin=0.75*inch,
)

styles = getSampleStyleSheet()

# Custom styles
styles.add(ParagraphStyle(
    'MainTitle', parent=styles['Title'],
    fontSize=22, textColor=PRIMARY, spaceAfter=4,
    fontName='Helvetica-Bold', alignment=TA_LEFT
))
styles.add(ParagraphStyle(
    'Subtitle', parent=styles['Normal'],
    fontSize=12, textColor=GRAY, spaceAfter=16,
    fontName='Helvetica', alignment=TA_LEFT
))
styles.add(ParagraphStyle(
    'SectionHead', parent=styles['Heading1'],
    fontSize=14, textColor=ACCENT, spaceBefore=16, spaceAfter=8,
    fontName='Helvetica-Bold', borderWidth=0,
))
styles.add(ParagraphStyle(
    'SubHead', parent=styles['Heading2'],
    fontSize=11, textColor=PRIMARY, spaceBefore=10, spaceAfter=4,
    fontName='Helvetica-Bold',
))
styles.add(ParagraphStyle(
    'Body', parent=styles['Normal'],
    fontSize=9.5, textColor=DARK_TEXT, spaceAfter=6,
    fontName='Helvetica', leading=13, alignment=TA_JUSTIFY,
))
styles.add(ParagraphStyle(
    'Insight', parent=styles['Normal'],
    fontSize=9.5, textColor=DARK_TEXT, spaceAfter=4,
    fontName='Helvetica', leading=13,
    leftIndent=12, bulletIndent=0,
))
styles.add(ParagraphStyle(
    'Bold', parent=styles['Normal'],
    fontSize=9.5, textColor=DARK_TEXT, spaceAfter=4,
    fontName='Helvetica-Bold', leading=13,
))
styles.add(ParagraphStyle(
    'Small', parent=styles['Normal'],
    fontSize=8, textColor=GRAY, spaceAfter=2,
    fontName='Helvetica',
))

story = []

# ============================================================
# TITLE
# ============================================================
story.append(Paragraph("Stories Coffee: Data-Driven Growth Strategy", styles['MainTitle']))
story.append(Paragraph("Executive Summary  |  Data Science Consulting Report  |  January 2026", styles['Subtitle']))
story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=12))

# ============================================================
# 1. PROBLEM STATEMENT
# ============================================================
story.append(Paragraph("1. Problem Statement", styles['SectionHead']))
story.append(Paragraph(
    "Stories, one of Lebanon's fastest-growing coffee chains with <b>25 branches</b> across the country, "
    "generated roughly <b>920M arbitrary units</b> in 2025 revenue across <b>300+ products</b>. "
    "The founder's challenge: <i>\"I have all this data but I don't know what to do with it. Tell me how to make more money.\"</i> "
    "We analyzed a full year of POS data (2025 + January 2026) across four dimensions: monthly revenue trends, "
    "product-level profitability, category performance, and branch efficiency to answer three strategic questions: "
    "<b>(1) Where is money being left on the table? (2) Which products and branches should be prioritized? "
    "(3) How should the 2025 expansion wave be evaluated?</b>",
    styles['Body']
))

# ============================================================
# 2. KEY FINDINGS
# ============================================================
story.append(Paragraph("2. Key Findings", styles['SectionHead']))

# Finding 1
story.append(Paragraph("<b>Finding 1: Severe Revenue Seasonality Creates a 6x Peak-to-Trough Gap</b>", styles['SubHead']))
story.append(Paragraph(
    f"Revenue swings dramatically through the year: August (peak) generated <b>5.9x</b> the revenue of June (trough). "
    f"The pattern shows a sharp dip in May-June (Ramadan/low season), a summer surge July-September driven by cold beverages and tourism, "
    f"and sustained strength October-December. This 6x volatility means staffing, inventory, and cash flow "
    f"planning must be seasonally adjusted. Fixed costs during June consume a disproportionate share of revenue.",
    styles['Body']
))

# Seasonality chart
img_path = f'{OUT_DIR}/01_seasonality.png'
if os.path.exists(img_path):
    story.append(Image(img_path, width=6.5*inch, height=2.6*inch))
    story.append(Spacer(1, 6))

# Finding 2
story.append(Paragraph("<b>Finding 2: Beverages Drive 62% of Profit at 77% Margins vs. Food at 63%</b>", styles['SubHead']))
story.append(Paragraph(
    f"Beverages account for <b>57%</b> of total revenue but <b>62%</b> of gross profit, operating at a <b>77.2% margin</b> "
    f"compared to Food's <b>63.0%</b>. This 14-point margin gap means every 1% shift in mix toward beverages "
    f"adds meaningful profit. Branches with higher beverage share (Event Starco 78%, Airport 64%, Batroun 63%) "
    f"consistently outperform on margin. Mall and university locations (Le Mall 49%, LAU 50%) skew toward food, "
    f"depressing their overall profitability.",
    styles['Body']
))

# Finding 3
story.append(Paragraph("<b>Finding 3: Combo Toppings Are a Hidden Profit Drain of ~23M Units</b>", styles['SubHead']))
story.append(Paragraph(
    "The frozen yoghurt combo system has a structural profitability problem. While yoghurt combos themselves are the "
    "<b>top revenue category</b> (183M), the associated combo toppings (Strawberry, Blueberries, Mango, Pineapple, "
    "Brownies, Oreo, etc.) are all <b>loss-making</b>. The top 10 loss-making items are exclusively combo toppings, "
    "collectively losing ~<b>23M in gross profit</b>. These toppings are priced as add-ons with zero standalone revenue "
    "but significant ingredient cost. The combo pricing model needs restructuring: either raise combo prices to cover "
    "topping costs, or reduce the number of included toppings.",
    styles['Body']
))

# Finding 4
story.append(Paragraph("<b>Finding 4: January 2026 Shows a Concerning YoY Decline Across All Established Branches</b>", styles['SubHead']))
story.append(Paragraph(
    f"Every established branch that existed in January 2025 saw a revenue decline in January 2026. "
    f"The average drop is <b>~42%</b>. While some of this may be explained by the denominator shifting (more branches "
    f"splitting the same market), even flagship locations like Ain El Mreisseh (-50%), Zalka (-45%), and "
    f"Khaldeh (-38%) saw steep drops. LAU (-60%) and Saida (-67%) are particularly alarming. "
    f"This requires urgent investigation: is this cannibalization from new branches, a macro-economic effect, "
    f"or competitive pressure?",
    styles['Body']
))

# ============================================================
# PAGE BREAK
# ============================================================
story.append(PageBreak())

# Finding 5
story.append(Paragraph("<b>Finding 5: 11 New Branches Opened in 2025 — Jbeil and Airport Are the Standout Performers</b>", styles['SubHead']))
story.append(Paragraph(
    "Stories aggressively expanded from ~14 to 25 branches in 2025. Among new openings, <b>Jbeil</b> (opened September) "
    "and <b>Airport</b> (opened June) showed the fastest ramp-ups, reaching top-10 monthly revenue within 2-3 months. "
    "Aley and Sour 2 (both July) stabilized at mid-tier performance. Late-2025 openings (Kaslik, Raouche, Amioun, "
    "Sin El Fil) have limited data but early signs are promising. The Event Starco location remains minimal, "
    "consistent with an events-only model.",
    styles['Body']
))

# New branches chart
img_path = f'{OUT_DIR}/11_new_branches.png'
if os.path.exists(img_path):
    story.append(Image(img_path, width=6.2*inch, height=2.8*inch))
    story.append(Spacer(1, 6))

# ============================================================
# 3. RECOMMENDATIONS
# ============================================================
story.append(Paragraph("3. Recommendations", styles['SectionHead']))

story.append(Paragraph("<b>R1. Restructure Frozen Yoghurt Combo Pricing (Impact: +23M profit recovery)</b>", styles['SubHead']))
story.append(Paragraph(
    "Increase base combo price by 10-15% to absorb topping costs, or limit included toppings to 2-3 per combo with "
    "premium toppings (brownies, Oreo, Lotus) priced as paid add-ons. This single change could recover the entire "
    "23M loss-making gap without reducing volume, as yoghurt combos have proven demand elasticity (they're the #1 category).",
    styles['Body']
))

story.append(Paragraph("<b>R2. Push Beverage Upsells at Food-Heavy Branches (Impact: +2-4% margin lift)</b>", styles['SubHead']))
story.append(Paragraph(
    "Branches where food exceeds 45% of revenue (Le Mall, Mansourieh, Antelias, LAU, Sin El Fil) should implement "
    "beverage-first promotions: combo deals pairing food with specialty drinks, barista recommendations at register, "
    "and seasonal beverage highlights. Target: shift mix 5% toward beverages at these locations. Additionally, "
    "train staff to suggest high-margin modifiers (extra shot at 73% margin, caramel drizzle at 90% margin).",
    styles['Body']
))

story.append(Paragraph("<b>R3. Seasonal Revenue Smoothing Strategy</b>", styles['SubHead']))
story.append(Paragraph(
    "June produces only 17% of peak-month revenue. Implement: (a) Ramadan-specific promotions and Iftar offerings "
    "in May-June, (b) loyalty program double-points during low season, (c) limited-time menu items to drive traffic. "
    "Target: lift June from 2% to 5% of annual revenue, worth ~28M incremental.",
    styles['Body']
))

story.append(Paragraph("<b>R4. Investigate and Address January 2026 Decline Urgently</b>", styles['SubHead']))
story.append(Paragraph(
    "The 42% average YoY decline in January is a red flag. Conduct: (a) cannibalization analysis mapping new branch "
    "catchment areas against existing branch declines, (b) competitive audit of new entrants, (c) customer survey "
    "on visit frequency changes. If cannibalization is confirmed, pause further expansion until existing branches "
    "stabilize.",
    styles['Body']
))

story.append(Paragraph("<b>R5. Double Down on Star Products</b>", styles['SubHead']))
story.append(Paragraph(
    "The top 5 profit-generating products (Mango/Original/Blueberry Yoghurt Combos, Water, Classic Cinnamon Roll) "
    "contribute ~107M in profit. Ensure these are never out of stock, prominently displayed, and featured in marketing. "
    "Water at 88% margin and 588K units is the silent profit champion — consider branded/premium water upsells.",
    styles['Body']
))

# ============================================================
# 4. EXPECTED IMPACT
# ============================================================
story.append(Paragraph("4. Expected Impact", styles['SectionHead']))

impact_data = [
    ['Recommendation', 'Estimated Annual Impact', 'Complexity'],
    ['Combo pricing restructure', '+23M profit recovery', 'Low (pricing change)'],
    ['Beverage mix optimization', '+15-30M incremental profit', 'Medium (training + promos)'],
    ['June revenue smoothing', '+28M incremental revenue', 'Medium (marketing)'],
    ['YoY decline investigation', 'Prevent further erosion', 'High (strategic)'],
    ['Star product focus', '+5-10M from availability', 'Low (operational)'],
]

t = Table(impact_data, colWidths=[2.5*inch, 2.2*inch, 2*inch])
t.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), ACCENT),
    ('TEXTCOLOR', (0, 0), (-1, 0), white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 9),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('GRID', (0, 0), (-1, -1), 0.5, LIGHT_GRAY),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#F9FAFB')]),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ('LEFTPADDING', (0, 0), (-1, -1), 8),
]))
story.append(t)
story.append(Spacer(1, 12))

# ============================================================
# 5. METHODOLOGY
# ============================================================
story.append(Paragraph("5. Methodology", styles['SectionHead']))
story.append(Paragraph(
    "We analyzed four POS data exports covering 2025 (full year) + January 2026: monthly revenue by branch (25 branches), "
    "product-level profitability (~14,600 line items, 550+ unique products), sales by product group (14,100 records "
    "across 36 groups), and category profit summaries. Data cleaning included: filtering POS page headers, "
    "normalizing inconsistent branch names, handling the Total Price display truncation bug (using Cost + Profit "
    "as true revenue where needed), and separating hierarchy levels (Branch > Service Type > Category > Section > Product). "
    "Analysis techniques: time-series decomposition for seasonality, menu engineering matrix (volume vs. margin quadrant analysis), "
    "YoY comparative analysis, branch efficiency scoring (profit per unit), and category mix analysis. "
    "All values are in arbitrary units; findings are based on patterns, ratios, and relative comparisons.",
    styles['Body']
))

story.append(Spacer(1, 16))
story.append(HRFlowable(width="100%", thickness=1, color=LIGHT_GRAY, spaceAfter=8))
story.append(Paragraph(
    "<i>Prepared for Stories Coffee leadership. Full analysis, code, and interactive visualizations available in the accompanying GitHub repository.</i>",
    styles['Small']
))

# Build PDF
doc.build(story)
print(f"✅ Executive Summary PDF created: {pdf_path}")
