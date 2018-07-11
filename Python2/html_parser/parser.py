import re
from urlparse import urlparse

from helpers import text_cleaner, get_language_iso, find_lang_in_comments, lower_fn
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


def extract_description(soup_obj):
    """Try to catch description"""

    descriptions = []
    descriptions.extend(soup_obj.find_all("meta", {"name": RERULES.DESCRIPTION}))
    descriptions.extend(soup_obj.find_all("meta", {"property": RERULES.DESCRIPTION}))

    description = None
    # extract & cleanup
    if descriptions:
        # clear html tags, eg. <p>, <br/>
        descriptions = [re.sub('<.*?>', '', elem.get('content', '')).strip() for elem in descriptions]

    if descriptions:
        # remove duplicates
        descriptions = list(set(descriptions))
        # remove empty elements
        descriptions = filter(None, descriptions)
        # clear framework`s crap
        descriptions = map(text_cleaner, descriptions)

    # select after cleanup
    if descriptions:
        # get longest
        description = max(descriptions, key=lambda a: len(a)).strip() or ''
    return description


def extract_language(soup_obj, head_soup_obj, keyword_parser, title='', description=''):
    """Try to catch language"""

    language = None
    language_temp = None

    # variuos ways to get language
    language_elem = soup_obj.find("html", {"lang": True})  # html5
    if language_elem:
        language_temp = language_elem.get("lang", "")
    else:  # deprecated meta
        language_elem = soup_obj.find("meta", {"http-equiv": lower_fn("content-language")})
        if language_elem:
            language_temp = language_elem.get("content", "")
        else:
            language_elem = soup_obj.find("meta", {"property": lower_fn("og:locale")})
            if language_elem:
                language_temp = language_elem.get("content", "")
            else:
                language_elem = soup_obj.find("meta", {"name": lower_fn("language")})
                if language_elem:
                    language_temp = language_elem.get("content", "")

    # clean language code
    if language_temp:
        language = get_language_iso(language_temp)

    # try find language in html comments
    if not language:
        language_temp = find_lang_in_comments(head_soup_obj)
        if language_temp:
            language = get_language_iso(language_temp)

    # check title+description length
    dummy_body = u"{} {}".format(title, description)
    if len(dummy_body) > 20:
        language = keyword_parser.get_language(dummy_body) or ''

    return language
