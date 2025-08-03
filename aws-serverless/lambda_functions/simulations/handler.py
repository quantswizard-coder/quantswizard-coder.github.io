"""
Simulations Lambda function for Trading Simulator API
"""
import json
import os
import boto3
import uuid
from datetime import datetime, timedelta
from decimal import Decimal


# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')

# Get table name from environment
TABLE_NAME = os.getenv('DYNAMODB_TABLE')
table = dynamodb.Table(TABLE_NAME) if TABLE_NAME else None


def lambda_handler(event, context):
    """
    Handle simulation API requests
    """
    try:
        http_method = event['httpMethod']
        path = event['path']
        path_parameters = event.get('pathParameters') or {}
        
        if http_method == 'POST' and path == '/api/simulations':
            body = json.loads(event['body'])
            return create_simulation(body)
        elif http_method == 'GET' and path == '/api/simulations':
            return get_simulations()
        elif http_method == 'GET' and 'simulationId' in path_parameters:
            return get_simulation(path_parameters['simulationId'])
        elif http_method == 'POST' and path.endswith('/start'):
            return start_simulation(path_parameters['simulationId'])
        elif http_method == 'POST' and path.endswith('/stop'):
            return stop_simulation(path_parameters['simulationId'])
        elif http_method == 'GET' and path.endswith('/state'):
            return get_simulation_state(path_parameters['simulationId'])
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


def create_simulation(body):
    """
    Create a new simulation
    """
    try:
        simulation_id = str(uuid.uuid4())
        user_id = "demo_user"  # In production, get from authentication
        timestamp = datetime.utcnow().isoformat()
        
        # Validate required fields
        required_fields = ['strategy_id', 'strategy_params', 'config']
        for field in required_fields:
            if field not in body:
                return {
                    'statusCode': 400,
                    'headers': get_cors_headers(),
                    'body': json.dumps({
                        "success": False,
                        "error": f"Missing required field: {field}"
                    })
                }
        
        # Create simulation record
        simulation_data = {
            'userId': user_id,
            'timestamp': timestamp,
            'simulationId': simulation_id,
            'recordType': 'simulation',
            'status': 'created',
            'strategy_id': body['strategy_id'],
            'strategy_params': convert_floats_to_decimal(body['strategy_params']),
            'config': convert_floats_to_decimal(body['config']),
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        # Save to DynamoDB
        if table:
            table.put_item(Item=simulation_data)
        
        return {
            'statusCode': 201,
            'headers': get_cors_headers(),
            'body': json.dumps({
                "success": True,
                "data": {
                    "simulation_id": simulation_id,
                    "status": "created",
                    "message": "Simulation created successfully"
                },
                "timestamp": timestamp
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({
                "success": False,
                "error": f"Failed to create simulation: {str(e)}"
            })
        }


def start_simulation(simulation_id):
    """
    Start a simulation (simplified version for Lambda)
    """
    try:
        user_id = "demo_user"
        timestamp = datetime.utcnow().isoformat()
        
        # Get simulation from DynamoDB
        if table:
            response = table.query(
                IndexName='simulation-index',
                KeyConditionExpression='simulationId = :sim_id',
                ExpressionAttributeValues={':sim_id': simulation_id}
            )
            
            if not response['Items']:
                return {
                    'statusCode': 404,
                    'headers': get_cors_headers(),
                    'body': json.dumps({
                        "success": False,
                        "error": "Simulation not found"
                    })
                }
            
            simulation = response['Items'][0]
        else:
            # Fallback for testing without DynamoDB
            simulation = {'status': 'created'}
        
        # Update status to running
        if table:
            table.update_item(
                Key={
                    'userId': user_id,
                    'timestamp': simulation['timestamp']
                },
                UpdateExpression='SET #status = :status, updated_at = :updated_at',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'running',
                    ':updated_at': timestamp
                }
            )
        
        # For Lambda, we'll run a simplified simulation
        # In production, this would trigger an SQS message for heavy processing
        simulation_results = run_simple_simulation(simulation_id)
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                "success": True,
                "data": {
                    "simulation_id": simulation_id,
                    "status": "running",
                    "message": "Simulation started successfully"
                },
                "timestamp": timestamp
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({
                "success": False,
                "error": f"Failed to start simulation: {str(e)}"
            })
        }


def get_simulation_state(simulation_id):
    """
    Get current simulation state
    """
    try:
        user_id = "demo_user"
        
        # Query DynamoDB for simulation data
        if table:
            response = table.query(
                IndexName='simulation-index',
                KeyConditionExpression='simulationId = :sim_id',
                ExpressionAttributeValues={':sim_id': simulation_id}
            )
            
            if not response['Items']:
                return {
                    'statusCode': 404,
                    'headers': get_cors_headers(),
                    'body': json.dumps({
                        "success": False,
                        "error": "Simulation not found"
                    })
                }
            
            # Get the latest simulation record
            simulation_records = sorted(response['Items'], key=lambda x: x['timestamp'], reverse=True)
            latest_record = simulation_records[0]
            
            # Generate mock state for demo
            state = generate_mock_simulation_state(simulation_id, latest_record)
        else:
            # Fallback mock state
            state = generate_mock_simulation_state(simulation_id, {})
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                "success": True,
                "data": state,
                "timestamp": datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({
                "success": False,
                "error": f"Failed to get simulation state: {str(e)}"
            })
        }


