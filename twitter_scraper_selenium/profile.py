#!/usr/bin/env python3

from .driver_initialization import Initializer
from .driver_utils import Utilities
from .element_finder import Finder
from .driver_utils import Utilities
import re
import json
import csv
import os
import logging

logging.getLogger().setLevel(logging.INFO)


class Profile:
    """this class needs to be instantiated in orer to scrape post of some
    twitter profile"""

    def __init__(self, twitter_username, browser, proxy, tweets_count, headless, browser_profile):
        self.twitter_username = twitter_username
        self.URL = "https://twitter.com/{}".format(twitter_username.lower())
        self.__driver = ""
        self.browser = browser
        self.proxy = proxy
        self.tweets_count = tweets_count
        self.posts_data = {}
        self.retry = 10
        self.headless = headless
        self.browser_profile = browser_profile

    def __start_driver(self):
        """changes the class member __driver value to driver on call"""
        self.__driver = Initializer(
            self.browser, self.headless, self.proxy, self.browser_profile).init()

    def __close_driver(self):
        self.__driver.close()
        self.__driver.quit()

    def __check_tweets_presence(self, tweet_list):
        if len(tweet_list) <= 0:
            self.retry -= 1

    def __check_retry(self):
        return self.retry <= 0

    def __fetch_and_store_data(self):
        try:
            all_ready_fetched_posts = []
            present_tweets = Finder._Finder__fetch_all_tweets(self.__driver)
            self.__check_tweets_presence(present_tweets)
            all_ready_fetched_posts.extend(present_tweets)

            while len(self.posts_data) < self.tweets_count:
                for tweet in present_tweets:
                    status, tweet_url = Finder._Finder__find_status(tweet)
                    replies = Finder._Finder__find_replies(tweet)
                    retweets = Finder._Finder__find_shares(tweet)
                    status = status[-1]
                    username = tweet_url.split("/")[3]
                    is_retweet = True if self.twitter_username.lower() != username.lower() else False
                    name = Finder._Finder__find_name_from_post(
                        tweet, is_retweet)
                    retweet_link = tweet_url if is_retweet is True else ""
                    posted_time = Finder._Finder__find_timestamp(tweet)
                    content = Finder._Finder__find_content(tweet)
                    likes = Finder._Finder__find_like(tweet)
                    images = Finder._Finder__find_images(tweet)
                    videos = Finder._Finder__find_videos(tweet)
                    hashtags = re.findall(r"#(\w+)", content)
                    mentions = re.findall(r"@(\w+)", content)
                    profile_picture = "https://twitter.com/{}/photo".format(
                        username)
                    link = Finder._Finder__find_external_link(tweet)
                    self.posts_data[status] = {
                        "tweet_id": status,
                        "username": username,
                        "name": name,
                        "profile_picture": profile_picture,
                        "replies": replies,
                        "retweets": retweets,
                        "likes": likes,
                        "is_retweet": is_retweet,
                        "retweet_link": retweet_link,
                        "posted_time": posted_time,
                        "content": content,
                        "hashtags": hashtags,
                        "mentions": mentions,
                        "images": images,
                        "videos": videos,
                        "tweet_url": tweet_url,
                        "link": link
                    }

                Utilities._Utilities__scroll_down(self.__driver)
                Utilities._Utilities__wait_until_completion(self.__driver)
                Utilities._Utilities__wait_until_tweets_appear(self.__driver)
                present_tweets = Finder._Finder__fetch_all_tweets(
                    self.__driver)
                present_tweets = [
                    post for post in present_tweets if post not in all_ready_fetched_posts]
                self.__check_tweets_presence(present_tweets)
                all_ready_fetched_posts.extend(present_tweets)
                if self.__check_retry() is True:
                    break

        except Exception as ex:
            logging.exception(
                "Error at method fetch_and_store_data : {}".format(ex))

    def scrap(self):
        try:
            self.__start_driver()
            self.__driver.get(self.URL)
            Utilities._Utilities__wait_until_completion(self.__driver)
            Utilities._Utilities__wait_until_tweets_appear(self.__driver)
            self.__fetch_and_store_data()
            self.__close_driver()
            data = dict(list(self.posts_data.items())
                        [0:int(self.tweets_count)])
            return data
        except Exception as ex:
            self.__close_driver()
            logging.exception(
                "Error at method scrap : {} ".format(ex))


