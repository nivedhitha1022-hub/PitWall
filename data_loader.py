import pandas as pd
import numpy as np
from pathlib import Path

def load_data():

    DATA_PATH = Path(__file__).parent / "PitWall_Analytics_Dataset.xlsx"

    xl = pd.read_excel(DATA_PATH, sheet_name=None, header=1)

    # -----------------------
    # Subscribers
    # -----------------------
    subs = xl["Subscribers"].copy()
    subs.columns = [c.lower().replace(" ", "_") for c in subs.columns]

    subs["signup_date"] = pd.to_datetime(subs["signup_date"], errors="coerce")
    subs["churn_date"] = pd.to_datetime(subs["churn_date"], errors="coerce")

    subs["churned_bool"] = (subs["churned"] == "Yes").astype(int)
    subs["churn_reason"] = subs["churn_reason"].fillna("Not Churned")

    today = pd.Timestamp("2024-12-31")

    subs["tenure_months"] = subs.apply(
        lambda r: round(
            ((r["churn_date"] if pd.notna(r["churn_date"]) else today) - r["signup_date"]).days / 30.44,
            1
        ) if pd.notna(r["signup_date"]) else np.nan,
        axis=1
    )

    subs["lifetime_revenue_usd"] = (subs["tenure_months"] * subs["monthly_price_usd"]).round(2)

    subs["nps_category"] = pd.cut(
        subs["nps_score"],
        bins=[-1, 6, 8, 10],
        labels=["Detractor", "Passive", "Promoter"]
    )

    subs["age_group"] = pd.cut(
        subs["age"],
        bins=[17, 24, 34, 44, 54, 80],
        labels=["18-24", "25-34", "35-44", "45-54", "55+"]
    )

    subs["cohort_month"] = subs["signup_date"].dt.to_period("M").astype(str)

    subs["plan_order"] = subs["plan"].map({
        "Pit Lane": 1,
        "Podium": 2,
        "Paddock Club": 3
    })

    # -----------------------
    # Engagement Sessions
    # -----------------------
    sess = xl["Engagement Sessions"].copy()
    sess.columns = [c.lower().replace(" ", "_") for c in sess.columns]

    sess["session_date"] = pd.to_datetime(sess["session_date"], errors="coerce")
    sess["session_month"] = sess["session_date"].dt.to_period("M").astype(str)
    sess["is_weekend"] = sess["session_date"].dt.dayofweek >= 5

    sess["engagement_tier"] = pd.cut(
        sess["engagement_score"],
        bins=[-1, 39, 69, 100],
        labels=["Low", "Medium", "High"]
    )

    # -----------------------
    # Revenue MRR
    # -----------------------
    mrr = xl["Revenue MRR"].copy()
    mrr.columns = [c.lower().replace(" ", "_") for c in mrr.columns]

    mrr["month_dt"] = pd.to_datetime(mrr["month"], format="%Y-%m", errors="coerce")

    mrr["churn_rate_pct"] = (
        mrr["churned_subscribers"] /
        (mrr["active_subscribers"] + mrr["churned_subscribers"]).replace(0, np.nan)
        * 100
    ).round(2)

    mrr["arpu_usd"] = (
        mrr["mrr_usd"] /
        mrr["active_subscribers"].replace(0, np.nan)
    ).round(2)

    # -----------------------
    # RFM Segmentation
    # -----------------------
    snapshot = pd.Timestamp("2024-12-31")

    last_sess = sess.groupby("subscriber_id")["session_date"].max().reset_index()
    last_sess.columns = ["subscriber_id", "last_session"]

    freq = sess.groupby("subscriber_id").size().reset_index(name="frequency")

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

    rfm["r_score"] = pd.qcut(rfm["recency_days"].rank(method="first"), 4, labels=[4,3,2,1]).astype(int)
    rfm["f_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 4, labels=[1,2,3,4]).astype(int)
    rfm["m_score"] = pd.qcut(rfm["monetary"].rank(method="first"), 4, labels=[1,2,3,4]).astype(int)

    rfm["rfm_score"] = rfm["r_score"] + rfm["f_score"] + rfm["m_score"]

    def segment(row):
        s, r = row["rfm_score"], row["r_score"]

        if s >= 10:
            return "Champion"
        elif s >= 8:
            return "Loyal"
        elif r >= 3 and s >= 6:
            return "Potential Loyalist"
        elif r >= 3:
            return "Recent"
        elif s >= 6:
            return "At Risk"
        elif s >= 4:
            return "Needs Attention"
        else:
            return "Lost"

    rfm["segment"] = rfm.apply(segment, axis=1)

    return subs, sess, mrr, rfm
