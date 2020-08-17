import os.path
import PySimpleGUI as sg
from requests import get
from os import remove
from os.path  import basename
from bs4 import BeautifulSoup
from PIL import ImageTk, Image
from tkinter import Tk, Canvas

import scrapy
import argparse

from scrapy.crawler import CrawlerProcess
from GetLightNovelSpider import GetLightNovelSpider

import re


# ----- Full layout -----
layout = [
    [sg.Text("Link"),sg.In(size = (32,1),enable_events=True, key="-LINK-"),sg.Button("OK")],
    [sg.Text(size=(40, 1), key="-NAME-")],
    [sg.Text(size=(40, 1), key="-AUTHOR-")],
    [sg.Image(key="-IMAGE-")],
    [sg.Button("DOWNLOAD")],
]

window = sg.Window("Light Novel Crawler", layout, element_justification = 'c')

while True:
    event, values = window.read()

    if event == "Exit" or event == sg.WIN_CLOSED:
        try: 
            remove('temp.png')
            remove(basename(image_url))
        except: 
            pass 

        break

    if event == "OK":
        url = values["-LINK-"]

        response = get(url)
        html_soup = BeautifulSoup(response.text, 'html.parser')
        AUTHOR_SELECTOR  = 'div.series-information span.info-value a'
        NAME_SELECTOR  = 'div.series-name-group span a'
        IMAGE_SELECTOR  = 'div.left-column.col-12.col-md-3 div div.a6-ratio div'
        r = r"url\('(.*)'\)"

        name =  "Name :" + html_soup.select(NAME_SELECTOR)[0].text
        author = "Author :" + html_soup.select(AUTHOR_SELECTOR)[0].text
        image_url = re.findall(r,html_soup.select(IMAGE_SELECTOR)[0].attrs['style'])[0]

        with open(basename(image_url), "wb") as f:
            f.write(get(image_url).content)

        window["-NAME-"].update(name)
        window["-AUTHOR-"].update(author)
        im = Image.open(basename(image_url))
        im.save('temp.png')
        window["-IMAGE-"].update(filename='temp.png')

    elif event == "DOWNLOAD":  
        process = CrawlerProcess()
        process.crawl(GetLightNovelSpider, 
                    start_url = url,
                    author = author,
                    name = name)
        process.start()
        process.stop()

