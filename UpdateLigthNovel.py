import ebooklib

import os 
from os.path  import basename
from ebooklib import epub

from collections import OrderedDict
import itertools

import re 
from requests import get
from bs4 import BeautifulSoup

import time 
import glob

from ultis import print_progress

class UpdateLightNovel():
    base_urls = 'https://ln.hako.re'
    time_sleep = 2

    def __init__(self,file,url = None):

        # self.name = name[6:]
        self.file = file 
        
        self.book = epub.read_epub(self.file)        
        if url: 
            self.url = url  
            self.book.add_metadata(None, 'meta', '', {'name': 'website', 
                                    'content': self.url,
                                    })
        else:
            self.url = self.book.get_metadata('OPF', 'website')[0][1]['content'] 

        response = get(self.url)
        self.html_soup = BeautifulSoup(response.text, 'html.parser')

        self.toc = self._get_toc()
        self.book_default_css = list(self.book.get_items_of_type(ebooklib.ITEM_STYLE))[0]
        self.all_chapter      = list(self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT))[1:-1]
        
    def update(self):
        VOL_SELECTOR = 'h2.title-item'
        CHAP_SELECTOR = 'h4.title-item'
        CONTENT_SELECTOR = '#chapter-content'

        not_in_chapter = list(self._not_in_chapter())
        total = len(not_in_chapter)
        index = 0 

        for loc,link in not_in_chapter:
            url = self.base_urls + link 
            response = get(url)
            print("Crawl at url ({}):{} ".format(response.status_code,url))
            html_soup = BeautifulSoup(response.text, 'html.parser') 

            content = str(html_soup.select(VOL_SELECTOR)[0])
            content += str(html_soup.select(CHAP_SELECTOR)[0])
            content += str(html_soup.select(CONTENT_SELECTOR)[0])
            
            vol = html_soup.select(VOL_SELECTOR)[0].text 
            chapter = html_soup.select(CHAP_SELECTOR)[0].text

            # Download Image 
            html_soup =  BeautifulSoup(content, 'html.parser')
            image_name = []
            for image_url in html_soup.select('img'):
                image_url = image_url.attrs['src']
                with open(basename(image_url), "wb") as f:
                    f.write(get(image_url).content)
                image_name.append(basename(image_url))
            
            # Parse Image
            regex   = re.compile(r'src="[\w:/.-]*\/([\w.-]*)"')
            content = regex.sub('src="\g<1>"',content)
            
            c = self._write_chapter(chapter,content,image_name)

            if  self.toc.get(vol):
                self.toc[vol].append(c)  
            else: 
                self.toc[vol] = [c]

            self.all_chapter.insert(loc,c)
            print_progress(index,total)
            index += 1 
            time.sleep(self.time_sleep)

        self._create_book()
        print("Update Done")

    def _get_toc(self):
        toc = OrderedDict()
        for key,item in self.book.toc:
            toc[key.title] = item
        return toc 
    
    def _not_in_chapter(self):
        CHAPTER_SELECTOR = '.chapter-name a'

        regex = re.compile(r'(\r\n|\r|\n)')

        chapters = {}
        for c in self.html_soup.select(CHAPTER_SELECTOR):
            c_name  = c.text
            c_hrefs = c['href']
            content = regex.sub('',c_name)
            chapters[c_name] = c_hrefs

        chapter = self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT)
        already = [ c.get_name()[:-6] for c in chapter ]

        not_in = [ (i,c) for i,c in enumerate(chapters) if c not in already]

        for loc,n in not_in: 
            yield loc,chapters[n]
    
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
    
    def _create_book(self):
        #TABLE OF CONTENT 
        self.toc = [(epub.Section(i),tuple(z)) for i,z in zip(self.toc.keys(),
                                                            self.toc.values())]
        self.book.toc = (
                        tuple(self.toc)
                        )

        # basic spine
        self.book.spine = ['nav'] + self.all_chapter
        
        # write to the file
        epub.write_epub(self.file, self.book, {})

        for f in glob.glob(r"*.jpg"):
            os.remove(f)

        for f in glob.glob(r"*.png"):
            os.remove(f)