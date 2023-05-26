import os
import re
import requests
import urllib3
import time
import argparse
import logging

import m3u8
from bs4 import BeautifulSoup
from tqdm import tqdm

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SESSION = requests.Session()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def display_banner():
    banner = """
 █████        ████████    █████████  ██████████                                      
░░███        ███░░░░███  ███░░░░░███░░███░░░░███                                     
 ░███       ░░░    ░███ ███     ░░░  ░███   ░░███  ██████  █████ ███ █████ ████████  
 ░███          ███████ ░███          ░███    ░███ ███░░███░░███ ░███░░███ ░░███░░███ 
 ░███         ███░░░░  ░███    █████ ░███    ░███░███ ░███ ░███ ░███ ░███  ░███ ░███ 
 ░███      █ ███      █░░███  ░░███  ░███    ███ ░███ ░███ ░░███████████   ░███ ░███ 
 ███████████░██████████ ░░█████████  ██████████  ░░██████   ░░████░████    ████ █████
░░░░░░░░░░░ ░░░░░░░░░░   ░░░░░░░░░  ░░░░░░░░░░    ░░░░░░     ░░░░ ░░░░    ░░░░ ░░░░░                                                                                                             
============================== Lecture2Go Downloader ==============================
    """
    print(banner)


def fetch_content(url, parse_html=True, verify=True, headers=None, cookies=None, password=None):
    if parse_html:
        logging.info(f"Starting to fetch content from {url}")

    protected = testing_if_site_protected(url)
    if protected:
        logging.info(f"Site is protected")
    
    if protected and not password:
        logging.error(f"Password required for protected videos.")
        exit(1)
    
    if protected and password:
        logging.info(f"Password provided, trying to access protected area...")
      
        params = {
            "_OpenAccessVideos_formDate": int(time.time()),
            "_OpenAccessVideos_password": password,
            "_OpenAccessVideos_tryauth": 1,
            "p_auth": ""
        }

        response = SESSION.post(url, params=params)
        cookies = response.cookies.get_dict()
        SESSION.cookies.update(cookies)

        if ".m3u8" in response.text:
            logging.info(f"Password correct, continuing.")
        else:
            logging.error(f"Password incorrect, exiting.")
            exit(1)

    else:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
        }
        response = SESSION.get(url, headers=headers, verify=verify, cookies=cookies)

    if parse_html:
        return BeautifulSoup(response.text, 'html.parser')
    else:
        return response

def testing_if_site_protected(url):
    url_pattern = r"https://lecture2go\.uni-hamburg\.de/l2go/-/get/v/[a-zA-Z0-9]{24}$"
    return bool(re.match(url_pattern, url))


def get_all_videos_in_series(video_url, password=None):
    soup = fetch_content(video_url, password=password)
    related_videos = []
    for li in soup.find('ul', attrs={'class': 'ul-related'}).find_all('li'):
        related_videos.append({
            "date": li.find('div', attrs={'class': 'video-label'}).text.strip(),
            "title": li.find('h4', attrs={'class': 'video-title'}).find('a').text.strip(),
            "url": li.find('h4', attrs={'class': 'video-title'}).find('a')['href']
        })

    return related_videos[::-1]


def parse_website_for_metadata(video_url, password=None):
    soup = fetch_content(video_url, password=password)
    video_date = soup.find('div', attrs={'id': 'video-info'}).find('div', attrs={'class': 'video-label'}).text.strip()
    video_date = '-'.join(reversed(video_date.split('.')))

    data = {
        "topic": soup.find('div', attrs={'class': 'path'}).find('span', attrs={'class': 'breadcrumb-item'}).text.strip(),
        "title": soup.find('h2', attrs={'class': 'video-title'}).text.strip(),
        "creator": soup.find('div', attrs={'class': 'allcreators'}).find('a').text.strip(),
        "date": video_date
    }

    return data


def choose_resolution(playlist, resolution):
    resolutions = {chunklist.stream_info.resolution[0]: idx for idx, chunklist in enumerate(playlist.playlists)}
    if resolution == "max":
        logging.info(f"Selecting highest resolution.")
        return resolutions[max(resolutions.keys())]
    elif resolution == "min":
        logging.info(f"Selecting lowest resolution.")
        return resolutions[min(resolutions.keys())]
    else:
        print("---------------------------")
        for i, res in enumerate(resolutions.keys()):
            print(f"{i}) : {res}")
        while True:
            res_input = input("Select resolution: ")
            if res_input.isdigit() and int(res_input) in resolutions.values():
                return int(res_input)
            logging.warning(f"Invalid resolution, try again.")


def download_single_video(video_url, video_metadata, password=None, resolution=None):
    response = fetch_content(video_url, parse_html=False, password=password)
    m3u8_url = re.search(r'https://.*m3u8', response.text).group(0)
    playlist = m3u8.load(m3u8_url, verify_ssl=False)
    selected_resolution_idx = choose_resolution(playlist, resolution)

    selected_resolution_chunklist = playlist.playlists[selected_resolution_idx]
    m3u8_chunklist = m3u8.load(selected_resolution_chunklist.absolute_uri, verify_ssl=False)

    os.makedirs("videos", exist_ok=True)
    os.makedirs(f"videos/{video_metadata['topic']}", exist_ok=True)
    video_filename = f'{video_metadata["date"]}_{video_metadata["creator"]}_{video_metadata["title"]}_{time.strftime("%Y%m%d-%H%M%S")}'

    logging.info(f"Downloading {video_filename}...")
    with open(f"videos/{video_metadata['topic']}/{video_filename}.ts", 'wb') as f:
        for segment in tqdm(m3u8_chunklist.segments):
            segment_content = fetch_content(segment.absolute_uri, parse_html=False, verify=False, cookies=response.cookies).content
            f.write(segment_content)

def download_videos(url, password=None, download_all=False, resolution="max"):
    video_urls = []
    
    if download_all:
        logging.info(f"Parsing website for all videos in series...")
        all_videos = get_all_videos_in_series(url, password=password)
        logging.info(f"Found {len(all_videos)} videos in series.")
        for video in all_videos:
            video_urls.append(video["url"])
    else:
        video_urls.append(url)
    
    for video_url in video_urls:
        video_metadata = parse_website_for_metadata(video_url, password=password)
        download_single_video(video_url, video_metadata, password=password, resolution=resolution)
        print("---------------------------")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--url", help="Lecture2Go URL")
    parser.add_argument("-p", "--password", help="Password for protected videos")
    parser.add_argument("-a", "--all", help="Download all videos in series", action="store_true")
    parser.add_argument("-r", "--resolution", help="Always download MIN/MAX resolution", choices=["min", "max"], default="max")
    args = parser.parse_args()

    display_banner()
    download_videos(args.url, password=args.password, download_all=args.all, resolution=args.resolution)

if __name__ == '__main__':
    main()
