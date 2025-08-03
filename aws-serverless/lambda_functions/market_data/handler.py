"""
Market Data Lambda function for Trading Simulator API
"""
import json
import os
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd


def lambda_handler(event, context):
    """
    Handle market data API requests
    """
    try:
        http_method = event['httpMethod']
        path_parameters = event.get('pathParameters') or {}
        query_parameters = event.get('queryStringParameters') or {}
        
        if http_method == 'GET' and 'symbol' in path_parameters:
            symbol = path_parameters['symbol']
            days = int(query_parameters.get('days', 180))
            return get_market_data(symbol, days)
        else:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    "success": False,
                    "error": "Endpoint not found"
                })
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
        }


def get_market_data(symbol, days):
    """
    Fetch market data from Yahoo Finance
    """
    try:
        # Create ticker object
        ticker = yf.Ticker(symbol)
        
        # Get historical data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        hist = ticker.history(start=start_date, end=end_date)
        
        if hist.empty:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    "success": False,
                    "error": f"No data found for symbol {symbol}"
                })
            }
        
        # Get current price and calculate changes
        current_price = float(hist['Close'].iloc[-1])
        previous_price = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current_price
        price_change_24h = current_price - previous_price
        price_change_percent_24h = (price_change_24h / previous_price * 100) if previous_price != 0 else 0
        
        # Convert historical data to list of dictionaries
        data_points = []
        for index, row in hist.iterrows():
            data_points.append({
                "timestamp": index.isoformat(),
                "open": float(row['Open']),
                "high": float(row['High']),
                "low": float(row['Low']),
                "close": float(row['Close']),
                "volume": int(row['Volume'])
            })
        
        # Get additional info
        info = ticker.info
        market_cap = info.get('marketCap', 0)
        
        response_data = {
            "symbol": symbol,
            "current_price": current_price,
            "price_change_24h": price_change_24h,
            "price_change_percent_24h": price_change_percent_24h,
            "market_cap": market_cap,
            "data": data_points,
            "data_points": len(data_points),
            "period": f"{days} days"
        }
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                "success": True,
                "data": response_data,
                "timestamp": datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({
                "success": False,
                "error": f"Failed to fetch market data: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            })
        }


def get_cors_headers():
    """
    Get CORS headers for responses
    """
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': os.getenv('CORS_ORIGINS', '*'),
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }
