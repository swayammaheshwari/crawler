"""
Author : Nauman Khan Gori
date : 26/01/2023
purpose : webhook- Sending the data to the webhook as the crawling completed from fetching urls through the mongodb.
"""
import os
import http.client
import pymongo
import json
import logging
from bson.json_util import dumps

class WebhookCall():
    def __init__(self,jobid,url,companyId,botId):
        connection = pymongo.MongoClient(
            os.getenv("MONGO_DB_URL"),
            27017,
        )
        self.db = connection["crawler"]
        self.collection=self.db["crawledData"]
        self.urlsCollection=self.db["urls"]
        self.jobid=jobid
        self.url=url
        self.companyId=companyId
        self.botId=botId
    def call(self,status):
        """
        Sends a POST request to the specified webhook endpoint with the provided data.

        Parameters:
            None

        Returns:
            None
        """
        # data=self.getData()
        body={"job_id":self.jobid,"url":self.url,"company_id":self.companyId,"bot_id":self.botId,"status":status}     
        logging.info(body)
        logging.info(f'endpoint:{os.getenv("WEBHOOK_DOMAIN")}{os.getenv("WEBHOOK_ENDPOINT")}')
        conn = http.client.HTTPConnection(os.getenv("WEBHOOK_DOMAIN"))
        payload = json.dumps(body)
        headers = {
        'Content-Type': 'application/json'
        }
        conn.request("POST", os.getenv("WEBHOOK_ENDPOINT"), payload, headers)
        res = conn.getresponse()
        logging.info("res: {}".format(res))
        logging.info("Status: {}".format(res.status))
        return 

    def getData(self):
        """
        Retrieve data from the database for a given job ID.

        Returns:
            dict: A dictionary containing the crawled data and URL data for the specified job ID.
        """
        CrawlData=list(self.collection.find({"jobId":self.jobid}))
        UrlData=list(self.urlsCollection.find({"jobId":self.jobid}))
        return {"CrawlData":dumps(CrawlData),"UrlData":dumps(UrlData)}

    
    
   
