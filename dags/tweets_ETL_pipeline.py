from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import requests
import json
import brotli
import time
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import random
import tempfile

user_header_1 ={
  "id":"1",
  "Accept": "*/*",
  "Accept-Encoding": "gzip, deflate, br",
  "Accept-Language": "en-US,en;q=0.5",
  "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
  "Connection": "keep-alive",
  "Content-Type": "application/json",
  "Cookie": "g_state={\"i_l\":0}; kdt=LGzDmv9Kye5puAFVlNIFwePQezc7vPVSjzlPGA3q; lang=en; dnt=1; gt=1785665685642739789; d_prefs=MToxLGNvbnNlbnRfdmVyc2lvbjoyLHRleHRfdmVyc2lvbjoxMDAw; guest_id_ads=v1%3A171457030820134199; guest_id_marketing=v1%3A171457030820134199; personalization_id=\"v1_zpbBmPqG8htqHM0oGeiu6Q==\"; guest_id=v1%3A171457118188167391; _twitter_sess=BAh7BiIKZmxhc2hJQzonQWN0aW9uQ29udHJvbGxlcjo6Rmxhc2g6OkZsYXNo%250ASGFzaHsABjoKQHVzZWR7AA%253D%253D--1164b91ac812d853b877e93ddb612b7471bebc74; twid=u%3D1785667437540597760; ct0=876a0dee11c3788bfd91d9763f6ac5f2d28a459c15bec6f0d749acbdbf79259e3b623afd8cc752b96b6b55dc852eb6971483e374a4e5b744e8d28a8c9fbd6dcdee9775d92d084448fbdc0be9ba776188; auth_token=eae60ca6cf44e378e8bdf560ba59088b3a4d428b",
  "Host": "twitter.com",
  "Sec-Fetch-Dest": "empty",
  "Sec-Fetch-Mode": "cors",
  "Sec-Fetch-Site": "same-origin",
  "TE": "trailers",
  "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
  "x-client-transaction-id": "v633MAI2yLa/cqSOa+K4JVEZ2tyU/zNxGazPugfJvYfOxvOQj6Crva1VnczZe45jA5ZaXb5bo/cmHhBf+YjhsUwHhrkhvA",
  "X-Client-UUID": "8bc52ba1-106f-415b-9167-079c3af43756",
  "x-csrf-token": "876a0dee11c3788bfd91d9763f6ac5f2d28a459c15bec6f0d749acbdbf79259e3b623afd8cc752b96b6b55dc852eb6971483e374a4e5b744e8d28a8c9fbd6dcdee9775d92d084448fbdc0be9ba776188",
  "x-twitter-active-user": "yes",
  "x-twitter-auth-type": "OAuth2Session",
  "x-twitter-client-language": "en"
}

user_header_3 ={
  "id":"3",
  "Accept": "*/*",
  "Accept-Encoding": "gzip, deflate, br",
  "Accept-Language": "en-US,en;q=0.5",
  "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
  "Connection": "keep-alive",
  "Content-Type": "application/json",
  "Cookie": "g_state={\"i_l\":0}; kdt=LGzDmv9Kye5puAFVlNIFwePQezc7vPVSjzlPGA3q; lang=en; dnt=1; d_prefs=MToxLGNvbnNlbnRfdmVyc2lvbjoyLHRleHRfdmVyc2lvbjoxMDAw; guest_id_ads=v1%3A171457429768478803; guest_id_marketing=v1%3A171457429768478803; personalization_id=\"v1_IzbtngGTalp+GLuaBpEhsA==\"; gt=1785673551166525742; _twitter_sess=BAh7CSIKZmxhc2hJQzonQWN0aW9uQ29udHJvbGxlcjo6Rmxhc2g6OkZsYXNo%250ASGFzaHsABjoKQHVzZWR7ADoHaWQiJTVlMmFhN2Y4MmY4MTMyNDI2Mjk1OTE4%250AMjQwZGFhNWQ4Og9jcmVhdGVkX2F0bCsIxyCWNI8BOgxjc3JmX2lkIiVmZjIy%250AMzg3NTUzYzIyYzE1M2I4Zjg5MTI5ZjRjNzk0Nw%253D%253D--d4360a54260c1a6f4f8a1a61a449c4f43d429c6a; guest_id=v1%3A171457429768478803; twid=u%3D1471430559951958016; ct0=c5548399937f51f0cc76c9878342bdf1bbb8f132d733652fb32edc8630110f43fbc81b030f1908f1c86661e58369e19edc16ab986115ce4f6d26e61b5d1195a4cc1d5627915d50cc8893cfe6ed7104e9; auth_token=485cfe31bab71192fd5f94540d34f52bda87ec1f; att=1-taZg5t05RJL7nUzLfOrkqhwuKMYM3OgQ8qqkKPwb",
  "Host": "twitter.com",
  "Sec-Fetch-Dest": "empty",
  "Sec-Fetch-Mode": "cors",
  "Sec-Fetch-Site": "same-origin",
  "TE": "trailers",
  "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
  "x-client-transaction-id": "FBUxbxcpZyHPQnhGimB+F8F+BW0gCfbFu5njMKiVMuhYgWo/H8t4lMJhhUgx7c4Suojl9hUWXzznHUC99tRDZnWbQAOBFw",
  "x-csrf-token": "c5548399937f51f0cc76c9878342bdf1bbb8f132d733652fb32edc8630110f43fbc81b030f1908f1c86661e58369e19edc16ab986115ce4f6d26e61b5d1195a4cc1d5627915d50cc8893cfe6ed7104e9",
  "x-twitter-active-user": "yes",
  "x-twitter-auth-type": "OAuth2Session",
  "x-twitter-client-language": "en"
}

