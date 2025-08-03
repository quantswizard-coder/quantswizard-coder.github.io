# Trading Simulator AWS Architecture Summary

## Stack Overview
React frontend + REST API backend + backtesting engine for quantitative trading simulation

## Architecture Components

### Frontend: React App
- **Deployment**: S3 static hosting + CloudFront CDN
- **Alternative**: AWS Amplify for automatic CI/CD
- **Cost**: $1-5/month

### Backend: REST API
- **Primary**: Lambda functions + API Gateway
- **Structure**: One Lambda per endpoint group (trades, portfolio, backtest)
- **Scaling**: Auto-scales, pay-per-request
- **Alternative**: ECS Fargate for complex APIs

### Database
- **Trading Data**: DynamoDB
  - Partition key: `userId`, Sort key: `timestamp`
  - GSI on `symbol` for quick lookups
  - Auto-scaling, fast writes
- **Analytics**: Add RDS PostgreSQL if complex queries needed

### Backtesting Engine
- **Light Processing**: Lambda (15min max, 3GB memory)
- **Heavy Processing**: ECS + SQS queue system
- **Results Storage**: S3 for reports, DynamoDB for metadata

### Data Storage Strategy
- **Hot Data**: DynamoDB (recent prices, user trades)
- **Cold Data**: S3 (historical market data, backtest reports)
- **Market Data Ingestion**: Lambda functions

## Sample DynamoDB Schema
```json
{
  "userId": "user123",
  "timestamp": "2025-01-15T10:30:00Z",
  "symbol": "AAPL",
  "action": "BUY",
  "quantity": 100,
  "price": 150.25,
  "portfolioValue": 50000
}
```

## Deployment
- **IaC**: CloudFormation or CDK
- **CI/CD**: GitHub Actions
- **Frontend**: Build → S3 → CloudFront invalidation
- **Backend**: Package → Lambda deployment

## Cost Estimate
- S3 + CloudFront: $2-5/month
- API Gateway + Lambda: $5-20/month
- DynamoDB: $5-25/month
- **Total**: $12-50/month (moderate usage)

## Implementation Path
1. **MVP**: S3 frontend + 1 Lambda + 1 DynamoDB table
2. **Expand**: Multiple Lambda functions, backtesting engine
3. **Scale**: ECS for heavy compute, caching, real-time features

## Key Benefits
- Serverless = no infrastructure management
- Pay-per-use pricing model
- Auto-scaling built-in
- Independent component deployment
- Perfect for variable trading simulation workloads