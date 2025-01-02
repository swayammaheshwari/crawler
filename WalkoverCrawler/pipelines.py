# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
"""
Author : Nauman Khan Gori
date : 26/01/2023
purpose : Pipeline to store data in database. 
"""
from itemadapter import ItemAdapter
import pymongo
from scrapy.exceptions import DropItem
import datetime
from datetime import timezone
import uuid
import logging
import os
from dotenv import load_dotenv
load_dotenv()
class WalkovercrawlerPipeline:
    def __init__(self):
        connection = pymongo.MongoClient(
            os.getenv("MONGO_DB_URL"),
            27017,
        )
        self.db = connection["crawler"]
        self.collection=self.db["crawledData"]
        self.urls=self.db["urls"]
    def process_item(self, item, spider):
        """
        Process an item scraped by the spider.

        Args:
            item (dict): The scraped item to be processed.
            spider (Spider): The spider that scraped the item.

        Returns:
            dict: The processed item.

        Description:
            This function is responsible for processing an item that has been scraped by the spider.
            It takes in the scraped item and the spider object as parameters.
            The function performs the following tasks:
            1. Generates a UTC timestamp using the current time.
            2. Generates a unique identifier for the item using UUID.
            3. Logs the value of the "Texts" key in the item dictionary.
            4. Checks if the "Status" key in the item dictionary is equal to 200.
                a. If it is, the function creates a new dictionary with the following keys and values:
                    - "Texts": The value of the "Texts" key in the item dictionary.
                    - "SourceUrl": The value of the "SourceUrl" key in the item dictionary.
                    - "PageUrls": The value of the "PageUrls" key in the item dictionary.
                    - "guid": The unique identifier generated earlier.
                    - "Timestamp": The UTC timestamp generated earlier.
                b. Inserts the "PageUrls" value into the "urls" collection.
                c. Inserts the created dictionary into the "collection".
            5. If the "Status" key is not equal to 200, logs a message indicating that the item was dropped.

        Example Usage:
            item = {
                "Texts": "Lorem ipsum",
                "Status": 200,
                "SourceUrl": "https://example.com",
                "PageUrls": ["https://example.com/page1", "https://example.com/page2"]
            }
            spider = Spider()
            processed_item = process_item(item, spider)
            print(processed_item)  # Output: {
                                    #   "Texts": "Lorem ipsum",
                                    #   "SourceUrl": "https://example.com",
                                    #   "PageUrls": ["https://example.com/page1", "https://example.com/page2"],
                                    #   "guid": "e0a11685-4d9d-4714-8b3e-3e1a876f0f9f",
                                    #   "Timestamp": 1641625418.123456
                                    # }
        """
        utc_timestamp = datetime.datetime.now(timezone.utc).timestamp()
        a = {
            "Texts": item.get("Texts", "NA"),
            "SourceUrl": item.get("SourceUrl", "NA"),
            "PageUrls": item.get("PageUrls", "NA"),
            "status": item.get("Status"),
            "Timestamp": utc_timestamp,
            "jobId": item.get("jobid")
        }
        urls={"urls":item.get("PageUrls"),"status":item.get("Status"),"jobId":item.get("jobid")}
        #insert if not present in db and update if present
        if not self.urls.find_one({'urls':item.get("PageUrls")}):
            self.urls.insert_one(urls)
        if urls:
            if self.urls.find_one({'urls':item.get("PageUrls")}):
                self.urls.update_one({'urls':item.get("PageUrls")},{'$set':urls})
            else:
                self.urls.insert_one(urls)
        else: 
            logging.info("urls not available")
        if not self.collection.find_one({'PageUrls':item.get("PageUrls")}):
            self.collection.insert_one(a)
        else:
            self.collection.update_one({'PageUrls':item.get("PageUrls")},{'$set':a})

        if item.get("Status")==200:
            logging.info("Item not dropped bze status code is 200: ", item)
        else:
           logging.info("Item dropped bze status code is not 200: ", item)
            
        return 
