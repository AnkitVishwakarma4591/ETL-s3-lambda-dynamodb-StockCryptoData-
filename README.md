# Stock/Crypto Data ETL Pipeline - Serverless AWS

## Project Title

Real-World Serverless ETL Pipeline for Stock/Crypto Market Data

## Dataset Source

Sample stock and cryptocurrency market data including symbols like AAPL, GOOGL, MSFT, TSLA, AMZN, BTC, ETH.

## Scenario

Raw stock/crypto price records are uploaded to Amazon S3. An AWS Lambda function is triggered automatically, validates and transforms the data, then loads clean records into Amazon DynamoDB for analytics and dashboarding.

## Architecture

Third-Party Data -> S3 (raw/) -> Lambda ETL -> DynamoDB (clean\_records) -> CloudWatch Logs

## AWS Services Used

* Amazon S3 - Raw data storage
* AWS Lambda - ETL processing
* Amazon DynamoDB - Clean records storage
* AWS IAM - Least privilege role for Lambda
* AWS CloudWatch - Audit logs
* AWS CodePipeline - CI/CD pipeline
* AWS CodeBuild - Build and syntax validation

## ETL Rules

### Extract

* Reads raw CSV file from S3 bucket under raw/ prefix

### Transform

* Rejects records with missing symbol
* Rejects records with invalid or negative price
* Rejects records with missing volume
* Standardizes symbol to UPPERCASE
* Standardizes currency to UPPERCASE
* Adds derived field price\_category: HIGH (>=1000), MEDIUM (>=100), LOW (<100)

### Load

* Writes clean records to DynamoDB table clean\_records
* Adds processed\_at timestamp to each record

### Audit

* Logs total input records, inserted records, rejected records, timestamp, and source file

## DynamoDB Table Design

* Table Name: clean\_records
* Partition Key: record\_id (String)
* Capacity Mode: On-demand

## Testing Steps

1. Upload sample\_data/sample\_raw\_data.csv to S3 under raw/ prefix
2. Lambda triggers automatically via S3 event
3. Check CloudWatch logs for audit summary
4. Verify clean records in DynamoDB console

## GitHub Actions Summary

* Triggers on push or pull request to main branch
* Sets up Python 3.11
* Installs dependencies from requirements.txt
* Validates Lambda syntax using py\_compile

## AWS CodePipeline Summary

* Source Stage: Connected to GitHub repository
* Build Stage: AWS CodeBuild runs buildspec.yml
* Validates Lambda syntax and packages artifacts



\## Enhancement: File-Type Based Lambda Routing



This project includes an enhancement where a dedicated Router Lambda inspects the

incoming file's extension and dynamically invokes the correct downstream Lambda

function for processing, instead of using a single monolithic Lambda for all file types.



\### Architecture

S3 (raw/) -> Router Lambda (stock-etl-router) -> CSV Lambda (stock-etl-csv-processor) OR JSON Lambda (stock-etl-json-processor) -> DynamoDB



\### How it works

1\. A file is uploaded to the S3 bucket under the raw/ prefix.

2\. The S3 event triggers the Router Lambda (stock-etl-router).

3\. The Router Lambda reads the file extension from the object key.

4\. Based on the extension, it invokes the matching processor Lambda using boto3's

&#x20;  Lambda invoke API, passing the bucket and key as payload.

5\. The processor Lambda (CSV or JSON) extracts, transforms, validates, and loads

&#x20;  clean records into DynamoDB, tagging each record with a source\_type field

&#x20;  (CSV or JSON) for traceability.



\### Lambda Functions

\- stock-etl-router: Routes events based on file extension (.csv / .json)

\- stock-etl-csv-processor: Parses and validates CSV files

\- stock-etl-json-processor: Parses and validates JSON array files



\### Why this design

\- Keeps each parser focused on a single file format, improving maintainability

\- Makes it easy to add new file types (e.g. XML) by adding a new processor Lambda

&#x20; and one new condition in the router, without touching existing processors

\- Each processor Lambda follows least-privilege IAM permissions independently

