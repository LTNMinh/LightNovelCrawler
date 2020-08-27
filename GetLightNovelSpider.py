from ebooklib import epub

import scrapy
from scrapy import signals

import os 
from os.path  import basename
from requests import get
from bs4 import BeautifulSoup
from pydispatch import dispatcher

import re
import glob


class GetLightNovelSpider(scrapy.Spider):
    name = 'GetLightNovelSpider'
    base_urls = 'https://ln.hako.re'

    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'USER_AGENT' : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36',
    }

    def __init__(self,start_url,author,name):
        """[Init Spider]

        Args:
            start_url ([string]): [URL of first chapter]
        """
        
        self.start_url = start_url
        self.author  = author[8:] if author else "Author"
        self.name    = name[6:] if name else "Light Novel"
        self.temp_chapter = []
        self.all_chapter  = []
        self.toc     = {}

        self.__init_book()
        dispatcher.connect(self._create_book, signals.spider_closed)


    def start_requests(self):
        yield scrapy.Request(self.start_url,
                                callback = self.parse)

    def parse(self, response):
        CHAPTER_LINK_SELECTOR = '.col-md-10 a::attr(href)'
        link = response.css(CHAPTER_LINK_SELECTOR).extract_first()
        link = self.base_urls + link
        yield scrapy.Request(url=link, callback=self.parse_chapter)

    def parse_chapter(self,response):
        VOL_SELECTOR = '//*[@id="mainpart"]/div/div/div[1]/div[2]/h2'
        CHAPTER_SELECTOR = '//*[@id="mainpart"]/div/div/div[1]/div[2]/h4'
        CONTENT_SELECTOR = '//*[@id="chapter-content"]'

        NEXT_PAGE_SELECTOR = '//*[@id="rd-side_icon"]/a[6]/@href'
        VOL_SELECTOR_TEXT = '//*[@id="mainpart"]/div/div/div[1]/div[2]/h2/text()'
        CHAPTER_SELECTOR_TEXT = '//*[@id="mainpart"]/div/div/div[1]/div[2]/h4/text()'

        content = response.xpath(VOL_SELECTOR).extract_first()
        content += response.xpath(CHAPTER_SELECTOR).extract_first()
        content += response.xpath(CONTENT_SELECTOR).extract_first()

        vol     = response.xpath(VOL_SELECTOR_TEXT).extract_first()
        chapter = response.xpath(CHAPTER_SELECTOR_TEXT).extract_first()

        # Download Image 
        html_soup =  BeautifulSoup(content, 'html.parser')
        image_name = []
        for image_url in html_soup.select('img'):
            image_url = image_url.attrs['src']
            with open(basename(image_url), "wb") as f:
                f.write(get(image_url).content)
            image_name.append(basename(image_url))
        
        # Parse Image
        regex = re.compile(r'src="[\w:/.-]*\/([\w.-]*)"')
        content = regex.sub('src="\g<1>"',content)

        c = self._write_chapter(chapter,content,image_name)
        if  self.toc.get(vol):
            self.toc[vol].append(c)  
        else: 
            self.toc[vol] = [c]

        self.all_chapter.append(c)

        link = response.xpath(NEXT_PAGE_SELECTOR).extract_first()
        if link:
            link = self.base_urls + link
            yield scrapy.Request(url=link, callback=self.parse_chapter)
        
    def __init_book(self):
        """
        [Init epub writer]
        """
        self.book = epub.EpubBook()
        self.book.set_identifier(self.name)
        self.book.set_title(self.name)
        self.book.set_language('vi')
        self.book.set_cover("temp.png", open('temp.png', 'rb').read())
        self.book.add_author(self.author)

        # defube style
        style = '''
        p {
            margin-top: 0.0em;
            margin-bottom: 0.3em;
            text-indent: 1.3em;
        }
        '''

        self.book_default_css = epub.EpubItem(uid="style_default", 
                                    file_name="style/default.css", 
                                    media_type="text/css", content=style)
        
        self.book.add_item(self.book_default_css)

    def _write_chapter(self,chapter,content,image_name):
        """
        Write Chapter 

        Args:
            chapter (string): [Name of chapter]
            content (string): [Content of chapter]

        Returns:
            [epub.EpubHtml]: [Chapter of book]
        """

        # create chapter
        chap = epub.EpubHtml(title=chapter, 
                            file_name=chapter + '.xhtml', 
                            lang='vi')

        chap.content= content
        chap.add_item(self.book_default_css)
        # add chapter
        self.book.add_item(chap)
        # add image 
        for iname in image_name:
            image_item = epub.EpubItem(file_name = iname, 
                        content=open(iname, 'rb').read(),)
            self.book.add_item(image_item)
        
        
        return chap 
    
    def _create_book(self,spider):
        #TABLE OF CONTENT 
        self.toc = [(epub.Section(i),tuple(z)) for i,z in zip(self.toc.keys(),
                                                            self.toc.values())]
        self.book.toc = (
                        tuple(self.toc)
                        )

        # self.book.toc = (
        #                 tuple(self.all_chapter)
        #                 )

        # add default NCX and Nav file
        self.book.add_item(epub.EpubNcx())
        self.book.add_item(epub.EpubNav())

        # define CSS style
        style = 'BODY {color: white;}'
        nav_css = epub.EpubItem(uid="style_nav", 
                                file_name="style/nav.css", 
                                media_type="text/css", 
                                content=style)

        # add CSS file
        self.book.add_item(nav_css)

        # basic spine
        self.book.spine = ['nav'] + self.all_chapter
        # write to the file
        epub.write_epub(str(self.name) + '.epub', self.book, {})

        for f in glob.glob(r"*.jpg"):
            os.remove(f)

        for f in glob.glob(r"*.png"):
            os.remove(f)