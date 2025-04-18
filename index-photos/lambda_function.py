import json
import boto3
import requests
from datetime import datetime

rekognition = boto3.client('rekognition')
s3 = boto3.client('s3')

opensearch_url = 'https://search-photos-po3kciitrlhdf36vzy66wqterm.us-east-1.es.amazonaws.com'
index = 'photos'
headers = {"Content-Type": "application/json"}

def lambda_handler(event, context):
    print("Lambda triggered!")
    print("Received event:", json.dumps(event))
    
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    rekog_response = rekognition.detect_labels(
        Image={
            'S3Object': {
                'Bucket': bucket,
                'Name': key
            }
        },
        MaxLabels=10,
        MinConfidence=70
    )
    
    rekog_labels = [label['Name'].lower() for label in rekog_response['Labels']]
    print(f"Rekognition detected labels: {rekog_labels}")
    
    head_object = s3.head_object(Bucket=bucket, Key=key)
    custom_labels = []
    
    if 'Metadata' in head_object and 'customlabels' in head_object['Metadata']:
        custom_labels_raw = head_object['Metadata']['customlabels']
        custom_labels = [label.strip().lower() for label in custom_labels_raw.split(',') if label.strip()]
    
    print(f"Custom labels from metadata: {custom_labels}")
    
    all_labels = list(set(rekog_labels + custom_labels))
    
    photo_metadata = {
        "objectKey": key,
        "bucket": bucket,
        "createdTimestamp": datetime.now().isoformat(),
        "labels": all_labels
    }
    
    print("Final metadata to index:", json.dumps(photo_metadata))
    
    # ⬇️ Use Basic Auth instead of AWS4Auth here
    try:
        document_url = f"{opensearch_url}/{index}/_doc/{key}"
        response = requests.put(
            document_url,
            auth=('aranya', 'Aranya289#'),  # <== Basic Authentication
            headers=headers,
            data=json.dumps(photo_metadata)
        )
        response.raise_for_status()
        print("Document indexed successfully!")
    except Exception as e:
        print(f"Error communicating with OpenSearch: {str(e)}")

    return {
        'statusCode': 200,
        'body': json.dumps('Photo processed and indexed successfully')
    }