def get_total_topics():
    try:
        with open('logs/topics/topic.json', 'r', encoding='utf-8') as file:
            topics = json.load(file)
            return len(topics.keys())
    except FileNotFoundError:
        print(f"Error: File not found.")
        return None

def get_topic(json_file_path='logs/topics/topic.json'):
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            topics = json.load(file)
            key_index = read_from_log()
            key = list(topics.keys())[key_index]
            return {key: topics[key]}

    except FileNotFoundError:
        print(f"Error: File '{json_file_path}' not found.")
        return {}

def write_to_log(file_path="logs/topics/logTopics.txt", new_line="0"):
    try:
        with open(file_path, 'a', encoding='utf-8') as file:
            file.write(new_line + '\n')  # Append the new line of text followed by a newline character
            #print("New line added to logTopics.txt:", new_line)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")

def read_from_log(file_path="logs/topics/logTopics.txt"):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            if lines:
                last_line = lines[-1].strip()
                return int(last_line)
            else:
                return 0
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None
    
def keep_last_line_only(file_path="logs/topics/logTopics.txt"):
    try:
        # Read all lines from the file
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        # Check if there are more than two lines
        if len(lines) > 1:
            # Extract the last line
            last_line = lines[-1].strip()

            # Write only the last line back to the file
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(last_line + '\n')
                #print("Only the last line kept in logTopics.txt:", last_line)
        else:
            print("No action needed. File has one or zero lines.")

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")

def save_json_to_temp_file(data):
    """
    Saves JSON data to a temporary file and returns the path of the temporary file.

    Args:
        data (dict): Dictionary containing JSON serializable data.

    Returns:
        str: Path of the temporary file where JSON data is stored.
    """
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            # Write JSON data to the temporary file
            json.dump(data, temp_file, indent=4)
            temp_file.flush()  # Flush to ensure data is written to the file
            temp_file.seek(0)  # Move file pointer to the beginning

            # Get the temporary file path
            temp_file_path = temp_file.name

            return temp_file_path

    except Exception as e:
        print(f"Error occurred while saving JSON to temporary file: {e}")
        return None

def read_json_file(file_path):
    """
    Reads JSON data from a file and returns the parsed JSON content as a dictionary.

    Args:
        file_path (str): Path to the JSON file.

    Returns:
        dict or None: Parsed JSON content as a dictionary, or None if an error occurs.
    """
    try:
        with open(file_path, 'r') as json_file:
            json_data = json.load(json_file)
            return json_data
    except FileNotFoundError:
        print(f"Error: JSON file not found at '{file_path}'.")
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON from file '{file_path}'. {e}")
    except Exception as e:
        print(f"Error occurred while reading JSON file '{file_path}': {e}")
    return None

last_keyword = None

def get_random_user():
    global last_keyword
    keywords = [user_header_3]
    
    while True:
        keyword = random.choice(keywords)
        if keyword != last_keyword:
            last_keyword = keyword
            return keyword

