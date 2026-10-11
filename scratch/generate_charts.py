import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set style
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams['font.sans-serif'] = 'Arial'
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['axes.linewidth'] = 0.8

# Ensure output directory exists
os.makedirs('visualizations', exist_ok=True)

# 1. Load Data
customers = pd.read_csv('customers.csv')
products = pd.read_csv('products.csv')
orders = pd.read_csv('orders.csv')

# Merge
df = orders.merge(customers, on='customer_id', how='left').merge(products, on='product_id', how='left')
df['discount_pct_clean'] = df['discount_pct'].fillna(0)
df['item_revenue'] = df['price'] * df['quantity'] * (1 - df['discount_pct_clean'] / 100.0)
df['payment_method_clean'] = df['payment_method'].str.upper()

# Identify Duplicates
dup_mask = df.duplicated(subset=['customer_id', 'product_id', 'order_date', 'quantity', 'discount_pct', 'payment_method', 'rating', 'returned'], keep='first')
df_clean = df.loc[~dup_mask].copy()
df_clean['month'] = pd.to_datetime(df_clean['order_date']).dt.to_period('M').astype(str)

# -------------------------------------------------------------
# Chart 1: Monthly Revenue Trend (Apparent vs Corrected)
# -------------------------------------------------------------
plt.figure(figsize=(10, 5.5), dpi=300)

monthly_apparent = df_clean.groupby('month')['item_revenue'].sum()
df_retail = df_clean[df_clean['quantity'] < 20]
monthly_corrected = df_retail.groupby('month')['item_revenue'].sum()

months = list(monthly_apparent.index)
x = np.arange(len(months))

plt.plot(x, monthly_apparent.values, marker='o', linewidth=2.5, color='#e74c3c', label='Apparent Revenue (with B2B Bulk Outliers)')
plt.plot(x, monthly_corrected.values, marker='s', linewidth=2.5, color='#2ecc71', linestyle='--', label='Corrected Organic Demand (Retail < 20 Qty)')

# Annotations
plt.annotate('Jan Spike (Bulk Qty 25 & 30):\n₹29,582.10', 
             xy=(0, monthly_apparent.values[0]), xytext=(0.2, 26000),
             arrowprops=dict(facecolor='#c0392b', shrink=0.08, width=1.5, headwidth=6),
             fontweight='bold', fontsize=9, color='#c0392b')

plt.annotate('True Peak Retail Demand:\nMarch 2026 (₹20,318.90)', 
             xy=(2, monthly_corrected.values[2]), xytext=(1.8, 15000),
             arrowprops=dict(facecolor='#27ae60', shrink=0.08, width=1.5, headwidth=6),
             fontweight='bold', fontsize=9, color='#27ae60')

plt.title('Monthly Revenue Trajectory: Outlier Inflation vs True Demand', fontsize=14, fontweight='bold', pad=15)
plt.xlabel('Month', fontsize=11, labelpad=10)
plt.ylabel('Net Revenue (INR ₹)', fontsize=11, labelpad=10)
plt.xticks(x, months)
plt.ylim(5000, 32000)
plt.legend(frameon=True, facecolor='white', framealpha=0.9)
plt.tight_layout()
plt.savefig('visualizations/monthly_revenue_trend.png')
plt.close()

# -------------------------------------------------------------
# Chart 2: Return Rate by Payment Method
# -------------------------------------------------------------
plt.figure(figsize=(8, 5), dpi=300)
ret_pay = df_clean.groupby('payment_method_clean')['returned'].mean() * 100
colors = ['#3498db', '#e74c3c', '#2ecc71']

bars = plt.bar(ret_pay.index, ret_pay.values, color=colors, width=0.5, edgecolor='#333333', linewidth=1)
plt.axhline(20, color='gray', linestyle=':', label='High Risk Threshold (20%)')

for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2.0, yval + 1.2, f'{yval:.1f}%', ha='center', va='bottom', fontweight='bold', fontsize=11)

