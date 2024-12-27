from flask import Flask, render_template, request
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

app = Flask(__name__)

# Generate random historical price data for a single currency
def generate_currency_data(currency_name, days=7, start_price=100):
    data = []
    current_time = datetime.now() - timedelta(days=days)
    current_price = float(start_price)
    for _ in range(days * 288):  # 288 = 24 hours * 60 / 5
        o = current_price
        close_change = np.random.randint(-3, 4)
        c = o + close_change
        h = max(o, c) + np.random.randint(0, 3)
        l = min(o, c) - np.random.randint(0, 3)
        data.append({"currency": currency_name, "time": current_time, "open": o, "high": h, "low": l, "close": c})
        current_price = c
        current_time += timedelta(minutes=5)
    return pd.DataFrame(data)

# Generate a scatter plot mimicking a box plot for currency price history with green and red colors
def generate_colored_scatter_plot(data, currency_name):
    # Determine colors based on whether the closing price increased or decreased
    colors = ["green" if close > open else "red" for open, close in zip(data["open"], data["close"])]
    
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            y=data["close"],
            mode="markers",
            marker=dict(color=colors, size=6),
            name=f"{currency_name} Prices",
        )
    )
    
    fig.update_layout(
        title=f"{currency_name} Price History (Last 7 Days)",
        yaxis_title="Price",
        xaxis_title="Time",
        xaxis=dict(showticklabels=False),  # Hides x-axis tick labels for simplicity
    )
    return fig.to_html(full_html=False)

@app.route("/")
def index():
    # Available currencies
    currencies = ["USD", "EUR", "JPY", "BTC"]
    return render_template("test.html", currencies=currencies)

@app.route("/currency/<string:currency_name>")
def show_currency(currency_name):
    # Validate currency
    available_currencies = ["USD", "EUR", "JPY", "BTC"]
    if currency_name not in available_currencies:
        return f"Currency {currency_name} not found.", 404

    # Generate data and plot
    data = generate_currency_data(currency_name, days=7, start_price=np.random.randint(50, 150))
    scatter_plot_html = generate_colored_scatter_plot(data, currency_name)
    return render_template("currency.html", currency_name=currency_name, chart_html=scatter_plot_html)

if __name__ == "__main__":
    app.run(debug=True)
