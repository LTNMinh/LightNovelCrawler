import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy import signals

import os 
import os.path
from os import remove
from os.path  import basename

from requests import get
from bs4 import BeautifulSoup
from pydispatch import dispatcher

import re
import glob

from PIL import ImageTk, Image
from tkinter import Tk, Canvas

import PySimpleGUI as sg


from GetLightNovelSpider import GetLightNovelSpider
from UpdateLigthNovel import UpdateLightNovel

import itertools
import ebooklib
from ebooklib import epub
import time