plt.title('Return Rate by Payment Channel: Severe COD Vulnerability', fontsize=13, fontweight='bold', pad=15)
plt.xlabel('Payment Method', fontsize=11, labelpad=10)
plt.ylabel('Return Rate (%)', fontsize=11, labelpad=10)
plt.ylim(0, 52)
plt.legend(loc='upper left')
plt.tight_layout()
plt.savefig('visualizations/return_rate_by_payment.png')
plt.close()

# -------------------------------------------------------------
# Chart 3: Risk Segment Heatmap (Payment Method × City Tier)
# -------------------------------------------------------------
plt.figure(figsize=(7, 4.5), dpi=300)
heatmap_data = df_clean.pivot_table(index='payment_method_clean', columns='city_tier', values='returned', aggfunc='mean') * 100
heatmap_data.columns = ['Tier 1 (Metro)', 'Tier 2 (Emerging)']

sns.heatmap(heatmap_data, annot=True, fmt='.1f', cmap='YlOrRd', cbar_kws={'label': 'Return Rate (%)'}, linewidths=1.5, linecolor='white', annot_kws={"size": 13, "weight": "bold"})
plt.title('Return Risk Matrix: Payment Method × City Tier', fontsize=13, fontweight='bold', pad=15)
plt.xlabel('City Tier', fontsize=11, labelpad=10)
plt.ylabel('Payment Method', fontsize=11, labelpad=10)
plt.tight_layout()
plt.savefig('visualizations/risk_segment_heatmap.png')
plt.close()

# -------------------------------------------------------------
# Chart 4: Product Category Performance
# -------------------------------------------------------------
cat_perf = df_clean.groupby('category').agg(
    Revenue=('item_revenue', 'sum'),
    Orders=('order_id', 'count')
).sort_values(by='Revenue', ascending=True)

fig, ax1 = plt.subplots(figsize=(9, 5), dpi=300)
y_pos = np.arange(len(cat_perf))
bar_width = 0.4

b1 = ax1.barh(y_pos - bar_width/2, cat_perf['Revenue'], bar_width, label='Net Revenue (₹)', color='#1abc9c', edgecolor='#333')
ax2 = ax1.twiny()
b2 = ax2.barh(y_pos + bar_width/2, cat_perf['Orders'], bar_width, label='Order Count', color='#34495e', edgecolor='#333')

ax1.set_yticks(y_pos)
ax1.set_yticklabels(cat_perf.index, fontsize=11, fontweight='bold')
ax1.set_xlabel('Net Revenue (INR ₹)', color='#1abc9c', fontsize=11, labelpad=8)
ax2.set_xlabel('Total Orders', color='#34495e', fontsize=11, labelpad=8)
plt.title('Product Category Breakdown: Revenue vs Order Volume', fontsize=13, fontweight='bold', pad=25)

# Legends
lines = [b1, b2]
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='lower right')

plt.tight_layout()
plt.savefig('visualizations/category_performance.png')
plt.close()

# -------------------------------------------------------------
# Chart 5: Customer Acquisition Channel Breakdown
# -------------------------------------------------------------
plt.figure(figsize=(8, 4.5), dpi=300)
acq_data = df_clean.groupby('acquisition_source').agg(
    Total_Spend=('item_revenue', 'sum'),
    Order_Count=('order_id', 'count')
).sort_values(by='Total_Spend', ascending=False)

bars = plt.bar(acq_data.index, acq_data['Total_Spend'], color='#8e44ad', width=0.55, edgecolor='#333')
for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2.0, yval + 500, f'₹{yval:,.0f}', ha='center', va='bottom', fontweight='bold', fontsize=10)

plt.title('Revenue Contribution by Customer Acquisition Source', fontsize=13, fontweight='bold', pad=15)
plt.xlabel('Acquisition Channel', fontsize=11, labelpad=10)
plt.ylabel('Total Net Revenue (INR ₹)', fontsize=11, labelpad=10)
plt.ylim(0, max(acq_data['Total_Spend']) * 1.15)
plt.tight_layout()
plt.savefig('visualizations/customer_acquisition_breakdown.png')
plt.close()

print("All 5 publication-grade visualizations successfully generated in visualizations/ folder!")