def extract_json_data(search,next_page="",header=user_header_1):

    # Define the URL
    url = "https://twitter.com/i/api/graphql/LcI5kBN8BLC7ovF7mBEBHg/SearchTimeline"

    # Define the request parameters
    variables = {"rawQuery": search, "count": 20, "querySource": "typed_query", "product": "Latest","cursor":next_page}
    
    features = {
        "rweb_tipjar_consumption_enabled": False,
        "responsive_web_graphql_exclude_directive_enabled": True,
        "verified_phone_label_enabled": False,
        "creator_subscriptions_tweet_preview_api_enabled": True,
        "responsive_web_graphql_timeline_navigation_enabled": True,
        "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
        "communities_web_enable_tweet_community_results_fetch": True,
        "c9s_tweet_anatomy_moderator_badge_enabled": True,
        "tweetypie_unmention_optimization_enabled": True,
        "responsive_web_edit_tweet_api_enabled": True,
        "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
        "view_counts_everywhere_api_enabled": True,
        "longform_notetweets_consumption_enabled": True,
        "responsive_web_twitter_article_tweet_consumption_enabled": True,
        "tweet_awards_web_tipping_enabled": False,
        "creator_subscriptions_quote_tweet_preview_enabled": False,
        "freedom_of_speech_not_reach_fetch_enabled": True,
        "standardized_nudges_misinfo": True,
        "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
        "tweet_with_visibility_results_prefer_gql_media_interstitial_enabled": False,
        "rweb_video_timestamps_enabled": True,
        "longform_notetweets_rich_text_read_enabled": True,
        "longform_notetweets_inline_media_enabled": True,
        "responsive_web_enhance_cards_enabled": False
    }

    # Define the headers
    headers = header
    # Send the GET request
    response = requests.get(url, params={"variables": json.dumps(variables), "features": json.dumps(features)}, headers=headers)

    # Check if request was successful
    if response.status_code == 200:
        print("Request was successful")

        # Check if the response is compressed
        #print("Content-Encoding:", response.headers.get('Content-Encoding'))

        if response.headers.get('Content-Encoding') == 'br':
            # Decompress the response content
            try:
                response_content = brotli.decompress(response.content)
            except Exception as e:
                #print("Error decompressing content:", e)
                response_content = response.content
        else:
            response_content = response.content

        # Parse the JSON content
        try:
            response_json = json.loads(response_content)
            return response_json
        except json.JSONDecodeError as e:
            print("Error decoding JSON content:", e)
            return None
    else:
        print("Request failed with status code:", response.status_code)
        return {}

def get_response_count(response_json):
    try:
        count = len(response_json['data']['search_by_raw_query']['search_timeline']['timeline']['instructions'][0]['entries'])
        return count
    except KeyError:
        #print("KeyError: Could not find the specified key in the response JSON.")
        return 0

total_topics = get_total_topics()

def extract_batch_data(**kwargs):
  
  tweet_topics = get_topic()
  header = get_random_user()
  
  raw_data = []

  for _, values in tweet_topics.items(): 
      for value in values:
          try:

            response_json = extract_json_data(value,header=header)
            
            if get_response_count(response_json) > 0 :
                raw_data.append(response_json)
            else:
                break
            for i in range(10):
              
              if i == 0 :
                    next_page = len(response_json['data']['search_by_raw_query']['search_timeline']['timeline']['instructions'][0]['entries'])-1
                    next_page = response_json['data']['search_by_raw_query']['search_timeline']['timeline']['instructions'][0]['entries'][next_page]['content']['value']
                    response_json = extract_json_data(value,next_page,header=header)
                    if get_response_count(response_json) > 0:
                        raw_data.append(response_json)
                    else:
                        break
              else :
                  
                    next_page = response_json['data']['search_by_raw_query']['search_timeline']['timeline']['instructions'][2]['entry']['content']['value']
                    response_json = extract_json_data(value,next_page,header=header)
                    
                    if get_response_count(response_json) > 0:
                        raw_data.append(response_json)
                    else:
                        break
                    
              time.sleep(random.uniform(4, 35))
              
            time.sleep(random.uniform(20, 50))

          except Exception as ex:
              print(ex)

  temp_file = save_json_to_temp_file(raw_data) 
  kwargs['ti'].xcom_push(key='raw_batch_data_key', value=temp_file) 
  kwargs['ti'].xcom_push(key='topic_key', value= list(tweet_topics.keys())[0]) 

  if len(raw_data) > 0 : 

    log_value = read_from_log()
    
    if total_topics == log_value:
        write_to_log(new_line="0")
        keep_last_line_only()
    else :
        write_to_log(new_line=str(log_value + 1))

    return True,temp_file,len(raw_data),header
  
  else:
      
      return False,temp_file,len(raw_data),header

