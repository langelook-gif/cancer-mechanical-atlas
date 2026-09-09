from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

def load_verified_studies():
    return pd.read_csv(DATA / "verified_gbm_studies.csv")

def load_verified_measurements():
    return pd.read_csv(DATA / "verified_gbm_measurements.csv")

def seed_verified_measurements(conn):
    """Insert the manually verified starter measurements once, by PMID/property/context/value."""
    df = load_verified_measurements()
    existing = pd.read_sql_query(
        "SELECT pmid, property_name, tissue_context, normalized_value, evidence_level FROM measurements",
        conn,
    )
    if existing.empty:
        df.to_sql("measurements", conn, if_exists="append", index=False)
        conn.commit()
        return len(df)

    keys = set(
        zip(
            existing["pmid"].astype(str),
            existing["property_name"].astype(str),
            existing["tissue_context"].astype(str),
            existing["normalized_value"].astype(float).round(12),
        )
    )
    keep = []
    for _, r in df.iterrows():
        k = (str(r.pmid), str(r.property_name), str(r.tissue_context), round(float(r.normalized_value), 12))
        if k not in keys:
            keep.append(r)
    if keep:
        pd.DataFrame(keep).to_sql("measurements", conn, if_exists="append", index=False)
        conn.commit()
    return len(keep)
