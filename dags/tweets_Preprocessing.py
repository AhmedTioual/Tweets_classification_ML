from airflow.decorators import dag, task,task_group
from airflow.utils.task_group import TaskGroup
from airflow.utils.dates import days_ago
from datetime import timedelta, datetime
import requests
import json
import re
import demoji
import string
from pymongo import MongoClient
import pandas as pd
import nltk
import spacy
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer, SnowballStemmer, ISRIStemmer, WordNetLemmatizer
from nltk.corpus import stopwords
from collections import Counter
from tashaphyne.stemming import ArabicLightStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report, accuracy_score
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score, RandomizedSearchCV,GridSearchCV
from sklearn.metrics import classification_report, accuracy_score
from sklearn.svm import SVC
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from scipy.stats import randint
import joblib
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.linear_model import LogisticRegression
import numpy as np
import tempfile
import pickle

# Download NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')

# Download demoji codes
demoji.download_codes()

# Initialize stemmers and lemmatizers
stemmer_en = PorterStemmer()
stemmer_fr = SnowballStemmer('french')
stemmer_ar = ISRIStemmer()
lemmatizer_en = WordNetLemmatizer()
ar_stemmer = ArabicLightStemmer()

# Load spaCy models
nlp_en = spacy.load('en_core_web_sm')
nlp_fr = spacy.load('fr_core_news_sm')

# Stop Words
stop_words_en = set(stopwords.words('english'))
stop_words_fr = set(stopwords.words('french'))
stop_words_ar = set(stopwords.words('arabic'))

default_args = {
    'owner': 'MLTeam',
    'retries': 3,
    'retry_delay': timedelta(minutes=10)
}

@dag(
    dag_id='tweets_Preprocessing_pipeline',
    default_args=default_args,
    description='This DAG is for Tweets Preprocessing Before Applying it to ML models',
    start_date=datetime(2024, 5, 24, 12, 0, 0),
    schedule_interval='@weekly',
    catchup=False
)

