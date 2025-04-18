import json
import boto3

s3 = boto3.client('s3')
BUCKET = 'aranya-photo-storage-bucket' 

def lambda_handler(event, context):
    print("Lambda triggered!")
    print("Event received:", event)
    print("Event:", event)
    
    object_name = event['queryStringParameters']['filename']
    custom_labels = event['queryStringParameters'].get('customLabels', '')
    
    presigned_url = s3.generate_presigned_url(
        'put_object',
        Params={
            'Bucket': BUCKET,
            'Key': object_name,
            'ContentType': 'image/jpeg',
            'Metadata': {
                'customlabels': custom_labels  # Lowercase key only
            }

        },
        ExpiresIn=3600  # URL valid for 1 hour
    )
    
    print(f"Generated presigned URL: {presigned_url}")
    
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',  # Allow all
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        },
        'body': json.dumps({'uploadURL': presigned_url})
    }