def json_to_csv(filename, json_data, directory):
    os.chdir(directory)  # change working directory to given directory
    # headers of the CSV file
    fieldnames = ['tweet_id', 'username', 'name', 'profile_picture', 'replies',
                  'retweets', 'likes', 'is_retweet', 'retweet_link', 'posted_time', 'content', 'hashtags', 'mentions',
                  'images', 'videos', 'tweet_url', 'link']
    mode = 'w'
    if os.path.exists("{}.csv".format(filename)):
        mode = 'a'
    # open and start writing to CSV files
    with open("{}.csv".format(filename), mode, newline='', encoding="utf-8") as data_file:
        # instantiate DictWriter for writing CSV fi
        writer = csv.DictWriter(data_file, fieldnames=fieldnames)
        if mode == 'w':
            writer.writeheader()  # write headers to CSV file
        # iterate over entire dictionary, write each posts as a row to CSV file
        for key in json_data:
            # parse post in a dictionary and write it as a single row
            row = {
                "tweet_id": key,
                "username": json_data[key]['username'],
                "name": json_data[key]['name'],
                "profile_picture": json_data[key]['profile_picture'],
                "replies": json_data[key]['replies'],
                "retweets": json_data[key]['retweets'],
                "likes": json_data[key]['likes'],
                "is_retweet": json_data[key]['is_retweet'],
                "retweet_link": json_data[key]['retweet_link'],
                "posted_time": json_data[key]['posted_time'],
                "content": json_data[key]['content'],
                "hashtags": json_data[key]['hashtags'],
                "mentions": json_data[key]['mentions'],
                "images": json_data[key]['images'],
                "videos": json_data[key]['videos'],
                "tweet_url": json_data[key]['tweet_url'],
                "link": json_data[key]['link']
            }
            writer.writerow(row)  # write row to CSV file
        data_file.close()  # after writing close the file
    logging.info('Data Successfully Saved to {}.csv'.format(filename))


def scrap_profile(twitter_username, browser="firefox", proxy=None, tweets_count=10, output_format="json", filename="", directory=os.getcwd(), headless=True, browser_profile = None):
    """
    Returns tweets data in CSV or JSON.

    Parameters:
    twitter_username(string): twitter username of the account.

    browser(string): Which browser to use for scraping?, Only 2 are supported Chrome and Firefox. Default is set to Firefox

    proxy(string): Optional parameter, if user wants to use proxy for scraping. If the proxy is authenticated proxy then the proxy format is username:password@host:port

    tweets_count(int): Number of posts to scrap. Default is 10.

    output_format(string): The output format, whether JSON or CSV. Default is JSON.

    filename(string): If output_format parameter is set to CSV, then it is necessary for filename parameter to passed. If not passed then the filename will be same as keyword passed.

    directory(string): If output_format parameter is set to CSV, then it is valid for directory parameter to be passed. If not passed then CSV file will be saved in current working directory.

    browser_profile(string): Path of Browser Profile where cookies might be located to scrap data in authenticated way.
    """
    profile_bot = Profile(twitter_username, browser,
                          proxy, tweets_count, headless, browser_profile)
    data = profile_bot.scrap()
    if output_format.lower() == "json":
        if filename == '':
          # if filename was not provided then print the JSON to console
            return json.dumps(data)
        elif filename != '':
          # if filename was provided, save it to that file
            mode = 'w'
            json_file_location = os.path.join(directory, filename+".json")
            if os.path.exists(json_file_location):
                mode = 'r'
            with open(json_file_location, mode, encoding='utf-8') as file:
                if mode == 'r':
                    try:
                        file_content = file.read()
                        content = json.loads(file_content)
                    except json.decoder.JSONDecodeError:
                        logging.warning('Invalid JSON Detected!')
                        content = {}
                    file.close()
                    data.update(content)
                    with open(json_file_location, 'w', encoding='utf-8') as file_in_write_mode:
                        json.dump(data, file_in_write_mode)
                logging.info(
                    'Data Successfully Saved to {}'.format(json_file_location))
    elif output_format.lower() == "csv":
        if filename == "":
            filename = twitter_username
        json_to_csv(filename=filename, json_data=data, directory=directory)
