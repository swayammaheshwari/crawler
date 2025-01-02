"""
Author : Nauman Khan Gori
date : 26/01/2023
purpose : WalkoverCrawler- main crawler file where request to urls and extraction of imp information is happening
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
exclusions = [
    "[contains(@class,'app-sidebar-galaxy')]", 
    "self::nav", 
    "self::footer", 
    "self::header", 
    "self::aside",
    "self::script", 
    "self::style", 
    "self::noscript", 
    "self::svg", 
    "[@role='alert']", 
    "[@role='banner']", 
    "[@role='dialog']", 
    "[@role='alertdialog']",
    "[@role='region'][contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'skip')]", 
    "[@aria-modal='true']",
    "contains(@class, 'folder')",
    "[contains(@class, 'sidebar')"
]


class Crawler(scrapy.Spider):
    name = "Crawler"
    allowed_domains=[]
    source_url=""
    def __init__(self, urls="",Isfirst="False",companyId="",botId="",**kwargs):
        self.jobid = kwargs.pop("_job")
        urls=json.loads(urls)
        super(Crawler, self).__init__(**kwargs)
        self.start_urls = urls  #urls are the array of urls
        self.Isfirst=Isfirst.lower()=="true"
        self.base_url = urlparse(urls[0]).netloc
        self.allowed_domains.append(self.base_url)
        self.call=WebhookCall(self.jobid,self.start_urls,companyId,botId)
        self.call.call(0)
    def start_requests(self):
        """
        Generate a sequence of requests to start crawling.

        This function is a generator that yields `scrapy.Request` objects to start the crawling process. 
        If `self.Isfirst` is `True`, it yields a request with the URL `self.start_urls` and the callback method `self.parseForUrls`. 
        Otherwise, it yields a request with the URL `self.start_urls` and the callback method `self.parse`. 

        Returns:
            A generator object that yields `scrapy.Request` objects.
        """
        if self.Isfirst:
          for url in self.start_urls:
                self.source_url=url
                yield SeleniumRequest(url=url, callback=self.parseForUrls)  
        else:
           for url in self.start_urls:
                self.source_url=url
                yield SeleniumRequest(url=url, callback=self.parse)
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
        self.call.call(1)

        
        
    def parseForUrls(self, response):
        """
        Parses the response body for URLs and extracts relevant information.

        Parameters:
        - response: the response object containing the HTML body

        Returns:
        - A generator that yields WalkovercrawlerItem objects containing the extracted information
        """
        # chunks=[]
        
        extractedText = ""
        exclusion_xpath = " or ".join(exclusions)
        correct_xpath = "//body//*[not(self::nav or self::footer or self::header or self::aside or self::script or self::style or self::noscript or self::svg or @role='alert' or @role='banner' or @role='dialog' or @role='alertdialog' or contains(@aria-label, 'skip') and @role='region' or @aria-modal='true' or contains(@class, 'app-sidebar-galaxy') or contains(@class, 'folder') or contains(@class, 'sidebar')) and not(ancestor::*[ self::nav or self::footer or self::header or self::aside or self::script or self::style or self::noscript or self::svg or @role='alert' or @role='banner' or @role='dialog' or @role='alertdialog' or contains(@aria-label, 'skip') and @role='region' or @aria-modal='true' or contains(@class, 'app-sidebar-galaxy') or contains(@class, 'folder') or contains(@class, 'sidebar')])]"

        for element in response.xpath(correct_xpath):
            # Only add text if the element does not contain child elements with text
            if not element.xpath('.//*[normalize-space(text())]'):
                text = element.xpath("normalize-space(string())").get()
                if text:  # Ensure text is not empty
                    extractedText += text + "\n"
        #     extractedId=element.xpath("@id").get()
        #     extractedclass=element.xpath("@class").get()
        #     if extractedText:
        #         if not currentChunk or (currentChunk[-1][0]!=tagName):
        #             currentChunk.append((tagName, extractedText.strip()))
        #         else:
        #             currentChunk[-1] = (tagName, currentChunk[-1][1] + '\n' + extractedText.strip())
        #             # flag=0
        # # # print("parse: ", txt)
        # for _, text in currentChunk:
        #     chunks.append(text)
        # txt=""
        # for chunk in chunks:
        #     txt+=chunk
        #     txt+="\n"+"-"*80+"\n"
        # logging.info("final txt: ==> "+txt)
        item = WalkovercrawlerItem()
        item["Texts"] = extractedText.strip()
        item["SourceUrl"] = self.source_url
        item["PageUrls"] = response.url
        item["Isurl"] = False
        item["Status"]=response.status
        item["jobid"]=self.jobid
        yield item
        
        linksExtractor=LinkExtractor(allow_domains=self.allowed_domains)
        links=linksExtractor.extract_links(response)

        for link in links:
            logging.info(link.url)
            yield SeleniumRequest(url=link.url, callback=self.parse,script="")
        

        

    def parse(self, response):
        """
        Parse the response and extract relevant information.

        Args:
            response (object): The response object containing the data to be parsed.

        Returns:
            item (object): A dictionary containing the extracted information.
        """
        # extractedText=" ".join(response.xpath("//body//text()").get())
        # chunks=[]
        # currentChunk=[]
        extractedText = ""
        exclusion_xpath = " or ".join(exclusions)
        correct_xpath = "//body//*[not(self::nav or self::footer or self::header or self::aside or self::script or self::style or self::noscript or self::svg or @role='alert' or @role='banner' or @role='dialog' or @role='alertdialog' or contains(@aria-label, 'skip') and @role='region' or @aria-modal='true' or contains(@class, 'app-sidebar-galaxy') or contains(@class, 'folder') or contains(@class, 'sidebar')) and not(ancestor::*[ self::nav or self::footer or self::header or self::aside or self::script or self::style or self::noscript or self::svg or @role='alert' or @role='banner' or @role='dialog' or @role='alertdialog' or contains(@aria-label, 'skip') and @role='region' or @aria-modal='true' or contains(@class, 'app-sidebar-galaxy') or contains(@class, 'folder') or contains(@class, 'sidebar')])]"

        for element in response.xpath(correct_xpath):
            # Only add text if the element does not contain child elements with text
            if not element.xpath('.//*[normalize-space(text())]'):
                text = element.xpath("normalize-space(string())").get()
                if text:  # Ensure text is not empty
                    extractedText += text + "\n"

            # extractedId=element.xpath("@id").get()
            # extractedclass=element.xpath("@class").get()
            
            # logging.info("cccc",extractedclass)
            # logging.info("ccc"+extractedId)
            # logging.info("ccc"+extractedText)
            
            # if extractedText:
            #     # if not currentChunk or (currentChunk[-1][0]!=tagName):
            #         currentChunk.append(extractedText.strip())
                # else:
                    # currentChunk[-1] = (tagName, currentChunk[-1][1] + '\n' + extractedText.strip())
                    # flag=0
        # # print("parse: ", txt)
        # for _, text in currentChunk:
        #     chunks.append(text)
        # txt=""
        # for chunk in chunks:
        #     txt+=chunk
        #     txt+="\n"+"-"*80+"\n"
        # logging.info("final txt: ==> "+txt)
        item = WalkovercrawlerItem()
        item["Texts"] = extractedText
        item["SourceUrl"] = self.source_url
        item["PageUrls"] = response.url
        item["Isurl"] = False
        item["Status"]=response.status
        item["jobid"]=self.jobid
        yield item