import streamlit as st
import plotly.graph_objects as go

def render_ats_gauge(score: float):
    # determine status label
    if score >= 100:
        status, color = "Excellent", "#2ECC71"
    elif score >= 80:
        status, color = "Strong match", "#27AE60"
    elif score >= 60:
        status, color = "Partial match", "#F1C40F"
    else:
        status, color = "Weak match", "#E74C3C"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={"x": [0,1], "y": [0,1]},
        title={
            "text": "ATS Score",
            "font": {"size": 24, "color": "white"}
        },
        number={
            "font": {"size": 36, "color": color}
        },
        gauge={
            "shape": "angular",
            "axis": {"range": [0,100], "tickcolor": "white"},
            "bar": {"color": color, "thickness": 0.2},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0, score], "color": color},
                {"range": [score, 100], "color": "#333333"},
            ],
        }
    ))

    fig.update_layout(
        paper_bgcolor="black",
        font={"color": "white"},
        margin=dict(t=0, b=0, l=0, r=0)
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown(f"<div style='text-align:center; font-size:24px; color:{color};'>{status}</div>", 
                unsafe_allow_html=True)