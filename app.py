from flask import Flask, render_template, request
import pandas as pd
import requests
import pygal
from pygal.style import DarkStyle
from datetime import datetime
import os

app = Flask(__name__)

# This is the API key I got
API_KEY = '3Q3H4SY1PNICDBG6'

def load_stock_symbols():
    """Load stock symbols from stocks.csv."""
    try:
        df = pd.read_csv('stocks.csv')
        return df['Symbol'].dropna().unique().tolist()
    except Exception as e:
        print(f"Error loading stock symbols: {e}")
        return []

def validate_date(date_text):
    """Validate date format YYYY-MM-DD."""
    try:
        datetime.strptime(date_text, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def validate_date_range(start_date, end_date):
    """Ensure start_date is not after end_date."""
    return datetime.strptime(start_date, '%Y-%m-%d') <= datetime.strptime(end_date, '%Y-%m-%d')

def fetch_stock_data(symbol, time_series, api_key, interval=None):
    """Fetch stock data from Alpha Vantage API."""
    base_url = "https://www.alphavantage.co/query?"
    params = {
        'function': time_series,
        'symbol': symbol,
        'apikey': api_key,
        'datatype': 'json'
    }
    if time_series == 'TIME_SERIES_INTRADAY' and interval:
        params['interval'] = interval

    response = requests.get(base_url, params=params)
    print(response.json()) 
    return response.json()


def generate_chart(data, chart_type, symbol):
    """Generate a Pygal chart and return as data URI."""
    dates = list(data.keys())
    open_prices = [float(value['1. open']) for value in data.values()]
    high_prices = [float(value['2. high']) for value in data.values()]
    low_prices = [float(value['3. low']) for value in data.values()]
    close_prices = [float(value['4. close']) for value in data.values()]
    
    dates.reverse()
    open_prices.reverse()
    high_prices.reverse()
    low_prices.reverse()
    close_prices.reverse()
    
    if chart_type == '1': 
        chart = pygal.Bar(style=DarkStyle, x_label_rotation=45, show_legend=True)
    elif chart_type == '2': 
        chart = pygal.Line(style=DarkStyle, x_label_rotation=45, show_legend=True)
    else:
        chart = pygal.Line(style=DarkStyle, x_label_rotation=45, show_legend=True)
    
    chart.title = f'{symbol} Stock Prices (Open, High, Low, Close)'
    chart.x_labels = dates
    
    chart.add('Open', open_prices)
    chart.add('High', high_prices)
    chart.add('Low', low_prices)
    chart.add('Close', close_prices)
    
    return chart.render_data_uri()

@app.route('/', methods=['GET', 'POST'])
def index():
    symbols = load_stock_symbols()
    chart = None
    error = None

    if request.method == 'POST':
       
        symbol = request.form.get('symbol')
        chart_type = request.form.get('chart_type')
        time_series_choice = request.form.get('time_series')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        interval = request.form.get('interval')  

       
        if not all([symbol, chart_type, time_series_choice, start_date, end_date]):
            error = "All fields are required."
            return render_template('index.html', symbols=symbols, chart=chart, error=error)
        
        if not validate_date(start_date) or not validate_date(end_date):
            error = "Invalid date format. Please use YYYY-MM-DD."
            return render_template('index.html', symbols=symbols, chart=chart, error=error)
        
        if not validate_date_range(start_date, end_date):
            error = "End date must be after start date."
            return render_template('index.html', symbols=symbols, chart=chart, error=error)
        
       
        time_series_map = {
            '1': 'TIME_SERIES_INTRADAY',
            '2': 'TIME_SERIES_DAILY',
            '3': 'TIME_SERIES_WEEKLY',
            '4': 'TIME_SERIES_MONTHLY'
        }

        time_series = time_series_map.get(time_series_choice)
        if not time_series:
            error = "Invalid time series choice."
            return render_template('index.html', symbols=symbols, chart=chart, error=error)
        
       
        if time_series == 'TIME_SERIES_INTRADAY':
            interval = request.form.get('interval')
            if interval not in ['1min', '5min', '15min', '30min', '60min']:
                error = "Invalid interval for intraday data."
                return render_template('index.html', symbols=symbols, chart=chart, error=error)
        else:
            interval = None  

        
        stock_data = fetch_stock_data(symbol, time_series, API_KEY, interval)

        
        if 'Error Message' in stock_data:
            error = "Error fetching data. Please check the stock symbol or time series function."
            return render_template('index.html', symbols=symbols, chart=chart, error=error)
        if 'Note' in stock_data:
            error = "API call frequency is exceeded. Please try again later."
            return render_template('index.html', symbols=symbols, chart=chart, error=error)
        
        
        time_series_key = next((key for key in stock_data.keys() if 'Time Series' in key), None)
        if not time_series_key:
            error = "Unexpected data format received from API."
            return render_template('index.html', symbols=symbols, chart=chart, error=error)
        
        
        filtered_data = {date: value for date, value in stock_data[time_series_key].items() if start_date <= date <= end_date}
        
        if not filtered_data:
            error = "No data available for the specified date range."
            return render_template('index.html', symbols=symbols, chart=chart, error=error)
        
       
        chart = generate_chart(filtered_data, chart_type, symbol)
        
    return render_template('index.html', symbols=symbols, chart=chart, error=error)

if __name__ == '__main__':
    app.run(host='0.0.0.0') 