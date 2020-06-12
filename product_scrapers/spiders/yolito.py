# -*- coding: utf-8 -*-
from scrapy import Spider, Request, FormRequest


class YolitoSpider(Spider):
    name = 'yolito'
    allowed_domains = ['yolito.cl', 'x-rates.com']
    start_urls = ['http://yolito.cl/']

    headers = {
        'Host': 'www.yolito.cl',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,ru-RU;q=0.8,ru;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Upgrade-Insecure-Requests': '1',
    }

    def start_requests(self):
        yield Request(self.start_urls[0], headers=self.headers)

    def parse(self, response):
        cat_urls = response.xpath('//div[@class="desktopMenu"]//a/@href').extract()
        for url in cat_urls:
            yield Request(response.urljoin(url), headers=self.headers)
        
        prod_urls = response.xpath('//a[@class="item"]/@href').extract()
        for url in prod_urls:
            yield Request(response.urljoin(url), callback=self.parse_product, headers=self.headers)
        
        next_page = response.xpath('//link[@rel="next"]/@href').extract_first()
        if next_page:
            yield Request(response.urljoin(next_page), headers=self.headers)
    
    def parse_product(self, response):
        stock = response.xpath('//link[@itemprop="availability"]/@href').extract_first()
        if 'InStock' not in stock:
            return

        name = response.xpath('//div[@itemprop="name"]/h1/text()').extract_first()
        sku = response.xpath('//span[@itemprop="sku"]/text()').extract_first()
        image = response.xpath('//meta[@property="og:image"]/@content').extract_first()
        manufacturer = response.xpath('//div[@itemprop="brand"]/text()').extract_first()
        price = response.xpath('//span[@itemprop="price"]/@content').extract_first()
        images = response.xpath('//img[@onclick="changePhoto(this)"]/@src').extract()[1:]
        category = ' > '.join(response.xpath('//ul[@class="breadcrumb"]//a/span/text()').extract()[1:])
        description = response.xpath('//div[@class="descripcionProductoContainer"]/text()').extract_first()
        description = description.strip() if description else ''
        attributes_names = response.xpath('//div[@class="fichaTecnicaContainer"]//div[@class="general-text"]/div[@class="atributo"]/text()').extract()
        attributes_names = [elem.strip() for elem in attributes_names]
        attributes_values = response.xpath('//div[@class="fichaTecnicaContainer"]//div[@class="general-text"]/div[@class="texto"]/text()').extract()
        attributes_values = [elem.strip() for elem in attributes_values]
        attributes = dict(zip(attributes_names, attributes_values))

        # Price rules
        if price < 50:
            price = price * 0.25
        elif 50 <= price < 150:
            price = price * 0.2
        elif 150 <= price < 300:
            price = price * 0.15
        else:
            price = price * 0.1

        item = {
            'name': name,
            'sku': sku,
            'image': image,
            'manufacturer': manufacturer,
            'price': price,
            'images': images,
            'category': category,
            'description': description,
            'attributes': attributes,
            'url': response.url
        }

        stock_url = 'https://www.yolito.cl/Home/GetStockAllDepots'
        formdata = {'barcode': sku}
        stock_hdr = {
            'Host': 'www.yolito.cl',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0',
            'Accept-Language': 'en-US,ru-RU;q=0.8,ru;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://www.yolito.cl',
            'Connection': 'keep-alive'
        }

        yield FormRequest(stock_url, formdata=formdata, headers=stock_hdr, callback=self.parse_stock, meta={'item': item})
    
    def parse_stock(self, response):
        item = response.meta['item']
        item['stock'] = response.text
        yield item



