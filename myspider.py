from ebooklib import epub

import scrapy
from scrapy import signals
# from scrapy.xlib.pydispatch import dispatcher
from pydispatch import dispatcher

class LightNovelSpider(scrapy.Spider):
    name = 'LightNovelSpider'
    start_urls = ['https://ln.hako.re/truyen/7307-no-game-no-life/c67073-chuong-1-l']
    base_urls = 'https://ln.hako.re'

    def __init__(self):
        self.__init_book()
        self.chapter = []

        dispatcher.connect(self._create_book, signals.spider_closed)

    def parse(self, response):
        VOL_SELECTOR = '//*[@id="mainpart"]/div/div/div[1]/div[2]/h2'
        CHAPTER_SELECTOR = '//*[@id="mainpart"]/div/div/div[1]/div[2]/h4'
        CONTENT_SELECTOR = '//*[@id="chapter-content"]'
        NEXT_PAGE_SELECTOR = '//*[@id="rd-side_icon"]/a[6]/@href'


        VOL_SELECTOR_TEXT = '//*[@id="mainpart"]/div/div/div[1]/div[2]/h2/text()'
        CHAPTER_SELECTOR_TEXT = '//*[@id="mainpart"]/div/div/div[1]/div[2]/h4/text()'

        content = response.xpath(VOL_SELECTOR).extract_first()
        content += response.xpath(CHAPTER_SELECTOR).extract_first()
        content += response.xpath(CONTENT_SELECTOR).extract_first()
        
        chapter = response.xpath(VOL_SELECTOR_TEXT).extract_first() + " " \
                    + response.xpath(CHAPTER_SELECTOR_TEXT).extract_first()
        
        print(chapter)
        self.chapter.append(self._write_chapter(chapter,content))
        
        for link in response.xpath(NEXT_PAGE_SELECTOR).extract():
            link = self.base_urls + link
            print(link)
            yield scrapy.Request(url=link, callback=self.parse)
            # response.follow(next_page, self.parse)
        
        # self._create_book()
    
    def __init_book(self):
        self.book = epub.EpubBook()
        self.book.set_identifier('No Game No Life')
        self.book.set_title('No Game No Life')
        self.book.set_language('vi')

        # set metadata
        self.book.add_author('Author')

        
    def _write_chapter(self,chapter,content):
        # create chapter
        chap = epub.EpubHtml(title='Intro', file_name=chapter + '.xhtml', lang='vi')

        chap.content= content
        
        # add chapter
        self.book.add_item(chap)
        return chap 
    
    def _create_book(self,spider):
        #TABLE OF CONTENT 
        self.book.toc = (
                        tuple(self.chapter)
                        )

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
        self.book.spine = ['nav'] + self.chapter

        # write to the file
        epub.write_epub('lightnovel.epub', self.book, {})
