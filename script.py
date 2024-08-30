import logging
import requests
import string
import random
import json
import os
import cv2
import numpy as np
from pathlib import Path
from PIL import Image
import io
import time
import b2sdk.v2 as b2
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed

B2_KEY_ID = ''
B2_APP_KEY = ''
B2_BUCKET_NAME = ''

log_file_path = "script_output.log" 
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path), 
        logging.StreamHandler()
    ]
)

info = b2.InMemoryAccountInfo()
b2_api = b2.B2Api(info)
b2_api.authorize_account("production", B2_KEY_ID, B2_APP_KEY)
bucket = b2_api.get_bucket_by_name(B2_BUCKET_NAME)


def main():
    config_path = './config.json'
    config = load_config(config_path)
    usernames = config["usernames"]
    process_usernames_in_parallel(usernames, config)


if __name__ == '__main__':
    main()


def load_config(config_path):
    with open(config_path, 'r') as file:
        config = json.load(file)
    return config


def generate_user_agent():
    iphone_models = ['iPhone11,8', 'iPhone10,6', 'iPhone12,1', 'iPhone12,3', 'iPhone12,5']
    ios_versions = ['12_3_1', '13_3_1', '14_4_1', '13_5_1', '14_0_1', '14_1_2', '15_0_2']
    locales = ['en_US']
    instagram_versions = ['105.0.0.11.118', '107.0.0.12.121', '108.0.0.14.124', '110.0.0.16.119', '111.0.0.25.121',
                          '113.0.0.39.122']

    iphone = random.choice(iphone_models)
    ios = random.choice(ios_versions)
    locale = random.choice(locales)
    instagram = random.choice(instagram_versions)

    user_agent = f'Mozilla/5.0 (iPhone; CPU iPhone OS {ios} like Mac OS X) ' \
                 f'AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 ' \
                 f'Instagram {instagram} ({iphone}; iOS {ios}; {locale}; {locale}; scale=2.00; 828x1792; 165586599)'

    return user_agent


def read_proxy_file(file_path):
    with open(file_path, 'r') as file:
        line = file.readline().strip()
        proxy_host, proxy_port, proxy_username, proxy_password = line.split(':')
    return proxy_host, proxy_port, proxy_username, proxy_password


def generate_random_cookies():
    cookie_keys = ['sessionid', 'csrftoken', 'mid', 'ig_did', 'shbid', 'rur', 'shbts', 'ds_user_id', 'urlgen']

    cookies = {}
    for key in cookie_keys:
        random_value = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(32))
        cookies[key] = random_value

    return cookies


def extract_values(obj, key):
    arr = []

    def extract(obj, arr, key):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    extract(v, arr, key)
                elif k == key:
                    arr.append(v)
        elif isinstance(obj, list):
            for item in obj:
                extract(item, arr, key)
        return arr

    results = extract(obj, arr, key)
    return results


def create_user_image_dict(username, urls):
    result = {"username": username}

    for i, url in enumerate(urls):
        result[f"image_{i + 1}"] = url

    return result


def read_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()


def get_random_proxy(proxy_list):
    return random.choice(proxy_list).strip()


def download_image(url, proxy_dict, max_retries=5, delay=0.1):
    attempt = 0
    while attempt < max_retries:
        try:
            response = requests.get(url, proxies=proxy_dict, stream=True)
            response.raise_for_status()  # Raise an exception for HTTP errors
            img = Image.open(io.BytesIO(response.content))
            return img
        except requests.exceptions.RequestException as e:
            attempt += 1
            logging.warning(f"Attempt {attempt} failed to download image: {e}")
            if attempt >= max_retries:
                logging.error("Max retries reached. Unable to download image.")
                return None
            time.sleep(delay)


def detect_faces(image):
    open_cv_image = np.array(image)
    gray_image = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray_image, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    return len(faces) > 0


def compress_image(image, target_size_kb):
    quality = 95
    step = 5
    while True:
        byte_stream = io.BytesIO()
        image.save(byte_stream, format='JPEG', quality=quality)
        size_kb = byte_stream.tell() / 1024
        if size_kb <= target_size_kb or quality <= 10:
            break
        quality -= step
    return byte_stream


