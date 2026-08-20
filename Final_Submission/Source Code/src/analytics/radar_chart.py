import numpy as np
import matplotlib.pyplot as plt

from src.screener.engine import ScreenerEngine


def generate_radar(company_id):
    engine = ScreenerEngine()

    peers = engine.compare_company(company_id)

    company = peers[
        peers["company_id"].str.upper() == company_id.upper()
    ]

    if company.empty:
        print("Company not found")
        return

    metrics = [
        "return_on_equity_pct",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "debt_to_equity",
        "free_cash_flow_cr",
    ]

    label_map = {
        "return_on_equity_pct": "ROE",
        "revenue_cagr_5yr": "Revenue CAGR",
        "pat_cagr_5yr": "PAT CAGR",
        "debt_to_equity": "D/E",
        "free_cash_flow_cr": "FCF",
    }

    labels = [label_map[m] for m in metrics]


    numeric = (
        peers[metrics]
        .replace("N/A", np.nan)
        .astype(float)
    )

    normalized = numeric.copy()

    for col in metrics:

        minimum = numeric[col].min()
        maximum = numeric[col].max()

        if maximum == minimum:
            normalized[col] = 50
        else:
            normalized[col] = (
                (numeric[col] - minimum)
                / (maximum - minimum)
            ) * 100

    # Lower debt is better
    normalized["debt_to_equity"] = (
        100 - normalized["debt_to_equity"]
    )

    company_index = company.index[0]

    company_values = normalized.loc[company_index]

    sector_average = normalized.mean()

    print("Company Values")
    print(company_values)

    print("\nSector Average")
    print(sector_average)


    company_data = company_values.values.tolist()
    sector_data = sector_average.values.tolist()

    # Close the radar chart
    company_data += company_data[:1]
    sector_data += sector_data[:1]
    
    angles = np.linspace(
        0,
        2 * np.pi,
        len(labels),
        endpoint=False
    ).tolist()

    angles += angles[:1]

    fig, ax = plt.subplots(
        figsize=(9, 9),
        subplot_kw=dict(polar=True)
    )

    ax.plot(
        angles,
        company_data,
        linewidth=2,
        label=company_id
    )

    ax.fill(
        angles,
        company_data,
        alpha=0.25
    )

    ax.plot(
        angles,
        sector_data,
        linewidth=2,
        linestyle="--",
        label="Sector Average"
    )

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)

    ax.set_title(
        f"{company_id} vs Sector Average",
        pad=30,
        fontsize=16
    )

    ax.legend(loc="upper right")

    plt.tight_layout()

    import os

    os.makedirs(
        "reports/radar_charts",
        exist_ok=True
    )

    output_path = f"reports/radar_charts/{company_id}_radar.png"

    plt.savefig(output_path)

    print(f"\nRadar chart saved to: {output_path}")

    plt.close()

def normalize(values, inverse=False):
    minimum = values.min()
    maximum = values.max()

    scaled = (values - minimum) / (maximum - minimum) * 100

    if inverse:
        scaled = 100 - scaled

    return scaled

if __name__ == "__main__":
    generate_radar("TCS")