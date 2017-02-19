# -*- coding: utf-8 -*-
"""
    ondemandkorea.com

    /includes/latest.php?cat=<name>
    /includes/episode_page.php?cat=<name>&id=<num>&page=<num>
"""
import urllib, urllib2
import re
import json
from bs4 import BeautifulSoup
from xbmcswift2 import Plugin
import xml.etree.ElementTree as etree

root_url = "http://www.ondemandkorea.com"
img_base = "http://max.ondemandkorea.com/includes/timthumb.php?w=175&h=100&src="
default_UA = "Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)"
tablet_UA = "Mozilla/5.0 (Linux; Android 4.0.4; Galaxy Nexus Build/IMM76B) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.133 Safari/535.19"

eplist_url = "/includes/episode_page.php?cat={program:s}&id={videoid:s}&page={page:d}"
global_hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Connection': 'keep-alive'}

bitrate2resolution = {
    196:'180p',
    396:'240p',
    796:'300p',
    1196:'360p',
    1596:'480p',
    2296:'720p'
}

def parseTop(koPage=True):
    req  = urllib2.Request(page_url, headers=global_hdr)
    req.add_header('User-Agent', default_UA)
    if koPage:
        req.add_header('Accept-Langauge', 'ko')
        req.add_header('Cookie', 'language=kr')
    html = urllib2.urlopen(req).read()
    soup = BeautifulSoup(html)
    items = []
    for node in soup.find('div', {'id':'menu-category'}).findAll(lambda tag: tag.name=='a' and '.html' in tag['href']):
        items.append(node['href'])
    return items

def parseGenrePage(page_url, koPage=True):
    req  = urllib2.Request(page_url, headers=global_hdr)
    req.add_header('User-Agent', default_UA)
    if koPage:
        req.add_header('Accept-Langauge', 'ko')
        req.add_header('Cookie', 'language=kr')
    html = urllib2.urlopen(req).read()
    soup = BeautifulSoup(html)
    # soup.findAll('div', {'class':'genreSub'})
    items = []
    for node in soup.findAll('div', {'class':'ep_box'}):
        thumb = node.find('img', {'title':True})['src']
        items.append({'title':node.a['title'], 'url':root_url+'/'+node.a['href'], 'thumbnail':thumb})
    return items

def parseGenrePage2(page_url, koPage=True):
    req  = urllib2.Request(page_url)
    req.add_header('User-Agent', default_UA)
    if koPage:
        req.add_header('Accept-Langauge', 'ko')
        req.add_header('Cookie', 'language=kr')
    html = urllib2.urlopen(req).read().decode("utf-8")
    items = []
    for part in html.split('<div class="ep_box"')[1:]:
        match = re.compile('<a href="([^"]*)" title="([^"]*)" class="poster_img_a">.*<img src="([^"]*timthumb[^"]*)"', re.S).search(part)
        if match:
            items.append({'title':match.group(2), 'url':root_url+"/"+match.group(1), 'thumbnail':match.group(3)})
    return items

def parseEpisodePage(page_url, koPage=True):
    req  = urllib2.Request(page_url, headers=global_hdr)
    if koPage:
        req.add_header('Accept-Langauge', 'ko')
        req.add_header('Cookie', 'language=kr')
    html = urllib2.urlopen(req).read()
    soup = BeautifulSoup(html)
    # soup.findAll('div', {'class':'genreSub'})
    result = {'episode':[]}
    for node in soup.findAll('div', {'class':re.compile('^(?:ep|ep_last)$')}):
        if not node.b:
            continue
        title = node.b.string.replace('&amp;','&').replace('&lt;','<').replace('&gt;','>')
        thumb = node.find('img', {'title':True})['src']
        dt = node.b.findNextSibling(text=True)
        bdate = dt.string.split(':',1)[1].strip() if dt else ''
        result['episode'].append({'title':title, 'broad_date':bdate, 'url':root_url+node.a['href'], 'thumbnail':thumb})
    # no page navigation
    return result