def save_image(byte_stream, output_path):
    try:
        with open(output_path, 'wb') as out_file:
            out_file.write(byte_stream.getvalue())
        logging.info(f"Compressed image saved to {output_path}")
    except Exception as e:
        logging.error(f"Error saving image to {output_path}: {e}")


def process_username_images(username, urls, datacenter_proxies, target_size_kb=10):
    output_dir = f"scraped_images/{username}"
    os.makedirs(output_dir, exist_ok=True)

    for index, url in enumerate(urls):
        key = f"image_{index + 1}"

        proxy = get_random_proxy(datacenter_proxies)
        proxy_host, proxy_port, proxy_username, proxy_password = proxy.split(':')
        proxy_url = f"http://{proxy_username}:{proxy_password}@{proxy_host}:{proxy_port}"
        proxy_dict = {"http": proxy_url, "https": proxy_url}

        image = download_image(url, proxy_dict, max_retries=5, delay=0.1)
        if image:
            if detect_faces(image):
                byte_stream = compress_image(image, target_size_kb)
                output_path = os.path.join(output_dir, f"{username}_{key}.jpg")
                logging.info(f"Saving image {username}_{key}.jpg.")
                save_image(byte_stream, output_path)
            else:
                logging.info(f"No face detected in image {username}_{key}. Not saving...")


def upload_file(file_path):
    try:
        file_name = os.path.basename(file_path)
        local_file = Path(file_path).resolve()
        logging.info(f'Uploading: {file_path}')

        uploaded_file = bucket.upload_local_file(
            local_file=local_file,
            file_name=file_name,
        )

        logging.info(f"Uploaded {file_path} : {uploaded_file}")
    except FileNotFoundError:
        logging.error(f"File {file_path} not found.")
    except Exception as e:
        logging.error(f"Error uploading {file_path}: {e}")


def upload_directory_to_b2(directory):
    with ThreadPoolExecutor() as executor:
        futures = []

        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                futures.append(executor.submit(upload_file, file_path))

        for future in as_completed(futures):
            future.result()  # This will raise an exception if the upload failed


def delete_file(file_path):
    try:
        os.remove(file_path)
        logging.info(f"Deleted {file_path}")
    except FileNotFoundError:
        logging.error(f"File {file_path} not found.")
    except Exception as e:
        logging.error(f"Error deleting {file_path}: {e}")


def delete_files_in_directory(directory):
    with ThreadPoolExecutor() as executor:
        futures = []

        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                futures.append(executor.submit(delete_file, file_path))

        for future in as_completed(futures):
            future.result()  # This will raise an exception if the delete failed


def process_username_full(username, config):
    file_name = f"./jsons/{username}'s_JSON_QUERY.json"

    if os.path.exists(file_name):
        logging.info(f"File for {username} already exists. Skipping...")
        return

    res_proxy = config["res-proxy"]
    datacenter_proxies = config["datacenter-proxies"]

    proxy_host, proxy_port, proxy_username, proxy_password = res_proxy.split(':')
    proxy_url = f"http://{proxy_username}:{proxy_password}@{proxy_host}:{proxy_port}"

    proxy_dict = {
        "http": proxy_url,
        "https": proxy_url
    }

    headers = {'User-Agent': generate_user_agent()}
    cookies = generate_random_cookies()

    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"

    try:
        response = requests.get(url, headers=headers, cookies=cookies, proxies=proxy_dict)
        response.raise_for_status()  # Raise an exception for HTTP errors

        json_response = response.json()

        with open(file_name, 'w') as file:
            json.dump(json_response, file)

        with open(f"./jsons/{username}'s_JSON_QUERY.json") as file:
            data = json.load(file)

        working_urls = list(set(extract_values(data, 'display_url')))

        process_username_images(username, working_urls, datacenter_proxies, target_size_kb=10)

    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed for {username}: {e}")
    except ValueError:
        logging.error("Response content is not in JSON format.")
    except Exception as e:
        logging.error(f"Error processing username {username}: {e}")

    try:
        upload_directory_to_b2(f"scraped_images/{username}")
        delete_files_in_directory(f"scraped_images/{username}")
    except Exception as e:
        logging.error(f"Error during upload or delete process: {e}")


def process_usernames_in_parallel(usernames, config, max_workers=128):
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_username_full, username, config) for username in usernames]
        for future in as_completed(futures):
            future.result()  # This will raise an exception if the task failed



