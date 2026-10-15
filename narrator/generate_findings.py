"""
Capstone Project - MamaEarth Growth Intelligence Pipeline
Module: generate_findings.py
Task 1: Structured JSON of verified figures written strictly by code (Never hand-typed).
"""

import os
import json
import pandas as pd
import numpy as np


def compute_growth_intelligence_findings(data_dir: str = None) -> dict:
    """
    Computes verified growth telemetry figures directly from raw CSV files.
    Ensures mathematical reconciliation across revenue, duplicate orders,
    payment channels, and outlier-inflated sales.
    """
    if data_dir is None:
        # Check current directory, then parent directory
        if os.path.exists('orders.csv'):
            data_dir = '.'
        elif os.path.exists('../orders.csv'):
            data_dir = '..'
        elif os.path.exists('data/orders.csv'):
            data_dir = 'data'
        else:
            raise FileNotFoundError("Could not locate orders.csv in current or parent directory.")

    customers_path = os.path.join(data_dir, 'customers.csv')
    products_path = os.path.join(data_dir, 'products.csv')
    orders_path = os.path.join(data_dir, 'orders.csv')

    customers = pd.read_csv(customers_path)
    products = pd.read_csv(products_path)
    orders = pd.read_csv(orders_path)

    # 1. Join tables to form comprehensive order telemetry
    df = orders.merge(customers, on='customer_id', how='left').merge(products, on='product_id', how='left')

    # 2. Impute missing discounts (NULL discount = 0%)
    df['discount_pct_clean'] = df['discount_pct'].fillna(0)
    df['item_revenue'] = df['price'] * df['quantity'] * (1 - df['discount_pct_clean'] / 100.0)

    # Raw total revenue
    raw_total_revenue = round(float(df['item_revenue'].sum()), 1)

    # 3. Identify and reconcile duplicate payloads (same customer, product, date, qty, discount, rating, return)
    dup_mask = df.duplicated(
        subset=['customer_id', 'product_id', 'order_date', 'quantity', 'discount_pct', 'payment_method', 'rating', 'returned'], 
        keep='first'
    )
    duplicate_delta = round(float(df.loc[dup_mask, 'item_revenue'].sum()), 1)

    df_clean = df.loc[~dup_mask].copy()
    cleaned_total_revenue = round(float(df_clean['item_revenue'].sum()), 1)

    # 4. Standardize payment methods and calculate return rate by payment mode
    df_clean['payment_method_clean'] = df_clean['payment_method'].str.upper()
    ret_payment = df_clean.groupby('payment_method_clean')['returned'].mean() * 100
    return_rate_by_payment = {
        k: round(float(v), 1) for k, v in ret_payment.items()
    }

    # 5. Highest risk segment (Payment method x City Tier return rate)
    ret_segment = df_clean.groupby(['payment_method_clean', 'city_tier'])['returned'].mean() * 100
    highest_segment_idx = ret_segment.idxmax()
    highest_risk_segment = {
        "payment_method": highest_segment_idx[0],
        "city_tier": int(highest_segment_idx[1]),
        "return_rate_pct": round(float(ret_segment.max()), 1)
    }

    # 6. Monthly trend and Outlier vs True Organic Demand decomposition
    df_clean['month'] = pd.to_datetime(df_clean['order_date']).dt.to_period('M').astype(str)
    monthly_apparent = df_clean.groupby('month')['item_revenue'].sum()

    # Retail consumer demand (excluding bulk wholesale outliers >= 20 units)
    df_retail = df_clean[df_clean['quantity'] < 20]
    monthly_corrected = df_retail.groupby('month')['item_revenue'].sum()

    true_peak_month_name = str(monthly_corrected.idxmax())
    true_peak_month = {
        "month": true_peak_month_name,
        "revenue_inr": round(float(monthly_corrected.max()), 1)
    }

    outlier_month_name = str(monthly_apparent.idxmax())
    outlier_inflated_month = {
        "month": outlier_month_name,
        "apparent_revenue_inr": round(float(monthly_apparent[outlier_month_name]), 1),
        "corrected_revenue_inr": round(float(monthly_corrected[outlier_month_name]), 1)
    }

    findings = {
        "cleaned_total_revenue_inr": cleaned_total_revenue,
        "raw_total_revenue_inr": raw_total_revenue,
        "duplicate_reconciliation_delta_inr": duplicate_delta,
        "return_rate_by_payment": return_rate_by_payment,
        "highest_risk_segment": highest_risk_segment,
        "true_peak_month": true_peak_month,
        "outlier_inflated_month": outlier_inflated_month
    }

    return findings


def main():
    print("=" * 60)
    print("MAMAEARTH GROWTH INTELLIGENCE PIPELINE: FINDINGS GENERATOR")
    print("=" * 60)
    
    findings = compute_growth_intelligence_findings()

    # Determine output path in narrator directory
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(output_dir, 'findings.json')

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(findings, f, indent=2)

    print(f"\n[SUCCESS] Structured findings written to: {output_path}")
    print("\nVerified Telemetry Metrics:")
    print(json.dumps(findings, indent=2))
    print("=" * 60)


if __name__ == '__main__':
    main()
