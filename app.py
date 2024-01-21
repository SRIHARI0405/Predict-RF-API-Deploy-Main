import time
from flask import Flask, jsonify, Response
import json
import numpy as np
import random
import joblib
import asyncio
from instagrapi import Client

app = Flask(__name__)

INSTAGRAM_USERNAME = 'loopstar154'
INSTAGRAM_PASSWORD = 'Starbuzz123@'

proxy = "socks5://yoqytafd-6:2dng483b96qx@p.webshare.io:80"
cl = Client(proxy=proxy)

try:
    cl.load_settings('session-loop.json')
    cl.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
except Exception as e:
    print(f"Instagram login failed: {e}")



def calculate_username_legitimacy(username):
    username_legitimacy = "1"
    
    if username.count('_') > 4:
        username_legitimacy = "0"
    elif len(username) < 5 or len(username) > 30:
        username_legitimacy = "0"
    elif sum(char.isdigit() for char in username) > 4:
        username_legitimacy = "0"
    
    return username_legitimacy

def load_ml_model(model_filename):
    try:
        model = joblib.load(model_filename)
        return model
    except Exception as e:
        print(f"Error loading the model: {e}")
        return None

@app.route('/followers/<username>')
def get_profile_route(username):
    # max_retries = 3
    # retry_delay = 5
    # for retry_number in range(1, max_retries + 1):
        try:
            user_info = cl.user_info_by_username(username)
            legitimacy = calculate_username_legitimacy(username)
            user_id = user_info.pk
            follower_count_value = user_info.follower_count
            followers_data = []
            followers_data1 = []
            followers = cl.user_followers(user_id, amount = 100)
            for follower_id in followers:
              try:
                follower_info = cl.user_info(follower_id)
                if not follower_info.is_private:
                  followers_data.append(follower_info.pk)
              except Exception as e:
                    if "404 Client Error: Not Found" in str(e):
                        follower_details_values = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                        followers_data.append(follower_details_values)
                        continue
                    else:
                        follower_details_values = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                        followers_data.append(follower_details_values)
                        continue

            follower_data_count = len(followers_data)
            random_profile = 0
            if follower_data_count > 50:
               random_profile = 50
            else:
              random_profile = follower_data_count
            selected_followers = random.sample(followers_data,random_profile)

            for follower_id in selected_followers:
                try:
                    follower_info = cl.user_info(follower_id)
                    biography = 1 if follower_info.biography else 0
                    username = follower_info.username
                    follower_count = follower_info.follower_count
                    following_count = follower_info.following_count
                    profile_pic_url = 1 if follower_info.profile_pic_url else 0
                    profile_pic_url_hd = 1 if follower_info.profile_pic_url_hd else 0
                    media_count = follower_info.media_count
                    is_private = 1 if follower_info.is_private else 0
                    is_verified = 1 if follower_info.is_verified else 0
                    posts = cl.user_medias(follower_id, amount=10)
                    total_posts = len(posts)
                    if total_posts == 0:
                        engagement_rate = 0
                    else:
                        total_likes = sum(post.like_count for post in posts)
                        total_comments = sum(post.comment_count for post in posts)
                        total_interactions = total_likes + total_comments
                        engagement_rate = (total_interactions / total_posts) / max(1, follower_count) * 100
                    followers_to_follows_ratio = round(follower_info.follower_count / max(1, follower_info.following_count), 5)
                    legitimacy = calculate_username_legitimacy(username)
                    follower_details_values = [biography, follower_count, following_count, profile_pic_url, profile_pic_url_hd, media_count, is_private, is_verified, engagement_rate, followers_to_follows_ratio, legitimacy]
                    followers_data1.append(follower_details_values)
                except Exception as e:
                    print(f"Error fetching detailed info for {follower_id}: {e}")

            if followers_data1:
                model_filename = 'Final_RFC_model3.pkl'
                ml_model = load_ml_model(model_filename)
                if ml_model is not None:
                    prediction = ml_model.predict(followers_data1)
                    real_count = np.count_nonzero(prediction == 0)
                    fake_count = np.count_nonzero(prediction == 1)
                    real_percentage = (real_count / len(prediction)) * 100
                    fake_percentage = (fake_count / len(prediction)) * 100

                    response = {
                        'success': True,
                        'message': 'Data received successfully',
                        'data': {
                            'Data': user_info.username,
                            'real_percentage': round(real_percentage, 2),
                            'fake_percentage': round(fake_percentage, 2)
                        }
                    }
                else:
                    response = {
                        'success': False,
                        'message': 'Error loading ML model',
                        'data': None
                    }
            else:
                response = {
                    'success': False,
                    'message': 'No non-private followers found.',
                    'data': None
                }
            followers_data = []
            followers_data1 = []
            json_data = json.dumps(response, ensure_ascii=False)
            return Response(json_data, content_type='application/json; charset=utf-8')

        except Exception as e:
            if "404 Client Error: Not Found" in str(e):
                follower_details_values = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                followers_data.append(follower_details_values)
                # continue
            elif "429" in str(e):
                # print(f"Rate limit exceeded. Retrying in {retry_delay} seconds (Retry {retry_number}/{max_retries}).")
                # time.sleep(retry_delay)
                print('delay')
            else:
                response = {
                    'success': False,
                    'message': f"{e}",
                    'data': None
                }
                return jsonify(response)

    # response = {
    #     'success': False,
    #     'message': 'Max retries reached. Unable to fetch profile.',
    #     'data': None
    # }
    # return jsonify(response)


if __name__ == '__main__':
    try:
        app.run(debug = False)
    except Exception as e:
        print(f"An error occurred: {e}")