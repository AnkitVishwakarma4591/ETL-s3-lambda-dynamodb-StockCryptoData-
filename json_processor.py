import json
import boto3
import logging
from datetime import datetime, timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
TABLE_NAME = 'clean_records'

def lambda_handler(event, context):
    logger.info("JSON ETL Lambda started")
    logger.info(f"Received event: {json.dumps(event)}")

    bucket = event['bucket']
    key = event['key']

    logger.info(f"Processing JSON file: s3://{bucket}/{key}")

    # EXTRACT
    response = s3_client.get_object(Bucket=bucket, Key=key)
    content = response['Body'].read().decode('utf-8')
    records = json.loads(content)

    total_input = len(records)
    inserted = 0
    rejected = 0

    table = dynamodb.Table(TABLE_NAME)

    for record in records:
        symbol = str(record.get('symbol', '')).strip()
        price_val = record.get('price')
        volume_val = record.get('volume')

        if not symbol:
            logger.warning(f"Rejected record {record.get('record_id')} - missing symbol")
            rejected += 1
            continue

        try:
            price = float(price_val)
            if price <= 0:
                raise ValueError("Price must be positive")
        except (ValueError, TypeError):
            logger.warning(f"Rejected record {record.get('record_id')} - invalid price: {price_val}")
            rejected += 1
            continue

        try:
            volume = int(volume_val)
        except (ValueError, TypeError):
            logger.warning(f"Rejected record {record.get('record_id')} - invalid volume: {volume_val}")
            rejected += 1
            continue

        symbol = symbol.upper()
        timestamp = str(record.get('timestamp', '')).strip()
        currency = str(record.get('currency', 'USD')).strip().upper()

        if price >= 1000:
            price_category = 'HIGH'
        elif price >= 100:
            price_category = 'MEDIUM'
        else:
            price_category = 'LOW'

        item = {
            'record_id': str(record.get('record_id', '')).strip(),
            'symbol': symbol,
            'price': str(round(price, 2)),
            'volume': str(volume),
            'timestamp': timestamp,
            'currency': currency,
            'price_category': price_category,
            'source_type': 'JSON',
            'processed_at': datetime.now(timezone.utc).isoformat()
        }

        table.put_item(Item=item)
        inserted += 1
        logger.info(f"Inserted record: {item['record_id']} - {symbol} @ {price}")

    audit = {
        'file_type': 'JSON',
        'total_input_records': total_input,
        'inserted_records': inserted,
        'rejected_records': rejected,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'source_file': f"s3://{bucket}/{key}"
    }

    logger.info(f"JSON ETL AUDIT SUMMARY: {json.dumps(audit)}")

    return {
        'statusCode': 200,
        'body': json.dumps(audit)
    }