import json
import os
import boto3
import requests
from datetime import datetime

newsapi_key = os.environ['apikey']
headers = {'X-Api-Key': newsapi_key}
newsapi_url = 'https://newsdata.io/api/1/news?apikey=pub_805640501d6ee0d1ddb14cb5df95365e57a64&q=tesla'

def lambda_handler(event, context):
    response = requests.get(newsapi_url, headers=headers)
    newsapi_data = response.json()
    
    client = boto3.client('s3')
    filename = 'articles_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '.json'
    
    client.put_object(
        Body=json.dumps(newsapi_data),
        Bucket='rawnewsbuckbucket',
        Key=filename
    )
    
    return {'statusCode': 200, 'body': 'success'}