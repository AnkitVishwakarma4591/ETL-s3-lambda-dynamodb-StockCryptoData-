import json
import boto3
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

lambda_client = boto3.client('lambda')

CSV_LAMBDA = 'stock-etl-csv-processor'
JSON_LAMBDA = 'stock-etl-json-processor'

def lambda_handler(event, context):
    logger.info(f"Router received event: {json.dumps(event)}")

    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    logger.info(f"Routing file: s3://{bucket}/{key}")

    file_extension = key.lower().split('.')[-1] if '.' in key else ''

    payload = {
        'bucket': bucket,
        'key': key
    }

    if file_extension == 'csv':
        target_lambda = CSV_LAMBDA
        logger.info(f"File type CSV detected. Routing to {CSV_LAMBDA}")
    elif file_extension == 'json':
        target_lambda = JSON_LAMBDA
        logger.info(f"File type JSON detected. Routing to {JSON_LAMBDA}")
    else:
        logger.warning(f"Unsupported file type: {file_extension}. Skipping processing.")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f'Unsupported file type: {file_extension}'})
        }

    response = lambda_client.invoke(
        FunctionName=target_lambda,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )

    result_payload = json.loads(response['Payload'].read())
    logger.info(f"Downstream Lambda response: {result_payload}")

    return {
        'statusCode': 200,
        'body': json.dumps({
            'routed_to': target_lambda,
            'file': key,
            'downstream_response': result_payload
        })
    }