def tweets_preprocessing_pipeline():
    
    @task
    def load_data():
        # MongoDB API endpoint URL
        url = "https://eu-west-2.aws.data.mongodb-api.com/app/data-zoriszx/endpoint/data/v1/action/find"
        limit = 20000  # Maximum number of documents to fetch per request
        skip = 0  # Starting point
        all_documents = []  # List to store all documents

        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Request-Headers': '*',
            'api-key': 'VkVWjzEhEqKIlbMq5czRWs077YxAfKpbPdw6YMEwrszzQZWQW2zdi0izXa92HDDO',
        }

        while True:
            # Define payload with the required parameters
            payload = json.dumps({
                "collection": "TweetsData",  # Specify the collection name
                "database": "TweetsDataBase",  # Specify the database name
                "dataSource": "Cluster0",  # Specify the data source
                "projection": {
                    "full_text": 1,
                    "lang": 1,
                    "topic": 1,
                    "_id": 0
                },
                "limit": limit,
                "skip": skip
            })

            # Make a POST request to fetch data from MongoDB API
            response = requests.post(url, headers=headers, data=payload)

            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                data = response.json()
                documents = data.get('documents', [])

                if not documents:  # Break the loop if no more documents are found
                    break

                all_documents.extend(documents)
                skip += limit  # Increment skip by limit to fetch the next batch

            else:
                print("Failed to fetch data from MongoDB API. Status code:", response.status_code)
                return None

        # Convert the list of all documents to a DataFrame
        df = pd.DataFrame(all_documents)
        df.rename(columns={'full_text': 'tweet'}, inplace=True)
        
        return df

    @task
    def data_quality(data_frame):
        data_frame['tweet'] = data_frame['tweet'].str.lower()

        filter_condition_eco = (
            (data_frame['topic'] == 'Economy') &
            (
                data_frame['tweet'].str.contains('eco') |
                data_frame['tweet'].str.contains('invest') |
                data_frame['tweet'].str.contains('قتص') |
                data_frame['tweet'].str.contains('مال') |
                data_frame['tweet'].str.contains('تجار')
            )
        )
        # Update the original DataFrame to keep only the filtered data for 'Economy' topic
        data_frame = data_frame.loc[~(data_frame['topic'] == 'Economy') | filter_condition_eco]

        filter_condition_politics = (
            (data_frame['topic'] == 'Politics') &
            (
                data_frame['tweet'].str.contains('polit') |
                data_frame['tweet'].str.contains('سياس') |
                data_frame['tweet'].str.contains('حكو')
            )
        )

        # Update the original DataFrame to keep only the filtered data for 'Economy' topic
        data_frame = data_frame.loc[~(data_frame['topic'] == 'Politics') | filter_condition_politics]

        filter_condition_tourism = (
            (data_frame['topic'] == 'Tourism') &
            (
                data_frame['tweet'].str.contains('touri') |
                data_frame['tweet'].str.contains('سياح')
            )
        )
        # Update the original DataFrame to keep only the filtered data for 'Economy' topic
        data_frame = data_frame.loc[~(data_frame['topic'] == 'Tourism') | filter_condition_tourism]

        filter_condition_techno = (
            (data_frame['topic'] == 'Technology') &
            (
                data_frame['tweet'].str.contains('techno') |
                data_frame['tweet'].str.contains('تكنو')
            )
        )

        # Update the original DataFrame to keep only the filtered data for '' topic
        data_frame = data_frame.loc[~(data_frame['topic'] == 'Technology') | filter_condition_techno]

        return data_frame

    @task
    def clean_dataframe(data):
        data['tweet'] = data['tweet'].str.lower()
        data = data[(data['lang'].isin(['fr', 'ar', 'en']))]
        data.drop_duplicates(subset=['tweet'],inplace=True)
        data.dropna(subset=['tweet'],inplace=True)
        data = data[data['tweet'] != '']
        return data

    @task
    def clean_text(data):
        # Your clean_text implementation
        def clean_text_func(text):
            #remove hyperlinks
            tweet = re.sub(r'https?://\S+|www\.\S+', '', text)
            # Remove tags (@xxxxx)
            tweet = re.sub(r'@\w+', '', tweet)
            # Remove special characters
            tweet = re.sub(r'\W', ' ', tweet)
            # Remove emojis
            tweet = demoji.replace(tweet, '')
            # Remove punctuation
            tweet = tweet.translate(str.maketrans('', '', string.punctuation))
            # Remove digits
            tweet = re.sub(r'[\W\d٠١٢٣٤٥٦٧٨٩]', ' ', tweet)
            # Lowercase
            return tweet.lower()
        
        data['tweet'] = data['tweet'].apply(clean_text_func)

        return data
    
    @task
    def word_tokenization(data):
        #word_tokenization implementation
        def word_tokenization_func(text, lang):
            if lang == 'en':
                return word_tokenize(text)
            elif lang == 'fr':
                return word_tokenize(text)
            elif lang == 'ar':
                #arabic_tokens = re.findall(r'\b[\w\']+\b', text, re.UNICODE)
                return word_tokenize(text)#arabic_tokens
            else:
                # Fallback to English
                return word_tokenize(text)
            
        data['tweet'] = data.apply(lambda row: word_tokenization_func(row['tweet'], row['lang']), axis=1)

        return data

    @task
    def remove_stop_words(data):
        # Remove_stop_words implementation
        # Define the function to remove stop words
        def remove_stop_words_func(tokens, lang):
            if lang == 'en':
                filtered_tokens = [token for token in tokens if token.lower() not in stop_words_en]
            elif lang == 'fr':
                filtered_tokens = [token for token in tokens if token.lower() not in stop_words_fr]
            elif lang == 'ar':
                filtered_tokens = [token for token in tokens if token not in stop_words_ar]
            else:
                filtered_tokens = tokens  # If language is not recognized, return the tokens as is
            
            return ' '.join(filtered_tokens)  # Join the tokens back into a string

        # Apply the function to each row in the dataframe
        data['tweet'] = data.apply(lambda row: remove_stop_words_func(row['tweet'], row['lang']), axis=1)

        return data

    @task
    def lemmatization(data):
    # lemmatization implementation
        def lemmatization_func(tokens, lang):
            if lang == 'en':
                tokens = word_tokenize(tokens)
                lemmatized_tokens = [lemmatizer_en.lemmatize(word) for word in tokens]
            elif lang == 'fr':
                doc = nlp_fr(tokens)
                lemmatized_tokens = [token.lemma_ for token in doc if token.is_alpha]
            elif lang == 'ar':
                tokens = word_tokenize(tokens)
                lemmatized_tokens = [ar_stemmer.light_stem(word) for word in tokens]
            else:
                lemmatized_tokens = tokens  # If language is not recognized, return the tokens as is
            
            return ' '.join(lemmatized_tokens)  # Join the tokens back into a string

        data['tweet'] = data.apply(lambda row: lemmatization_func(row['tweet'], row['lang']), axis=1)

        return data

    @task
    def remove_rare_frequent_words(df=None):
        # Count the word occurrences
        word_counts = Counter(word for tweet in df['tweet'] for word in tweet.split())

        # Identify rare and too frequent words
        total_tweets = len(df)
        rare_words = set(word for word, count in word_counts.items() if count <= 2) # Test This without rare words
        frequent_words = set(word for word, count in word_counts.items() if count >= total_tweets * 0.95)
        words_to_remove = rare_words | frequent_words

        # Remove rare and too frequent words from tweets
        df['tweet'] = df['tweet'].apply(lambda x: ' '.join([word for word in x.split() if word not in words_to_remove]))

        return df

    @task
    def balance_data(data):
        return pd.concat([data[data['topic'] == topic].sample(n=data['topic'].value_counts().min(), random_state=42) for topic in data['topic'].unique()])
    
    @task
    def feature_extraction(data, vectorizer=TfidfVectorizer()):
        # Vectorize the text data
        X = vectorizer.fit_transform(data['tweet'])
        # Get the target variable
        y = data['topic']
        
        # Convert sparse matrix X to a dense DataFrame
        X_df = pd.DataFrame(X.toarray(), columns=[str(i) for i in range(X.shape[1])])
        
        # Concatenate X_df and y into a single DataFrame
        result_df = pd.concat([X_df, y.reset_index(drop=True)], axis=1)
        
        return result_df

    
    @task(multiple_outputs=True)
    def split_data(data, test_size=0.2, val_size=0.1, random_state=42):
        X = data.iloc[:, :-1]  # All columns except the last one
        y = data.iloc[:, -1]   # The last column

        X_train_full, X_test, y_train_full, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)
        X_train, X_val, y_train, y_val = train_test_split(X_train_full, y_train_full, test_size=val_size, random_state=random_state)

        # Create temporary files
        X_train_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pkl')
        X_val_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pkl')
        X_test_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pkl')
        y_train_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pkl')
        y_val_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pkl')
        y_test_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pkl')

        # Save the data to temporary files
        X_train.to_pickle(X_train_file.name)
        X_val.to_pickle(X_val_file.name)
        X_test.to_pickle(X_test_file.name)
        y_train.to_pickle(y_train_file.name)
        y_val.to_pickle(y_val_file.name)
        y_test.to_pickle(y_test_file.name)

        # Close the files
        X_train_file.close()
        X_val_file.close()
        X_test_file.close()
        y_train_file.close()
        y_val_file.close()
        y_test_file.close()

        return {
            'X_train_file': X_train_file.name,
            'X_val_file': X_val_file.name,
            'X_test_file': X_test_file.name,
            'y_train_file': y_train_file.name,
            'y_val_file': y_val_file.name,
            'y_test_file': y_test_file.name
        }
        
    @task(multiple_outputs=True)
    def cross_validation(model=None, X_train_file=None, y_train_file=None, cv=3):
        # Load training data
        X_train = pd.read_pickle(X_train_file)
        y_train = pd.read_pickle(y_train_file)
        
        # Perform cross-validation
        cv_scores = cross_val_score(model, X_train, y_train, cv=cv)
        mean_cv_score = cv_scores.mean()
        
        # Serialize the model to a pickle file
        model_file = f"/tmp/{model.__class__.__name__}model.pkl"  # Or any other desired location
        with open(model_file, "wb") as f:
            pickle.dump(model, f)
        
        return {
            'model_file': model_file,
            'mean_cv_score': mean_cv_score
        }

    @task(multiple_outputs=True)
    def best_model(modelsDict):
        best_model = None
        best_cv_score = -float('inf')  # Initialize to negative infinity to ensure any model's score is higher

        for model in modelsDict:
            mean_cv_score = model['mean_cv_score']
            if mean_cv_score > best_cv_score:
                best_cv_score = mean_cv_score
                best_model = model
        
        return {
            'model_file': best_model['model_file'],
            'cv_score': best_model['mean_cv_score']
        }
    
    @task
    # Model Training and Evaluation
    def train_evaluate_model(X_train, y_train, X_val, y_val, model):
        classifier = model
        classifier.fit(X_train, y_train)
        y_val_pred = classifier.predict(X_val)
        accuracy = accuracy_score(y_val, y_val_pred)
        precision = precision_score(y_val, y_val_pred, average='weighted')
        recall = recall_score(y_val, y_val, average='weighted')
        f1 = f1_score(y_val, y_val, average='weighted')
        return {
            'modelName':classifier,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1
        }
    
    @task
    def hyperparameters_tuning(X_train, y_train, n_iter=50, random_state=42,best_model=None):
        if isinstance(best_model, LogisticRegression):
            param_grid = {
                'C': [0.1, 1, 10, 100],
                'solver': ['liblinear', 'saga']
            }
        elif isinstance(best_model, RandomForestClassifier):
            param_grid = {
                'n_estimators': [50, 100, 200],
                'max_depth': [None, 10, 20, 30]
            }
        elif isinstance(best_model, SVC):
            param_grid = {
                'C': [0.1, 1, 10, 100],
                'gamma': ['scale', 'auto']
            }
        elif isinstance(best_model, DecisionTreeClassifier):
            param_grid = {
                'max_depth': [None, 10, 20, 30],
                'min_samples_split': [2, 5, 10]
            }
        grid_search = GridSearchCV(best_model, param_grid, cv=5, scoring='accuracy')
        grid_search.fit(X_train, y_train)
        return {
                'bestModel':grid_search.best_estimator_,
                'bestParams':grid_search.best_params_
            }
    
        # Retrain the best model with the best parameters

    @task_group(group_id='data_preparation', tooltip='Data Preparation Tasks')
    def data_preparation_group():
        load_data_task = load_data()
        data_verification_task = data_quality(data_frame=load_data_task)
        clean_dataframe_task = clean_dataframe(data=data_verification_task)
        return clean_dataframe_task

    @task_group(group_id='text_processing', tooltip='Text Processing Tasks')
    def text_processing_group(clean_dataframe_task):
        clean_tweets_task = clean_text(data=clean_dataframe_task)
        word_tokenization_task = word_tokenization(data=clean_tweets_task)
        remove_stop_words_task = remove_stop_words(data=word_tokenization_task)
        return remove_stop_words_task

    @task_group(group_id='final_preparation', tooltip='Final Preparation Tasks')
    def final_preparation_group(remove_stop_words_task):
        final_clean_dataframe_task = clean_dataframe(data=remove_stop_words_task)
        lemmatization_task = lemmatization(data=final_clean_dataframe_task)
        remove_rare_frequent_words_task = remove_rare_frequent_words(df=lemmatization_task)
        balance_data_task = balance_data(data=remove_rare_frequent_words_task)
        return balance_data_task

    @task_group(group_id='feature_extraction_and_split', tooltip='Feature Extraction and Split')
    def feature_extraction_split_group(balance_data_task):
        feature_extraction_TF_IDF_task = feature_extraction(data=balance_data_task)
        split_data_task = split_data(data=feature_extraction_TF_IDF_task)
        return split_data_task

    @task_group(group_id='cross_validation', tooltip='Cross Validation')
    def cross_validation_group(split_data_task):
        # Define models
        models = [
            SVC(kernel='linear'), # rbf
            DecisionTreeClassifier(),
            RandomForestClassifier(),
            LogisticRegression(max_iter=1000)
        ]
        # Create tasks for cross-validation with each model
        cv_tasks = {}
        for model in models:
            cv_task = cross_validation(
                model=model,
                X_train_file=split_data_task['X_train_file'],
                y_train_file=split_data_task['y_train_file']
            )
            cv_tasks[model.__class__.__name__] = cv_task['mean_cv_score']

        return cv_tasks
    
    #load_data_task >> data_verification_task >> clean_dataframe_task >> clean_tweets_task >> word_tokenization_task >> remove_stop_words_task >> final_clean_dataframe_task >> lemmatization_task >> remove_rare_frequent_words_task >> balance_data_task >> feature_extraction_TF_IDF_task >> split_data_task >> [cv_SVM]
    clean_dataframe_task = data_preparation_group()
    remove_stop_words_task = text_processing_group(clean_dataframe_task)
    balance_data_task = final_preparation_group(remove_stop_words_task)
    feature_extraction_split_task = feature_extraction_split_group(balance_data_task)
    cross_validation_task = cross_validation_group(feature_extraction_split_task)
    best_model_task = best_model(cross_validation_task)

tweets_preprocessing_pipeline_dag = tweets_preprocessing_pipeline()