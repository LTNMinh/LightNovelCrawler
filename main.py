import scrapy
import argparse

from scrapy.crawler import CrawlerProcess
from LightNovelSpider import LightNovelSpider


import PySimpleGUI as sg


parser = argparse.ArgumentParser(description='Light Novel Crawler from ln.hake.re')

parser.add_argument("url",
                    action = 'store',
                    help='Start url of lightnovel')

parser.add_argument('-a', 
                    '--author',
                    dest='author',
                    action = 'store',
                    default=False,
                    help='Name of Author')

parser.add_argument('-n', 
                    '--name',
                    dest='name',
                    action = 'store',
                    default=False,
                    help='Name of LN')


if __name__ == "__main__":
    args = parser.parse_args()

    process = CrawlerProcess()
    process.crawl(LightNovelSpider, 
                    start_url = args.url, 
                    author = args.author,
                    name = args.name)
    process.start()