# ── F1 Colour Palette ────────────────────────────────────────────────────────
F1_RED = "#E8002D"
F1_BLACK = "#0A0A0A"
F1_WHITE = "#F5F5F5"
F1_SILVER = "#9B9B9B"
F1_GOLD = "#FFD700"
F1_GREY = "#1C1C1C"
F1_DGREY = "#141414"
F1_LGREY = "#2A2A2A"

ACCENT_BLUE = "#00B4D8"
ACCENT_GREEN = "#06D6A0"
ACCENT_AMBER = "#FFB703"

PLAN_COLORS = {
    "Pit Lane": "rgb(155,155,155)",
    "Podium": "rgb(232,0,45)",
    "Paddock Club": "rgb(255,215,0)",
}

SEGMENT_COLORS = {
    "Champion": "rgb(255,215,0)",
    "Loyal": "rgb(6,214,160)",
    "Potential Loyalist": "rgb(0,180,216)",
    "Recent": "rgb(144,224,239)",
    "At Risk": "rgb(255,183,3)",
    "Needs Attention": "rgb(251,133,0)",
    "Lost": "rgb(232,0,45)",
}

REGION_COLORS = [
    "rgb(232,0,45)",
    "rgb(255,215,0)",
    "rgb(0,180,216)",
    "rgb(6,214,160)",
    "rgb(255,183,3)",
    "rgb(155,155,155)",
]


# ── Plotly base layout ───────────────────────────────────────────────────────
def base_layout(title="", height=420):
    return dict(
        title=dict(
            text=title,
            font=dict(color=F1_WHITE, size=16, family="Arial Black"),
            x=0.01,
        ),
        paper_bgcolor=F1_GREY,
        plot_bgcolor=F1_DGREY,
        font=dict(color=F1_SILVER, family="Arial", size=12),
        height=height,
        margin=dict(l=40, r=20, t=50, b=40),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=F1_SILVER),
        ),
        xaxis=dict(
            gridcolor="#2E2E2E",
            linecolor="#3A3A3A",
            zerolinecolor="#3A3A3A",
        ),
        yaxis=dict(
            gridcolor="#2E2E2E",
            linecolor="#3A3A3A",
            zerolinecolor="#3A3A3A",
        ),
    )


# ── Streamlit CSS injection ───────────────────────────────────────────────────
F1_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Titillium+Web:wght@400;600;700;900&display=swap');

  html, body, [class*="css"] {
      font-family: 'Titillium Web', sans-serif !important;
      background-color: #0A0A0A;
      color: #F5F5F5;
  }

  [data-testid="stAppViewContainer"] {
      background-color: #0A0A0A;
  }

  [data-testid="stSidebar"] {
      background-color: #111111 !important;
      border-right: 2px solid #E8002D;
  }

  [data-testid="stSidebar"] * {
      color: #F5F5F5 !important;
  }

  [data-testid="stTabs"] button {
      font-family: 'Titillium Web', sans-serif !important;
      font-weight: 700;
      font-size: 14px;
      color: #9B9B9B !important;
      border-bottom: 3px solid transparent;
      padding: 10px 20px;
  }

  [data-testid="stTabs"] button[aria-selected="true"] {
      color: #E8002D !important;
      border-bottom: 3px solid #E8002D !important;
  }

  [data-testid="stTabsContent"] {
      background-color: #0A0A0A;
  }

  [data-testid="metric-container"] {
      background: linear-gradient(135deg, #1C1C1C 0%, #141414 100%);
      border: 1px solid #2A2A2A;
      border-left: 3px solid #E8002D;
      border-radius: 6px;
      padding: 12px 16px;
  }

  [data-testid="metric-container"] label {
      color: #9B9B9B !important;
      font-size: 12px !important;
      letter-spacing: 1px;
      text-transform: uppercase;
  }

  [data-testid="metric-container"] [data-testid="stMetricValue"] {
      color: #F5F5F5 !important;
      font-size: 26px !important;
      font-weight: 900;
  }

  [data-testid="metric-container"] [data-testid="stMetricDelta"] {
      font-size: 12px !important;
  }

  h1 {
      color: #E8002D !important;
      font-weight: 900 !important;
      letter-spacing: 2px;
  }

  h2 {
      color: #F5F5F5 !important;
      font-weight: 700 !important;
      border-bottom: 1px solid #2A2A2A;
      padding-bottom: 6px;
  }

  h3 {
      color: #9B9B9B !important;
      font-weight: 600 !important;
  }

  [data-testid="stDataFrame"] {
      border: 1px solid #2A2A2A;
      border-radius: 6px;
  }

  hr {
      border-color: #2A2A2A !important;
  }

  .insight-box {
      background: linear-gradient(135deg, #1C1C1C, #141414);
      border-left: 4px solid #E8002D;
      border-radius: 4px;
      padding: 14px 18px;
      margin: 8px 0;
      font-size: 14px;
      line-height: 1.6;
  }

  .insight-box b {
      color: #E8002D;
  }

  .section-label {
      font-size: 11px;
      letter-spacing: 2px;
      text-transform: uppercase;
      color: #E8002D;
      font-weight: 700;
      margin-bottom: 4px;
  }

  .badge-red {
      background: #E8002D;
      color: white;
      padding: 2px 8px;
      border-radius: 12px;
      font-size: 11px;
      font-weight: 700;
  }

  .badge-amber {
      background: #FFB703;
      color: black;
      padding: 2px 8px;
      border-radius: 12px;
      font-size: 11px;
      font-weight: 700;
  }

  .badge-green {
      background: #06D6A0;
      color: black;
      padding: 2px 8px;
      border-radius: 12px;
      font-size: 11px;
      font-weight: 700;
  }

  #MainMenu, footer {
      visibility: hidden;
  }

  [data-testid="stHeader"] {
      background: #0A0A0A;
  }
</style>
"""


def insight(text):
    return f'<div class="insight-box">{text}</div>'


def section_label(text):
    return f'<div class="section-label">{text}</div>'