def parseEpisodePage2(page_url, page=1, koPage=True):
    req  = urllib2.Request(page_url, headers=global_hdr)
    if koPage:
        req.add_header('Accept-Langauge', 'ko')
        req.add_header('Cookie', 'language=kr')
    html = urllib2.urlopen(req).read().decode('utf-8')
    program = re.compile('"program" *: *"(.*?)"').search(html).group(1)
    videoid = re.compile('"videoid" *: *(\d+)').search(html).group(1)
    list_url = root_url+eplist_url.format(program=program, videoid=videoid, page=page)
    req = urllib2.Request(list_url, headers=global_hdr)
    if koPage:
        req.add_header('Accept-Langauge', 'ko')
        req.add_header('Cookie', 'language=kr')
    #req.add_header('User-Agent', default_UA)
    jstr = urllib2.urlopen(req).read()
    obj = json.loads(jstr)

    result = {'episode':[]}
    for item in obj['list']:
        result['episode'].append({'title':item['title'], 'broad_date':item['on_air_date'], 'url':root_url+"/"+item['url'], 'thumbnail':img_base+item["thumbnail"]})
    if obj['cur_page'] > 1:
        result['prevpage'] = page-1
    if obj['cur_page'] < obj['num_pages']:
        result['nextpage'] = page+1
    return result

# rtmp
def extractStreamUrl(page_url, koPage=True):
    # loadPlayer()
    req = urllib2.Request(page_url, headers=global_hdr)
    req.add_header('User-Agent', default_UA)
    if koPage:
        req.add_header('Accept-Langauge', 'ko')
        req.add_header('Cookie', 'language=kr')
    html = urllib2.urlopen(req).read().decode('utf-8')
    vid_title = re.compile('<div id="title">(.*?)</div>', re.S).search(html).group(1).strip()
    info_url = root_url + re.compile("""['"](/includes/playlist.php\?token=\d+\|[^'"]*)""").search(html).group(1)
    print info_url
    xml = urllib.urlopen(info_url).read()
    root_node = etree.fromstring(xml)
    tcUrl = root_node.find('.//meta').attrib['base']
    app = tcUrl.rsplit('/',1)[1]
    videos = dict()
    paras = {'app':app, 'tcUrl':tcUrl}
    for item in root_node.findall('.//video'):
        resolution = bitrate2resolution[ int(item.attrib['system-bitrate'])/1000 ]
        videos[ resolution ] = {'tcUrl':tcUrl, 'app':app, 'playpath':item.attrib['src']}
    return {'title':vid_title, 'videos':videos}

# m3u8
def extractVideoUrl(page_url, koPage=True):
    req = urllib2.Request(page_url, headers=global_hdr)
#    req.add_header('User-Agent', tablet_UA)
    if koPage:
        req.add_header('Accept-Langauge', 'ko')
        req.add_header('Cookie', 'language=kr')
    html = urllib2.urlopen(req).read().decode('utf-8')
    vid_title = re.compile('<div id="title">(.*?)</div>', re.S).search(html).group(1).strip()
    #vid_url = re.compile('<video[^>]*src="([^"]*)"').search(html).group(1)
    vid_url = re.compile("""(http[^'"]*m3u8)""").search(html, re.I | re.U).group(1)
    videos = dict()
    for bitrate, resolution in bitrate2resolution.iteritems():
        videos[resolution] = {'url':vid_url.replace('480p.1596k', resolution+'.'+str(bitrate)+'k')}
    return {'title':vid_title, 'videos':videos}

if __name__ == "__main__":
    #print parseTop()
    #print parseGenrePage( root_url+"/variety" )
    print parseGenrePage2( root_url+"/variety" )
    #print parseEpisodePage( root_url+"/infinite-challenge-366.html" )
    print parseEpisodePage2( root_url+"/infinite-challenge-366.html", page=2 )
    #print extractStreamUrl( root_url+"/infinite-challenge-366.html" )
    print extractVideoUrl( root_url+"/infinite-challenge-366.html" )

# vim:sw=4:sts=4:et
