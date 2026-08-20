import os
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

DB_PATH = "data/nifty100.db"
OUTPUT_DIR = "output"
REPORTS_DIR = "reports"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

def run_clustering():
    conn = sqlite3.connect(DB_PATH)
    companies = pd.read_sql("SELECT company_id, ticker, name, sector FROM companies", conn)
    # Using 2024 (latest year) ratios
    ratios = pd.read_sql("""
        SELECT company_id, year, roe, de, revenue_cagr_5yr, opm
        FROM ratios
        WHERE year = 2024
    """, conn)

    # ratios contains duplicate rows for some companies.
    # Keep one identical record per company for clustering.
    ratios = ratios.drop_duplicates(
        subset=["company_id", "year"]
    )

    print("Ratios after deduplication:", len(ratios))
    print("Unique ratio companies:", ratios["company_id"].nunique())
        
    # fcf_cagr_5yr was generated in cashflow_kpis.py and saved in cashflow_intelligence.xlsx
    # Let's load it and merge it
    cf_intel = pd.read_excel("output/cashflow_intelligence.xlsx")

    cf_intel = cf_intel[
        ["company_id", "fcf_cagr_5yr"]
    ].drop_duplicates(
        subset=["company_id"]
    )

    print("Cashflow companies:", cf_intel["company_id"].nunique())

    # Keep one FCF CAGR value per company
    cf_intel = (
        cf_intel[["company_id", "fcf_cagr_5yr"]]
        .drop_duplicates("company_id")
    )
    
    df = pd.merge(
        companies,
        ratios,
        on="company_id",
        how="left",
        validate="one_to_one"
    )

    df = pd.merge(
        df,
        cf_intel,
        on="company_id",
        how="left",
        validate="one_to_one"
    )

    print("\nFinal clustering dataset:")
    print("Rows:", len(df))
    print("Unique companies:", df["company_id"].nunique())

    if len(df) != df["company_id"].nunique():
        raise ValueError("Duplicate company IDs found after merging!")

    features = ['roe', 'de', 'revenue_cagr_5yr', 'fcf_cagr_5yr', 'opm']
    
    # 1. Impute missing values with sector medians
    for feature in features:
        df[feature] = df.groupby('sector')[feature].transform(lambda x: x.fillna(x.median()))
        # If any sector median is also NaN, fill with overall median
        df[feature] = df[feature].fillna(df[feature].median())
        
    X = df[features].copy()
    
    # 2. StandardScaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 3. Elbow Plot
    inertias = []
    K_range = range(2, 11)
    for k in K_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(X_scaled)
        inertias.append(kmeans.inertia_)
        
    plt.figure(figsize=(8, 5))
    plt.plot(K_range, inertias, marker='o', linestyle='--')
    plt.title('KMeans Elbow Plot')
    plt.xlabel('Number of Clusters (k)')
    plt.ylabel('Inertia')
    plt.grid(True)
    plt.savefig(os.path.join(REPORTS_DIR, 'elbow_plot.png'))
    plt.close()
    
    # 4. KMeans with k=5
    kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
    df['cluster_id'] = kmeans.fit_predict(X_scaled)
    
    # Calculate distance from centroid
    centroids = kmeans.cluster_centers_
    distances = []
    for i, row in enumerate(X_scaled):
        cluster = df.loc[i, 'cluster_id']
        dist = np.linalg.norm(row - centroids[cluster])
        distances.append(dist)
    df['distance_from_centroid'] = distances
    
    # 5. Profiling - assign names
    # Compute median of each feature per cluster to decide names
    cluster_profiles = df.groupby('cluster_id')[features].median()
    print("\nCluster Profiles:")
    print(cluster_profiles.round(2))

    names = {}
    for cid in range(5):
        prof = cluster_profiles.loc[cid]
        # Heuristics for naming based on medians
        if prof['roe'] > 20 and prof['revenue_cagr_5yr'] > 15:
            names[cid] = "High-Quality Compounders"
        elif prof['de'] < 0.5 and prof['opm'] > 20:
            names[cid] = "Defensive Cash Cows"
        elif prof['roe'] < 10 and prof['de'] > 1.0:
            names[cid] = "Distressed / Turnaround"
        elif prof['revenue_cagr_5yr'] > 20 and prof['roe'] < 15:
            names[cid] = "Emerging Growth"
        else:
            names[cid] = "Value Cyclicals"
            
    # Ensure unique names if heuristics overlap
    used = set()
    for cid in range(5):
        base_name = names[cid]
        if base_name in used:
            names[cid] = base_name + f" (Type {cid+1})"
        used.add(names[cid])
        
    df['cluster_name'] = df['cluster_id'].map(names)
    
    out_cols = ['company_id', 'cluster_id', 'cluster_name', 'distance_from_centroid']
    df[out_cols].to_csv(os.path.join(OUTPUT_DIR, 'cluster_labels.csv'), index=False)
    
    print("✅ KMeans Clustering Complete (k=5).")
    print(f"✅ Saved reports/elbow_plot.png and output/cluster_labels.csv")
    
    # --- DAY 37 PROFILING ---
    
    # Correlation Heatmap (10 KPIs)
    # Let's fetch 10 KPIs for the latest year
    kpis = pd.read_sql("""
        SELECT
            company_id,
            roe,
            roce,
            pe,
            pb,
            ev_ebitda,
            de,
            opm,
            npm,
            revenue_cagr_5yr,
            pat_cagr_5yr
        FROM ratios
        WHERE year = 2024
    """, conn)

    kpis = kpis.drop_duplicates(
        subset=["company_id"]
    )
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(kpis.corr(method='pearson'), annot=True, cmap='coolwarm', fmt=".2f")
    plt.title("Pearson Correlation of 10 KPIs (FY24)")
    plt.tight_layout()
    plt.savefig(os.path.join(REPORTS_DIR, 'correlation_heatmap.png'))
    plt.close()
    
    # Outlier Detection (Z-score > 3 per broad_sector)
    kpis = pd.read_sql("""
        SELECT company_id, roe, roce, pe, pb, ev_ebitda,
            de, opm, npm, revenue_cagr_5yr, pat_cagr_5yr
        FROM ratios
        WHERE year=2024
    """, conn)

    full_df = pd.merge(
        companies,
        kpis,
        on="company_id",
        how="left",
        validate="one_to_one"
    )
    outliers = []
    
    for sector in full_df['sector'].unique():
        sec_df = full_df[full_df['sector'] == sector]
        for col in kpis.columns:
            mean = sec_df[col].mean()
            std = sec_df[col].std()
            if pd.notna(std) and std > 0:
                z_scores = (sec_df[col] - mean) / std
                outlier_mask = z_scores.abs() > 3
                if outlier_mask.any():
                    for idx, val in sec_df[outlier_mask].iterrows():
                        outliers.append({
                            'company_id': val['company_id'],
                            'ticker': val['ticker'],
                            'sector': sector,
                            'metric': col,
                            'value': val[col],
                            'z_score': z_scores[idx]
                        })
                        
    outlier_df = pd.DataFrame(outliers)
    if not outlier_df.empty:
        outlier_df.to_csv(os.path.join(OUTPUT_DIR, 'outlier_report.csv'), index=False)
    else:
        # Create empty if none
        pd.DataFrame(columns=['company_id', 'ticker', 'sector', 'metric', 'value', 'z_score']).to_csv(os.path.join(OUTPUT_DIR, 'outlier_report.csv'), index=False)
        
    # Portfolio Stats P10 to P90
    stats = []
    for col in kpis.columns:
        s = kpis[col].dropna()
        if not s.empty:
            stats.append({
                'KPI': col,
                'Mean': s.mean(),
                'Std': s.std(),
                'P10': s.quantile(0.1),
                'P25': s.quantile(0.25),
                'P50': s.median(),
                'P75': s.quantile(0.75),
                'P90': s.quantile(0.9)
            })
            
    stats_df = pd.DataFrame(stats)
    stats_df.to_csv(os.path.join(OUTPUT_DIR, 'portfolio_stats.csv'), index=False)
    
    print("✅ Cluster Profiling & Statistics Complete.")
    print("✅ Saved correlation_heatmap.png, outlier_report.csv, portfolio_stats.csv")
    conn.close()

if __name__ == "__main__":
    run_clustering()
