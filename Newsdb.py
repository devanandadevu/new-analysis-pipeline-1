import json
import boto3
import os
import psycopg2
import pandas as pd


def get_latest_s3_object_key(bucket_name, prefix=''):
    s3 = boto3.client('s3')
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)

    if 'Contents' not in response:
        return None

    # Sort by LastModified timestamp, descending
    sorted_objects = sorted(response['Contents'], key=lambda obj: obj['LastModified'], reverse=True)
    return sorted_objects[0]['Key']


def lambda_handler(event, context):
    host = os.environ['DB_HOST']
    database = os.environ['DB_NAME']
    user = os.environ['DB_USER']
    password = os.environ['DB_PASS']
    port = os.environ['DB_PORT']

    bucket_name = 'rawnewsbuckbucket'
    s3 = boto3.client('s3')

    # Automatically get the latest JSON file from the bucket
    key_key = get_latest_s3_object_key(bucket_name, prefix='articles')
    if not key_key:
        return {'statusCode': 404, 'body': json.dumps('No article files found in S3 bucket.')}

    print(f"Processing file: {key_key}")

    try:
        response = s3.get_object(Bucket=bucket_name, Key=key_key)
        data = json.loads(response['Body'].read())
        article = data.get("results", [])

        df = pd.DataFrame(article)

        if df.empty:
            return {'statusCode': 200, 'body': json.dumps('No articles found in latest file.')}

        df = df[['article_id', 'title', 'description', 'country', 'language', 'link', 'image_url']]
        df.dropna(inplace=True)

        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port
        )
        cursor = conn.cursor()

        # Create table if not exists
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS news_articles (
                    article_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    country TEXT NOT NULL,
                    language TEXT NOT NULL,
                    link TEXT NOT NULL,
                    image_url TEXT NOT NULL
                );
            """)
            conn.commit()
            print("Table check/creation completed.")
        except Exception as e:
            print(f"Error creating table: {e}")

        # Insert data into table
        for articles in article:
            try:
                article_id = articles.get("article_id")
                title = articles.get("title")
                description = articles.get("description")
                country = articles.get("country")
                language = articles.get("language")
                link = articles.get("link")
                image_url = articles.get("image_url")

                if not all([article_id, title, description, country, language, link, image_url]):
                    print(f"Skipping article with missing data: {article_id}")
                    continue

                cursor.execute("""
                    INSERT INTO news_articles (
                        article_id, title, description, country, language, link, image_url
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (article_id) DO NOTHING;
                """, (article_id, title, description, country, language, link, image_url))

            except Exception as e:
                print(f"Error inserting article {article_id}: {e}")
                continue

        conn.commit()
        cursor.close()
        conn.close()

        return {
            'statusCode': 200,
            'body': json.dumps(f'Data from {key_key} inserted successfully')
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f"Processing error: {str(e)}")
        }