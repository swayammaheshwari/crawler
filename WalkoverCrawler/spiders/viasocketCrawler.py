"""
Author : Nauman Khan Gori
date : 21/12/2023
purpose : viasocket plugin crawler- main crawler file where request to urls and extraction of imp information is happening
"""
from pathlib import Path
from urllib.parse import urlparse
import scrapy
from bs4 import BeautifulSoup
from scrapy.exceptions import CloseSpider
from WalkoverCrawler.items import WalkovercrawlerItem
from scrapy import signals
import logging
import http.client
import json
import os
from dotenv import load_dotenv
from .webhook import WebhookCall
load_dotenv()
from scrapy_selenium_custom import SeleniumRequest
from shutil import which
from scrapy.linkextractors import LinkExtractor
from urllib.parse import urlparse
from scrapy.exceptions import CloseSpider

class ViasocketcrawlerSpider(scrapy.Spider):
    name = "viasocketCrawler"
    allowed_domains=[]
    source_url=""
    def __init__(self, urls="",Isfirst="False",fetchData="False",jobId="",**kwargs):
        self.jobid = kwargs.pop("_job")
        super(ViasocketcrawlerSpider, self).__init__(**kwargs)
        self.start_urls = urls  #urls are the array of urls
        self.Isfirst=Isfirst.lower()=="true"
        self.fetchData=fetchData.lower()=="true"
        self.base_url = urlparse(urls).netloc
        self.allowed_domains.append(self.base_url)
        self.JOBID=jobId
    def start_requests(self):
        """
        Generate a sequence of requests to start crawling.

        This function is a generator that yields `scrapy.Request` objects to start the crawling process. 
        If `self.Isfirst` is `True`, it yields a request with the URL `self.start_urls` and the callback method `self.parseForUrls`. 
        Otherwise, it yields a request with the URL `self.start_urls` and the callback method `self.parse`. 

        Returns:
            A generator object that yields `scrapy.Request` objects.
        """
        if self.fetchData:
            raise CloseSpider('Condition met, closing spider')
        else:
            self.source_url=self.start_urls 
            yield SeleniumRequest(url=self.start_urls , callback=self.parse)
        self.crawler.signals.connect(self.spider_close, signal=signals.spider_idle)
    def spider_close(self, spider):
        """
        Close the spider.

        Parameters:
            spider (Spider): The spider instance to close.

        Raises:
            CloseSpider: If the spider needs to be forcefully closed.

        Returns:
            None
        """
        logging.info("spider closed!")
        # self.call.call(1)    

    def parse(self, response):
        """
        Parse the response and extract relevant information.

        Args:
            response (object): The response object containing the data to be parsed.

        Returns:
            item (object): A dictionary containing the extracted information.
        """

        chunks=[]
        currentChunk=[]
        flag=1
        for element in response.xpath("//body//*[not(self::header) and not(self::footer) and not(self::nav) and not(self::script)  and not(self::style) and not(self::chat-widget) and not(ancestor::div[contains(@class, 'sidebar')])  and not(*)]"):
            tagName= element.xpath("name()").get()
            extractedText=element.xpath("normalize-space(string())").get()
            extractedId=element.xpath("@id").get()
            extractedclass=element.xpath("@class").get()
            if extractedText:
                if not currentChunk or (currentChunk[-1][0]!=tagName):
                    currentChunk.append((tagName, extractedText.strip()))
                else:
                    currentChunk[-1] = (tagName, currentChunk[-1][1] + '\n' + extractedText.strip())
                    # flag=0
        # # print("parse: ", txt)
        for _, text in currentChunk:
            chunks.append(text)
        txt=""
        for chunk in chunks:
            txt+=chunk
            txt+="\n"
        logging.info("final txt: ==> "+txt)
        item = WalkovercrawlerItem()
        item["Texts"] = txt
        item["SourceUrl"] = self.source_url
        item["PageUrls"] = response.url
        item["Isurl"] = False
        item["Status"]=response.status
        item["jobid"]=self.jobid
        yield item
