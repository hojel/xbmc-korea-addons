# -*- coding: utf-8 -*-
"""
    Ondemand Korea
"""
from xbmcswift2 import Plugin
import os

plugin = Plugin()
_L = plugin.get_string

plugin_path = plugin.addon.getAddonInfo('path')
lib_path = os.path.join(plugin_path, 'resources', 'lib')
sys.path.append(lib_path)

import ondemandkorea as scraper

tPrevPage = u"[B]<<%s[/B]" %_L(30100)
tNextPage = u"[B]%s>>[/B]" %_L(30101)

root_url = "http://www.ondemandkorea.com"

@plugin.route('/')
def main_menu():
    #urls = scraper.parseTop()
    items = [
        #{'label':_L(30110), 'path':plugin.url_for('gallery_view', cate='kbs-news-9')},
        {'label':_L(30111), 'path':plugin.url_for('genre_view', genre='drama')},
        {'label':_L(30112), 'path':plugin.url_for('genre_view', genre='variety')},
        {'label':_L(30113), 'path':plugin.url_for('genre_view', genre='documentary')},
        {'label':_L(30114), 'path':plugin.url_for('genre_view', genre='food')},
        {'label':_L(30115), 'path':plugin.url_for('genre_view', genre='beauty')},
        {'label':_L(30116), 'path':plugin.url_for('genre_view', genre='women')},
        {'label':_L(30117), 'path':plugin.url_for('genre_view', genre='health')},
        {'label':_L(30118), 'path':plugin.url_for('genre_view', genre='sports')},
        #{'label':_L(30119), 'path':plugin.url_for('episode_view', url=urls[1])},
        {'label':_L(30120), 'path':plugin.url_for('genre_view', genre='economy')},
        {'label':_L(30121), 'path':plugin.url_for('genre_view', genre='religion')},
        #{'label':_L(30122), 'path':plugin.url_for('gallery_view', cate='hot')},
        {'label':_L(30123), 'path':plugin.url_for('genre_view', genre='kmuze')},
        {'label':_L(30124), 'path':plugin.url_for('genre_view', genre='games')},
    ]
    return items

@plugin.route('/genre/<genre>/')
def genre_view(genre):
    url = root_url+'/'+genre
    plugin.log.debug(url)
    info = scraper.parseGenrePage2(url, koPage=plugin.get_setting('koPage', bool))
    items = [{'label':item['title'], 'path':plugin.url_for('episode_view', url=item['url'], page=1), 'thumbnail':item['thumbnail']} for item in info]
    return plugin.finish(items, view_mode='thumbnail')

@plugin.route('/episode/<page>/<url>')
def episode_view(url, page):
    plugin.log.debug(url)
    info = scraper.parseEpisodePage2(url, page=int(page), koPage=plugin.get_setting('koPage', bool))
    items = [{'label':item['title'], 'label2':item['broad_date'], 'path':plugin.url_for('play_episode', url=item['url']), 'thumbnail':item['thumbnail']} for item in info['episode']]
    # navigation
    if 'prevpage' in info:
        items.append({'label':tPrevPage, 'path':plugin.url_for('episode_view', url=url, page=info['prevpage'])})
    if 'nextpage' in info:
        items.append({'label':tNextPage, 'path':plugin.url_for('episode_view', url=url, page=info['nextpage'])})
    return plugin.finish(items, update_listing=False)

@plugin.route('/play/<url>')
def play_episode(url):
    plugin.log.debug(url)
    resolution = plugin.get_setting('quality', str)
    use_mp4_url = plugin.get_setting('mp4_url', bool)

    if use_mp4_url:
        info = scraper.extractVideoUrl(url)
    else:
        info = scraper.extractStreamUrl(url)

    avail_resolutions = info['videos'].keys()
    if not resolution in avail_resolutions:
        resolution = avail_resolutions[0]
    video = info['videos'][resolution]

    if use_mp4_url:
        plugin.play_video( {'label':info['title'], 'path':video['url']} )
    else:
        flashVer = 'WIN 11,6,602,180'
        swfUrl = 'http://www.ondemandkorea.com/player/jw6.2/jwplayer.flash.swf'
        rtmp_url = "%s app=%s swfUrl=%s pageUrl=%s playpath=%s" % (video['tcUrl'], video['app'], swfUrl, url, video['playpath'])
        from xbmcswift2 import xbmc
        xbmc.Player().play( rtmp_url )

    return plugin.finish(None, succeeded=False)

if __name__ == "__main__":
    plugin.run()

# vim:sw=4:sts=4:et
