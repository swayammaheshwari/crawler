# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
"""
Author : Nauman Khan Gori
date : 26/01/2023
purpose : items file to store the scraped data
"""

from scrapy.item import Field,Item
class WalkovercrawlerItem(Item):
    # define the fields for your item here like:
    Texts= Field()
    SourceUrl=Field()
    PageUrls=Field()
    Isurl=Field()
    Status=Field()
    jobid=Field()
    pass
