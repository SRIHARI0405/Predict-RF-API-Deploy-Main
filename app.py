import time
from flask import Flask, jsonify
import random
import numpy as np
import joblib
import multiprocessing
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


def load_ml_model(model_filename):
    try:
        model = joblib.load(model_filename)
        return model
    except Exception as e:
        print(f"Error loading the model: {e}")
        return None

def calculate_username_legitimacy(username):
    username_legitimacy = "1"

    if username.count('_') > 4:
        username_legitimacy = "0"
    elif len(username) < 5 or len(username) > 30:
        username_legitimacy = "0"
    elif sum(char.isdigit() for char in username) > 4:
        username_legitimacy = "0"

    return username_legitimacy

def fetch_follower_info(follower_id):
    try:
        follower_info = cl.user_info(follower_id)
        return follower_info
    except Exception as e:
        print(f"Error processing follower {follower_id}: {e}")
        return None

@app.route('/followers/<username>')
def get_profile_route(username):
    try:
        user_info = cl.user_info_by_username(username)
        user_id = user_info.pk

        followers = cl.user_followers(user_id, amount=60)
        followers = list(followers)
        with multiprocessing.Pool(processes=8) as pool:
            follower_infos = pool.map(fetch_follower_info, followers)
        
        followers_data = []
        fake_followers_data = []
        for follower_info in follower_infos:
            if follower_info and not follower_info.is_private:
                biography = 1 if follower_info.biography else 0
                username = follower_info.username
                follower_count = follower_info.follower_count
                following_count = follower_info.following_count
                profile_pic_url = 1 if follower_info.profile_pic_url else 0
                profile_pic_url_hd = 1 if follower_info.profile_pic_url_hd else 0
                media_count = follower_info.media_count
                is_private = 1 if follower_info.is_private else 0
                is_verified = 1 if follower_info.is_verified else 0
                posts = cl.user_medias(follower_info.pk, amount=10)
                total_posts = len(posts)
                if total_posts == 0:
                    engagement_rate = 0
                else:
                    total_likes = sum(post.like_count for post in posts)
                    total_comments = sum(post.comment_count for post in posts)
                    total_interactions = total_likes + total_comments
                    engagement_rate = (total_interactions / total_posts) / max(1, follower_count) * 100
                followers_to_follows_ratio = round(follower_info.follower_count / max(1, follower_info.following_count), 5)
                # legitimacy = calculate_username_legitimacy(username)
                # legit = []
                # with multiprocessing.Pool(processes=4) as pool:
                #   legit = pool.map(calculate_username_legitimacy, username)
                # legitimacy = legit[0];
                # print(legitimacy)
                if username.count('_') > 4:
                  username_legitimacy = "0"
                elif len(username) < 5 or len(username) > 30:
                  username_legitimacy = "0"
                elif sum(char.isdigit() for char in username) > 4:
                  username_legitimacy = "0"
                else:
                  username_legitimacy = 1
                follower_details_values = [biography, follower_count, following_count, profile_pic_url, profile_pic_url_hd, media_count, is_private, is_verified, engagement_rate, followers_to_follows_ratio, username_legitimacy]
                followers_data.append(follower_details_values)
            else:
                fake_followers_data.append(follower_info.pk)

        selected_followers = random.sample(followers_data, min(len(followers_data), 50))
        if selected_followers:
            model_filename = 'Final_RFC_model3.pkl'
            ml_model = load_ml_model(model_filename)
            if ml_model:
                prediction = ml_model.predict(selected_followers)
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
                return jsonify(response)
            else:
                response = {
                    'success': False,
                    'message': 'Error loading ML model',
                    'data': None
                }
        else:
            response = {
                'success': False,
                'message': 'Error selecting followers for ML processing',
                'data': None
            }
    except Exception as e:
        print(f"An error occurred: {e}")
        response = {
            'success': False,
            'message': 'An error occurred',
            'data': None
        }
    return jsonify(response)

if __name__ == '__main__':
    try:
        app.run(debug=False)
    except Exception as e:
        print(f"An error occurred: {e}")