import json
import boto3
import requests
import os
from requests_aws4auth import AWS4Auth

# OpenSearch info
opensearch_url = 'https://search-photos-po3kciitrlhdf36vzy66wqterm.us-east-1.es.amazonaws.com'
index = 'photos'
headers = { "Content-Type": "application/json" }

# Lex client
lex_client = boto3.client('lexv2-runtime')  # Lex V2

def lambda_handler(event, context):
    print("Lambda triggered!")
    print("Event received:", json.dumps(event))

    query = ""
    if event.get('queryStringParameters') and event['queryStringParameters'].get('q'):
        query = event['queryStringParameters']['q']
    else:
        return {
            'statusCode': 400,
            'body': json.dumps('Missing search query parameter')
        }
    
    print(f"User Query: {query}")

    # Step 1: Send query to Lex
    try:
        response = lex_client.recognize_text(
            botId='2C3CEMQFXR',               # <-- Your Lex Bot ID
            botAliasId='TSTALIASID',          # <-- Your Lex Bot Alias ID
            localeId='en_US',
            sessionId='test-session',
            text=query
        )
    except Exception as e:
        print(f"Lex call failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps('Lex processing failed')
        }
    
    print("Lex Response:", json.dumps(response))

    # Step 2: Extract keywords from Composite Slot
    slots = response.get('sessionState', {}).get('intent', {}).get('slots', {})
    keywords = []

    if slots:
        for slot_name in ['keyword', 'keyword1', 'keyword2', 'keyword3']:
            slot_info = slots.get(slot_name)
            if slot_info and 'value' in slot_info and 'interpretedValue' in slot_info['value']:
                keyword = slot_info['value']['interpretedValue'].lower()
                keywords.append(keyword)

    print(f"Extracted Keywords: {keywords}")

    if not keywords:
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps([])
        }

    # Step 3: Search OpenSearch for each keyword
    photo_keys = set()

    for keyword in keywords:
        search_body = {
            "query": {
                "match": {
                    "labels": {
                        "query": keyword,
                        "fuzziness": "AUTO"  # Allow fuzzy matches like 'dog' vs 'dogs'
                    }
                }
            }
        }
        search_url = f"{opensearch_url}/{index}/_search"
        try:
            search_response = requests.get(
                search_url,
                auth=('aranya', 'Aranya289#'),  # Basic Auth to OpenSearch
                headers=headers,
                data=json.dumps(search_body)
            )
            search_response.raise_for_status()
            search_results = search_response.json()
            if 'hits' in search_results and 'hits' in search_results['hits']:
                for hit in search_results['hits']['hits']:
                    photo_keys.add(hit['_source']['objectKey'])
        except Exception as e:
            print(f"Error searching OpenSearch for keyword '{keyword}': {str(e)}")

    print(f"Final matched photo keys: {list(photo_keys)}")

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        },
        'body': json.dumps(list(photo_keys))
    }
