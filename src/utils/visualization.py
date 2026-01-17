import matplotlib.pyplot as plt
import plotly.graph_objects as go

def plot_equity_curve(equity_curve):
    plt.figure(figsize=(10, 6))
    plt.plot(equity_curve, label='Equity Curve')
    plt.xlabel('Time')
    plt.ylabel('Equity')
    plt.title('Equity Curve')
    plt.legend()
    plt.show()

def plot_interactive_equity_curve(equity_curve):
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=equity_curve, mode='lines', name='Equity Curve'))
    fig.update_layout(title='Equity Curve', xaxis_title='Time', yaxis_title='Equity')
    fig.show()