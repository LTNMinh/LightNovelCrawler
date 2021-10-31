from gooey import Gooey
from argparse import ArgumentParser
from gooey import GooeyParser

from requests import get
from bs4 import BeautifulSoup
from PIL import ImageTk, Image
from tkinter import Tk, Canvas

import os 
from os.path  import basename
from ebooklib import epub

import scrapy
from scrapy.crawler      import CrawlerProcess
from GetLightNovelSpider import GetLightNovelSpider
from UpdateLigthNovel    import UpdateLightNovel

import re
import glob


def crawl_light_novel(url):
    response = get(url)
    html_soup = BeautifulSoup(response.text, 'html.parser')
    AUTHOR_SELECTOR = 'div.series-information span.info-value a'
    NAME_SELECTOR   = 'div.series-name-group span a'
    IMAGE_SELECTOR  = 'div.left-column.col-12.col-md-3 div div.a6-ratio div'
    r = r"url\('(.*)'\)"

    name =  "Name :" + html_soup.select(NAME_SELECTOR)[0].text
    author = "Author :" + html_soup.select(AUTHOR_SELECTOR)[0].text
    image_url = re.findall(r,html_soup.select(IMAGE_SELECTOR)[0].attrs['style'])[0]

    with open(basename(image_url), "wb") as f:
        f.write(get(image_url).content)
    
    im = Image.open(basename(image_url))
    im.save('temp.png')

    process = CrawlerProcess()
    process.crawl(GetLightNovelSpider, 
                start_url = url,
                author = author,
                name = name,
                html_soup = html_soup)
    process.start()
    process.stop()
    

def update_light_novel(file,url):
    spider = UpdateLightNovel(file,url)
    spider.update()
    

def run(args):
    if args.command == "crawl":
        crawl_light_novel(args.input_link)
    elif args.command == "update":
        if args.use_internal_url:
            update_light_novel(args.input_file,None)
        else: 
            update_light_novel(args.input_file,args.external_url)


@Gooey(
    program_name="Light Novel Crawler",
    program_description= "Crawl content of light novel on website https://ln.hako.re/ an convert to epub format.",
    default_size=(600, 600),
    navigation="TABBED",
    progress_regex=r"^Progress (\d+)%$",
)
def main():
    parser = GooeyParser()
    
    subs = parser.add_subparsers(help="commands", dest="command")

    crawl  = subs.add_parser( "crawl", 
                            prog="Crawl New Lightnovel").add_argument_group("")
    crawl.add_argument(
        "-i",
        "--input_link", 
        required=True,
        help="Link of Light Novel",
        gooey_options=dict(fullwidth = True),
    )

    # crawl.add_argument(
    #     "-o",
    #     "--output_file", 
    #     required=True,
    #     help="Save file location",
    #     widget="FileSaver",
    #     gooey_options=dict(wildcard="EPUB (.epub)|*.epub",fullwidth = True)
    # )

    update_group = subs.add_parser( "update", 
                            prog="Update Lightnovel")
    update  = update_group.add_argument_group("")
    update.add_argument(
        "-i",
        "--input_file", 
        required=True,
        help="File of Light Novel",
        widget="FileChooser",
        gooey_options=dict(
            wildcard="Epub files (*.epub)|*.epub", full_width=True,
        )
    )

    url_settings = update_group.add_argument_group("URL")

    url_group = url_settings.add_mutually_exclusive_group(
        required=True,
        gooey_options=dict(title="", full_width=True,),
    )

    url_group.add_argument(
        "--use_internal_url", metavar="Use the internal URL", action="store_true"
    )

    url_group.add_argument(
        "--external_url",
        metavar="Use the external URL",
        help="Link of the update LightNovel",
        widget="TextField",
    )

    args = parser.parse_args()
    run(args)

if __name__ == "__main__":
    main()