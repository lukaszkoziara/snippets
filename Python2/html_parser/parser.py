from urlparse import urlparse

from helpers import text_cleaner
from rerules import RERULES


def extract_title(soup_obj, page_url):
    """Try to catch longest title, otherwise create title from URL"""

    titles = []

    # collect main title
    title = soup_obj.find("title")

    if title and title.text:
        # remove whitespaces at first
        title = title.text.strip()
        # validate if title has start/end html tags
        if title.find('\n') > -1:
            title = title[:title.find('\n')]
        else:
            title = title
        # remove whitespaces at end, just in case because of splitting
        titles = [title.strip()]

    # collect OG titles
    og_titles = soup_obj.find_all("meta", {"property": RERULES.TITLE})
    og_titles = og_titles + soup_obj.find_all("meta", {"name": RERULES.TITLE})
    titles += [elem.get("content", "") for elem in og_titles]

    # remove duplicates
    titles = list(set(titles))

    # remove angularjs crap
    if titles:
        titles = map(text_cleaner, titles)

    # get longest text
    if titles:
        titles.sort(key=len, reverse=True)
        return titles[0]

    # otherwise extract title from url
    path = urlparse(page_url).path
    return (path[:-1] if path[-1] == '/' else path).split('/')[-1]