import pandas as pd
import numpy as np
from pathlib import Path


def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    return df


def _safe_qcut(series: pd.Series, labels) -> pd.Series:
    ranked = series.rank(method="first")
    return pd.qcut(ranked, q=len(labels), labels=labels, duplicates="drop").astype(int)


def load_data():
    data_path = Path(__file__).parent / "PitWall_Analytics_Dataset.xlsx"

    if not data_path.exists():
        raise FileNotFoundError(
            f"Dataset not found at: {data_path}. "
            "Make sure PitWall_Analytics_Dataset.xlsx is in the same folder as app.py and data_loader.py."
        )

    xl = pd.read_excel(data_path, sheet_name=None, header=1)

    required_sheets = ["Subscribers", "Engagement Sessions", "Revenue MRR"]
    missing_sheets = [sheet for sheet in required_sheets if sheet not in xl]
    if missing_sheets:
        raise ValueError(f"Missing required sheet(s): {', '.join(missing_sheets)}")

    # -----------------------
    # Subscribers
    # -----------------------
    subs = _clean_columns(xl["Subscribers"])

    subs["signup_date"] = pd.to_datetime(subs.get("signup_date"), errors="coerce")
    subs["churn_date"] = pd.to_datetime(subs.get("churn_date"), errors="coerce")

    subs["churned"] = subs["churned"].fillna("No").astype(str).str.strip()
    subs["churned_bool"] = subs["churned"].eq("Yes").astype(int)

    if "churn_reason" in subs.columns:
        subs["churn_reason"] = subs["churn_reason"].fillna("Not Churned")
    else:
        subs["churn_reason"] = "Not Churned"

    today = pd.Timestamp("2024-12-31")

    subs["tenure_months"] = subs.apply(
        lambda r: round(
            (
                (r["churn_date"] if pd.notna(r["churn_date"]) else today) - r["signup_date"]
            ).days / 30.44,
            1,
        )
        if pd.notna(r["signup_date"])
        else np.nan,
        axis=1,
    )

    subs["monthly_price_usd"] = pd.to_numeric(subs["monthly_price_usd"], errors="coerce")
    subs["nps_score"] = pd.to_numeric(subs["nps_score"], errors="coerce")
    subs["age"] = pd.to_numeric(subs["age"], errors="coerce")

    subs["lifetime_revenue_usd"] = (subs["tenure_months"] * subs["monthly_price_usd"]).round(2)

    subs["nps_category"] = pd.cut(
        subs["nps_score"],
        bins=[-1, 6, 8, 10],
        labels=["Detractor", "Passive", "Promoter"],
    )

    subs["age_group"] = pd.cut(
        subs["age"],
        bins=[17, 24, 34, 44, 54, 80],
        labels=["18-24", "25-34", "35-44", "45-54", "55+"],
    )

    subs["cohort_month"] = subs["signup_date"].dt.to_period("M").astype(str)

    subs["plan"] = subs["plan"].fillna("Unknown").astype(str).str.strip()
    subs["region"] = subs["region"].fillna("Unknown").astype(str).str.strip()
    subs["acquisition_channel"] = (
        subs["acquisition_channel"].fillna("Unknown").astype(str).str.strip()
    )

    subs["plan_order"] = subs["plan"].map(
        {"Pit Lane": 1, "Podium": 2, "Paddock Club": 3}
    ).fillna(99)

    # -----------------------
    # Engagement Sessions
    # -----------------------
    sess = _clean_columns(xl["Engagement Sessions"])

    sess["session_date"] = pd.to_datetime(sess.get("session_date"), errors="coerce")
    sess["engagement_score"] = pd.to_numeric(sess["engagement_score"], errors="coerce")

    sess["session_month"] = sess["session_date"].dt.to_period("M").astype(str)
    sess["is_weekend"] = sess["session_date"].dt.dayofweek >= 5

    sess["engagement_tier"] = pd.cut(
        sess["engagement_score"],
        bins=[-1, 39, 69, 100],
        labels=["Low", "Medium", "High"],
    )

    # -----------------------
    # Revenue MRR
    # -----------------------
    mrr = _clean_columns(xl["Revenue MRR"])

    mrr["month_dt"] = pd.to_datetime(mrr["month"], format="%Y-%m", errors="coerce")
    mrr["mrr_usd"] = pd.to_numeric(mrr["mrr_usd"], errors="coerce")
    mrr["active_subscribers"] = pd.to_numeric(mrr["active_subscribers"], errors="coerce")
    mrr["churned_subscribers"] = pd.to_numeric(mrr["churned_subscribers"], errors="coerce")

    denom = (mrr["active_subscribers"] + mrr["churned_subscribers"]).replace(0, np.nan)

    mrr["churn_rate_pct"] = ((mrr["churned_subscribers"] / denom) * 100).round(2)
    mrr["arpu_usd"] = (
        mrr["mrr_usd"] / mrr["active_subscribers"].replace(0, np.nan)
    ).round(2)

    # -----------------------
    # RFM Segmentation
    # -----------------------
    snapshot = pd.Timestamp("2024-12-31")

    last_sess = sess.groupby("subscriber_id", as_index=False)["session_date"].max()
    last_sess.columns = ["subscriber_id", "last_session"]

    freq = sess.groupby("subscriber_id", as_index=False).size()
    freq.columns = ["subscriber_id", "frequency"]

    rfm = subs[
        [
            "subscriber_id",
            "lifetime_revenue_usd",
            "churned",
            "plan",
            "region",
            "nps_score",
            "tenure_months",
            "monthly_price_usd",
            "churned_bool",
            "nps_category",
            "age_group",
            "acquisition_channel",
        ]
    ].merge(last_sess, on="subscriber_id", how="left").merge(freq, on="subscriber_id", how="left")

    rfm["recency_days"] = (snapshot - rfm["last_session"]).dt.days.fillna(999)
    rfm["frequency"] = rfm["frequency"].fillna(0)
    rfm["monetary"] = rfm["lifetime_revenue_usd"].fillna(0)

    rfm["r_score"] = _safe_qcut(rfm["recency_days"], [4, 3, 2, 1])
    rfm["f_score"] = _safe_qcut(rfm["frequency"], [1, 2, 3, 4])
    rfm["m_score"] = _safe_qcut(rfm["monetary"], [1, 2, 3, 4])

    rfm["rfm_score"] = rfm["r_score"] + rfm["f_score"] + rfm["m_score"]

    def segment(row):
        s = row["rfm_score"]
        r = row["r_score"]

        if s >= 10:
            return "Champion"
        if s >= 8:
            return "Loyal"
        if r >= 3 and s >= 6:
            return "Potential Loyalist"
        if r >= 3:
            return "Recent"
        if s >= 6:
            return "At Risk"
        if s >= 4:
            return "Needs Attention"
        return "Lost"

    rfm["segment"] = rfm.apply(segment, axis=1)

    return subs, sess, mrr, rfm
