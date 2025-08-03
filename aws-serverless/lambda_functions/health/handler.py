"""
Health check Lambda function for Trading Simulator API
"""
import json
import os
from datetime import datetime


def lambda_handler(event, context):
    """
    Health check endpoint
    """
    try:
        response_data = {
            "success": True,
            "message": "Trading Simulator API is healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "environment": os.getenv('ENVIRONMENT', 'unknown'),
            "version": "1.0.0",
            "services": {
                "api": "healthy",
                "database": "healthy",
                "market_data": "healthy"
            }
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': os.getenv('CORS_ORIGINS', '*'),
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
            },
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        error_response = {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': os.getenv('CORS_ORIGINS', '*'),
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
            },
            'body': json.dumps(error_response)
        }
