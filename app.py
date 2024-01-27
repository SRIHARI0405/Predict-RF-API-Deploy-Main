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
INSTAGRAM_PASSWORD = 'Starbuzz6@'

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

def fetch_followers(user_id, amount=30):
    return cl.user_followers(user_id, amount=amount)

@app.route('/followers/<username>')
def get_profile_route(username):
    try:
        user_info = cl.user_info_by_username(username)
        legitimacy = calculate_username_legitimacy(username)
        user_id = user_info.pk
        followers_data = []
        fetched_followers = 0
        while fetched_followers < 20:  
            followers_batch = fetch_followers(user_id, amount=30)  
            for follower_id in followers_batch:
                follower_info = cl.user_info(follower_id)
                if not follower_info.is_private:
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
                    follower_details_values = [ biography, follower_count, following_count, profile_pic_url, profile_pic_url_hd, media_count, is_private, is_verified, engagement_rate, followers_to_follows_ratio, legitimacy]
                    followers_data.append(follower_details_values)
                    fetched_followers += 1
                    if fetched_followers >= 20:
                        break
                    time.sleep(1)
        
        if followers_data:
            model_filename = 'Final_RFC_model3.pkl'
            ml_model = load_ml_model(model_filename)
            if ml_model:
                print(len(followers_data))
                prediction = ml_model.predict(followers_data)
                print(prediction)
                real_count = np.count_nonzero(prediction == 0)
                fake_count = np.count_nonzero(prediction == 1)
                real_percentage = (real_count / len(prediction)) * 100
                fake_percentage = (fake_count / len(prediction)) * 100

                response = {
                    'success': True,
                    'message': 'Data received successfully',
                    'data': {
                        'username': user_info.username,
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
                'message': 'No followers data found',
                'data': None
            }
        
        json_data = json.dumps(response, ensure_ascii=False)
        return Response(json_data, content_type='application/json; charset=utf-8')

    except Exception as e:
        if "404 Client Error: Not Found" in str(e):
            response = {
                'success': False,
                'message': 'User not found',
                'data': None
            }
        elif "429" in str(e):
            response = {
                'success': False,
                'message': 'Rate limit exceeded',
                'data': None
            }
        else:
            response = {
                'success': False,
                'message': str(e),
                'data': None
            }
        json_data = json.dumps(response, ensure_ascii=False)
        return Response(json_data, content_type='application/json; charset=utf-8')

if __name__ == '__main__':
    try:
        app.run(debug = False)
    except Exception as e:
        print(f"An error occurred: {e}")