def transform_batch_data(**kwargs):
  
  temp_file = kwargs['ti'].xcom_pull(task_ids='extract_tweets_task', key='raw_batch_data_key')
  topic = kwargs['ti'].xcom_pull(task_ids='extract_tweets_task', key='topic_key')

  raw_data = read_json_file(file_path=temp_file)

  tweets_data = []

  for response_json in raw_data : 

      num_tweets = get_response_count(response_json)

      for i in range(num_tweets):
          try:
              data = response_json['data']['search_by_raw_query']['search_timeline']['timeline']['instructions'][0]['entries'][i]

              if 'itemContent' not in data['content']:
                break

              # Extract tweet information from the response JSON
              tweet_data = data['content']['itemContent']['tweet_results']['result']

              # Check if 'tweet' key is present
              if 'tweet' in tweet_data:
                  user_info = tweet_data['tweet']['core']
                  views_info = tweet_data['tweet']['views']
                  tweet_info = tweet_data['tweet']['legacy']
              else:
                  user_info = tweet_data['core']
                  views_info = tweet_data['views']
                  tweet_info = tweet_data['legacy']
              
              # Process tweet information here
              tweet = {
                      'followers_count': user_info['user_results']['result']['legacy']['followers_count'],
                      'friends_count': user_info['user_results']['result']['legacy']['friends_count'],
                      'location': user_info['user_results']['result']['legacy']['location'],
                      'verified': user_info['user_results']['result']['legacy']['verified'],
                      'created_at': tweet_info['created_at'],
                      'hashtags': [hashtag['text'] for hashtag in tweet_info['entities']['hashtags']],
                      'favorite_count': tweet_info['favorite_count'],
                      'full_text': tweet_info['full_text'],
                      'lang': tweet_info['lang'],
                      'quote_count': tweet_info['quote_count'],
                      'reply_count': tweet_info['reply_count'],
                      'retweet_count': tweet_info['retweet_count'],
                      'views_count': views_info.get('count', 0),
                      'topic': topic
                  }

              tweets_data.append(tweet)
                
          except KeyError as ke:
              # Handle missing keys
              print("KeyError:", ke)
              
          except Exception as ex:
              # Handle other exceptions
              print("Exception:", ex)

  temp_file = save_json_to_temp_file(tweets_data) 
  kwargs['ti'].xcom_push(key='clean_data_key', value=temp_file) 
  
  return True,topic,temp_file,len(tweets_data)

def load_to_mongodb(**kwargs):
    
    temp_file = kwargs['ti'].xcom_pull(task_ids='transform_tweets_task', key='clean_data_key')

    data_to_insert = read_json_file(file_path=temp_file)

    #with open("dags/topics/data.json", 'w') as json_file:
    #    json.dump(data_to_insert, json_file, indent=4)

    # MongoDB connection URL
    url = "https://eu-west-2.aws.data.mongodb-api.com/app/data-zoriszx/endpoint/data/v1/action/insertMany"

    try:
        # Convert the list of documents to JSON format
        payload = json.dumps({
            "collection": "TweetsData",  # Specify the collection name
            "database": "TweetsDataBase",  # Specify the database name
            "dataSource": "Cluster0",  # Specify the data source
            "documents": data_to_insert  # Specify the list of documents you want to insert
        })

        # Define headers including API key
        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Request-Headers': '*',
            'api-key': 'VkVWjzEhEqKIlbMq5czRWs077YxAfKpbPdw6YMEwrszzQZWQW2zdi0izXa92HDDO',
        }

        response = requests.post(url, headers=headers, data=payload)
        if len(response.text) > 0 :
            return True,len(data_to_insert)
        else:
            return False,len(data_to_insert)
    except Exception as e:
        print(f"An error occurred: {e}")
        return False,len(data_to_insert)
        
default_args = {
    'owner' : 'MLTeam',
    'retries' : 3,
    'retry_delay' : timedelta(minutes=5)
}

with DAG(
    dag_id='tweets_ETL_pipeline',
    default_args=default_args,
    description= 'This an ETL pipeline',
    start_date=datetime(2024,5,4,12),
    schedule_interval="0 */3 * * *",
    catchup=False
) as dag: 
    
    # Define tasks for each topic
    extract_task = PythonOperator(
        task_id='extract_tweets_task',
        python_callable=extract_batch_data
    )

    transform_task = PythonOperator(
            task_id='transform_tweets_task',
            python_callable=transform_batch_data
        )

    load_task = PythonOperator(
            task_id='load_tweets_to_mongodb_task',
            python_callable=load_to_mongodb
        )

    # Set task dependencies
    extract_task >> transform_task >> load_task