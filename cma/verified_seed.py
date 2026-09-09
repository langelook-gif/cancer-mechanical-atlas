from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

def load_verified_studies():
    return pd.read_csv(DATA / "verified_gbm_studies.csv")

def load_verified_measurements():
    return pd.read_csv(DATA / "verified_gbm_measurements.csv")

def seed_verified_measurements(conn):
    """
    Load the manually verified GBM starter measurements.

    Existing matching starter measurements are upgraded to
    evidence_level='verified'.

    Missing starter measurements are inserted.

    Machine-extracted measurements from later PubMed searches
    are NOT automatically verified.
    """

    df = load_verified_measurements().copy()

    # These rows come specifically from our manually checked
    # verified starter-measurement file.
    df["evidence_level"] = "verified"

    # --------------------------------------------------------
    # 1. UPDATE VERIFIED STARTER ROWS THAT ALREADY EXIST
    # --------------------------------------------------------

    for _, r in df.iterrows():

        pmid = str(r["pmid"])
        property_name = str(r["property_name"])

        tissue_context = (
            ""
            if pd.isna(r["tissue_context"])
            else str(r["tissue_context"])
        )

        normalized_value = float(
            r["normalized_value"]
        )

        conn.execute(
            """
            UPDATE measurements

            SET evidence_level = 'verified'

            WHERE CAST(pmid AS TEXT) = ?
              AND property_name = ?
              AND COALESCE(tissue_context, '') = ?
              AND ABS(normalized_value - ?) < 1e-9
            """,
            (
                pmid,
                property_name,
                tissue_context,
                normalized_value,
            )
        )

    conn.commit()

    # --------------------------------------------------------
    # 2. READ THE DATABASE AFTER THE UPDATE
    # --------------------------------------------------------

    existing = pd.read_sql_query(
        """
        SELECT
            pmid,
            property_name,
            tissue_context,
            normalized_value,
            evidence_level

        FROM measurements
        """,
        conn,
    )

    # --------------------------------------------------------
    # 3. BUILD A SET OF EXISTING MEASUREMENT KEYS
    # --------------------------------------------------------

    keys = set()

    for _, r in existing.iterrows():

        tissue_context = (
            ""
            if pd.isna(r["tissue_context"])
            else str(r["tissue_context"])
        )

        key = (
            str(r["pmid"]),
            str(r["property_name"]),
            tissue_context,
            round(
                float(r["normalized_value"]),
                12
            ),
        )

        keys.add(key)

    # --------------------------------------------------------
    # 4. INSERT VERIFIED STARTER ROWS THAT ARE STILL MISSING
    # --------------------------------------------------------

    keep = []

    for _, r in df.iterrows():

        tissue_context = (
            ""
            if pd.isna(r["tissue_context"])
            else str(r["tissue_context"])
        )

        key = (
            str(r["pmid"]),
            str(r["property_name"]),
            tissue_context,
            round(
                float(r["normalized_value"]),
                12
            ),
        )

        if key not in keys:
            keep.append(r)

    if keep:

        pd.DataFrame(
            keep
        ).to_sql(
            "measurements",
            conn,
            if_exists="append",
            index=False
        )

        conn.commit()

    return len(keep)
