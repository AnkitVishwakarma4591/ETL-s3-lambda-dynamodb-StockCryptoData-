import json
import boto3
import csv
import io
import logging
from datetime import datetime, timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
TABLE_NAME = 'clean_records'

def lambda_handler(event, context):
    logger.info("ETL Lambda started")
    
    # Get bucket and key from S3 event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    logger.info(f"Processing file: s3://{bucket}/{key}")
    
    # EXTRACT
    response = s3_client.get_object(Bucket=bucket, Key=key)
    content = response['Body'].read().decode('utf-8')
    reader = csv.DictReader(io.StringIO(content))
    records = list(reader)
    
    total_input = len(records)
    inserted = 0
    rejected = 0
    
    table = dynamodb.Table(TABLE_NAME)
    
    for record in records:
        # TRANSFORM - Validate required fields
        symbol = record.get('symbol', '').strip()
        price_str = record.get('price', '').strip()
        volume_str = record.get('volume', '').strip()
        
        # Reject if symbol is missing
        if not symbol:
            logger.warning(f"Rejected record {record.get('record_id')} - missing symbol")
            rejected += 1
            continue
        
        # Reject if price is invalid or negative
        try:
            price = float(price_str)
            if price <= 0:
                raise ValueError("Price must be positive")
        except (ValueError, TypeError):
            logger.warning(f"Rejected record {record.get('record_id')} - invalid price: {price_str}")
            rejected += 1
            continue
        
        # Reject if volume is missing
        try:
            volume = int(volume_str)
        except (ValueError, TypeError):
            logger.warning(f"Rejected record {record.get('record_id')} - invalid volume: {volume_str}")
            rejected += 1
            continue
        
        # Standardize fields
        symbol = symbol.upper()
        timestamp = record.get('timestamp', '').strip()
        currency = record.get('currency', 'USD').strip().upper()
        
        # Derived field - market cap category based on price
        if price >= 1000:
            price_category = 'HIGH'
        elif price >= 100:
            price_category = 'MEDIUM'
        else:
            price_category = 'LOW'
        
        # LOAD - Write to DynamoDB
        item = {
            'record_id': record.get('record_id', '').strip(),
            'symbol': symbol,
            'price': str(round(price, 2)),
            'volume': str(volume),
            'timestamp': timestamp,
            'currency': currency,
            'price_category': price_category,
            'processed_at': datetime.now(timezone.utc).isoformat()
        }
        
        table.put_item(Item=item)
        inserted += 1
        logger.info(f"Inserted record: {item['record_id']} - {symbol} @ {price}")
    
    # AUDIT LOG
    audit = {
        'total_input_records': total_input,
        'inserted_records': inserted,
        'rejected_records': rejected,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'source_file': f"s3://{bucket}/{key}"
    }
    
    logger.info(f"ETL AUDIT SUMMARY: {json.dumps(audit)}")
    
    return {
        'statusCode': 200,
        'body': json.dumps(audit)
    }