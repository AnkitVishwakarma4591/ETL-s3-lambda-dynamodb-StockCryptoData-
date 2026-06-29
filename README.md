# Stock/Crypto Data ETL Pipeline - Serverless AWS

## Project Title
Real-World Serverless ETL Pipeline for Stock/Crypto Market Data

## Dataset Source
Sample stock and cryptocurrency market data including symbols like AAPL, GOOGL, MSFT, TSLA, AMZN, BTC, ETH.

## Scenario
Raw stock/crypto price records are uploaded to Amazon S3. An AWS Lambda function is triggered automatically, validates and transforms the data, then loads clean records into Amazon DynamoDB for analytics and dashboarding.

## Architecture
Third-Party Data -> S3 (raw/) -> Lambda ETL -> DynamoDB (clean_records) -> CloudWatch Logs

## AWS Services Used
- Amazon S3 - Raw data storage
- AWS Lambda - ETL processing
- Amazon DynamoDB - Clean records storage
- AWS IAM - Least privilege role for Lambda
- AWS CloudWatch - Audit logs
- AWS CodePipeline - CI/CD pipeline
- AWS CodeBuild - Build and syntax validation

## ETL Rules

### Extract
- Reads raw CSV file from S3 bucket under raw/ prefix

### Transform
- Rejects records with missing symbol
- Rejects records with invalid or negative price
- Rejects records with missing volume
- Standardizes symbol to UPPERCASE
- Standardizes currency to UPPERCASE
- Adds derived field price_category: HIGH (>=1000), MEDIUM (>=100), LOW (<100)

### Load
- Writes clean records to DynamoDB table clean_records
- Adds processed_at timestamp to each record

### Audit
- Logs total input records, inserted records, rejected records, timestamp, and source file

## DynamoDB Table Design
- Table Name: clean_records
- Partition Key: record_id (String)
- Capacity Mode: On-demand

## Testing Steps
1. Upload sample_data/sample_raw_data.csv to S3 under raw/ prefix
2. Lambda triggers automatically via S3 event
3. Check CloudWatch logs for audit summary
4. Verify clean records in DynamoDB console

## GitHub Actions Summary
- Triggers on push or pull request to main branch
- Sets up Python 3.11
- Installs dependencies from requirements.txt
- Validates Lambda syntax using py_compile

## AWS CodePipeline Summary
- Source Stage: Connected to GitHub repository
- Build Stage: AWS CodeBuild runs buildspec.yml
- Validates Lambda syntax and packages artifacts