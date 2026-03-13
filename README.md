# 🏎 PitWall Analytics Dashboard

**F1 Performance Data Subscription Platform — Subscriber Retention Intelligence**

An end-to-end analytics dashboard covering Descriptive, Diagnostic, Predictive, and Prescriptive views for a B2C SaaS platform delivering F1 telemetry insights to fans.

---

## 📊 Dashboard Tabs

| Tab | Focus | Methods Used |
|-----|-------|-------------|
| 📋 **Descriptive** | Who are our subscribers? | RFM Segmentation, Cohort Retention Heatmap, MRR Trends |
| 🔍 **Diagnostic** | Why are they churning? | Survival Analysis, CLV Distribution, Engagement Heatmaps |
| 🔮 **Predictive** | Who will churn next? | Random Forest Classifier, ROC/PR Curves, Feature Importance, CLV Forecast |
| 🎯 **Prescriptive** | What should we do? | Uplift Modelling, A/B Test Simulator, Priority Intervention Table |

---

## 🚀 Deploy on Streamlit Cloud

1. **Fork or upload this repo to GitHub**
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Set **Main file path** to: `app.py`
5. Click **Deploy**

---

## 💻 Run Locally

```bash
git clone <your-repo-url>
cd pitwall
pip install -r requirements.txt
streamlit run app.py
```

---

## 📁 Project Structure

```
pitwall/
├── app.py                    # Main Streamlit entry point
├── data_loader.py            # Data ingestion & feature engineering
├── theme.py                  # F1 colour palette, CSS, layout helpers
├── requirements.txt          # Python dependencies
├── data/
│   └── PitWall_Analytics_Dataset.xlsx
└── pages/
    ├── __init__.py
    ├── tab1_descriptive.py
    ├── tab2_diagnostic.py
    ├── tab3_predictive.py
    └── tab4_prescriptive.py
```

---

## 🔬 Analytical Methods

- **RFM Segmentation** — Recency, Frequency, Monetary scoring → 7 behavioural segments
- **Cohort Retention Analysis** — Monthly signup cohorts tracked across 12 months
- **Survival Analysis** — Kaplan-Meier style subscriber survival curves by plan tier
- **Random Forest Churn Classifier** — 12 features, 5-fold CV, ROC-AUC scored
- **CLV Forecasting** — 6-month predicted revenue = retention probability × monthly price
- **Uplift Modelling** — 4-quadrant Persuadables/Sure Things/Lost Causes/Sleeping Dogs
- **A/B Test Simulator** — Chi-squared significance testing with ROI projection
- **Feature Importance** — Gini-based ranking of churn predictors

---

*Dataset: Synthetic PitWall Analytics data — 800 subscribers, 29,240 sessions, 24 months MRR (2023–2024)*