def run_simple_simulation(simulation_id):
    """
    Run a simplified simulation for Lambda (under 15 min limit)
    """
    # This is a simplified version - in production, heavy processing
    # would be handled by ECS tasks triggered via SQS
    
    # Get some real Bitcoin data for the simulation
    try:
        import yfinance as yf
        btc = yf.Ticker("BTC-USD")
        hist = btc.history(period="30d")
        
        if not hist.empty:
            current_price = float(hist['Close'].iloc[-1])
            # Simple mock calculation
            portfolio_value = 100000 * (1 + (current_price - 100000) / 100000 * 0.1)
        else:
            portfolio_value = 105000  # Fallback
            
    except:
        portfolio_value = 105000  # Fallback
    
    return {
        "portfolio_value": portfolio_value,
        "total_return": (portfolio_value - 100000) / 100000,
        "status": "completed"
    }


def generate_mock_simulation_state(simulation_id, simulation_record):
    """
    Generate mock simulation state for demo purposes
    """
    import random
    
    # Mock portfolio data
    portfolio_value = 100000 + random.uniform(-10000, 20000)
    total_return = (portfolio_value - 100000) / 100000
    
    return {
        "status": simulation_record.get('status', 'running'),
        "progress": random.uniform(0.8, 1.0),
        "current_date": datetime.utcnow().isoformat(),
        "portfolio": {
            "timestamp": datetime.utcnow().isoformat(),
            "totalValue": portfolio_value,
            "cash": portfolio_value * 0.2,
            "positions": [],
            "dailyReturn": random.uniform(-0.05, 0.05),
            "totalReturn": total_return * 100,
            "sharpeRatio": random.uniform(-1.0, 2.0),
            "maxDrawdown": random.uniform(-0.15, -0.02) * 100,
            "volatility": random.uniform(0.1, 0.3)
        },
        "trades": [],
        "performance": {
            "totalReturn": total_return * 100,
            "sharpeRatio": random.uniform(-1.0, 2.0),
            "maxDrawdown": random.uniform(-0.15, -0.02) * 100,
            "volatility": random.uniform(0.1, 0.3),
            "winRate": random.uniform(40, 70),
            "profitFactor": random.uniform(0.8, 1.5),
            "totalTrades": random.randint(5, 25),
            "avgTradeReturn": random.uniform(-2, 3),
            "bestTrade": random.uniform(5, 15),
            "worstTrade": random.uniform(-15, -5)
        },
        "error_message": None
    }


def convert_floats_to_decimal(obj):
    """
    Convert floats to Decimal for DynamoDB compatibility
    """
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(item) for item in obj]
    else:
        return obj


def get_simulations():
    """
    Get all simulations for user
    """
    return {
        'statusCode': 200,
        'headers': get_cors_headers(),
        'body': json.dumps({
            "success": True,
            "data": [],
            "message": "Simulations list (implement based on requirements)"
        })
    }


def get_simulation(simulation_id):
    """
    Get specific simulation details
    """
    return get_simulation_state(simulation_id)


def stop_simulation(simulation_id):
    """
    Stop a running simulation
    """
    return {
        'statusCode': 200,
        'headers': get_cors_headers(),
        'body': json.dumps({
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "status": "stopped"
            }
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
