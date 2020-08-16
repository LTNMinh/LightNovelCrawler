from ebooklib import epub

import scrapy
from scrapy import signals
from pydispatch import dispatcher

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
        self.author  = author if author else "Author"
        self.name    = name if name else "Light Novel"
        self.temp_chapter = []
        self.all_chapter  = []
        self.toc     = {}

        print("_____________________________________",self.name)
        print("_____________________________________",self.author) 
        self.__init_book()
        dispatcher.connect(self._create_book, signals.spider_closed)


    def start_requests(self):
        yield scrapy.Request(self.start_url,
                                callback = self.parse)

    def parse(self, response):
        VOL_SELECTOR  = '.volume-mobile .sect-title::text'
        CHAPTER_LINK_SELECTOR = '.col-md-10 a::attr(href)'
        # CHAPTER_NAME_SELECTOR = '.col-md-10 a::text'

        vols     = response.css(VOL_SELECTOR).extract()
        links    = response.css(CHAPTER_LINK_SELECTOR).extract()
        # chapters =  response.css(CHAPTER_NAME_SELECTOR).extract()

        for link in links:
            link = self.base_urls + link
            yield scrapy.Request(url=link, callback=self.parse_chapter)
            
            # print("Chapter:",self.temp_chapter)
            # temp = (epub.Section(v),tuple(self.temp_chapter))
            # self.toc.append(temp)
            # print("TOC", self.toc)
            # self.temp_chapter = []

    def parse_chapter(self,response):
        VOL_SELECTOR = '//*[@id="mainpart"]/div/div/div[1]/div[2]/h2'
        CHAPTER_SELECTOR = '//*[@id="mainpart"]/div/div/div[1]/div[2]/h4'
        CONTENT_SELECTOR = '//*[@id="chapter-content"]'


        VOL_SELECTOR_TEXT = '//*[@id="mainpart"]/div/div/div[1]/div[2]/h2/text()'
        CHAPTER_SELECTOR_TEXT = '//*[@id="mainpart"]/div/div/div[1]/div[2]/h4/text()'

        content = response.xpath(VOL_SELECTOR).extract_first()
        content += response.xpath(CHAPTER_SELECTOR).extract_first()
        content += response.xpath(CONTENT_SELECTOR).extract_first()

        vol     = response.xpath(VOL_SELECTOR_TEXT).extract_first()
        chapter = response.xpath(CHAPTER_SELECTOR_TEXT).extract_first()
                    #response.xpath(VOL_SELECTOR_TEXT).extract_first() + " " \
                    #+ response.xpath(CHAPTER_SELECTOR_TEXT).extract_first()

        c = self._write_chapter(chapter,content)
        if  self.toc.get(vol):
            self.toc[vol].append(c)  
        else: 
            self.toc[vol] = [c]

        self.all_chapter.append(c)
        
    
    def __init_book(self):
        """
        [Init epub writer]
        """
        self.book = epub.EpubBook()
        self.book.set_identifier(self.name)
        self.book.set_title(self.name)
        self.book.set_language('vi')
        self.book.set_cover("temp.png", open('temp.png', 'rb').read())

        # set metadata
        self.book.add_author(self.author)
        

    def _write_chapter(self,chapter,content):
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
        
        # add chapter
        self.book.add_item(chap)
        return chap 
    
    def _create_book(self,spider):
        print("_____________________________________",self.author) 
        #TABLE OF CONTENT 
        self.toc = [ (epub.Section(i),tuple(z)) for i,z in zip(self.toc.keys(),
                                                            self.toc.values())]
        print(self.toc)
        self.book.toc = (
                        tuple(self.toc)
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
        self.book.spine = ['nav'] + self.all_chapter
        print(self.all_chapter)
        # write to the file
        epub.write_epub(self.name + '.epub', self.book, {})

        print("_____________________________________",self.name + '.epub') 