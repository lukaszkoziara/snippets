import re

from bs4 import Comment
from HTMLParser import HTMLParser

from rerules import TEXTRULES


html_parser = HTMLParser()


def angular_extractor(content_string):
    if content_string.startswith('{{') and content_string.endswith('}}'):
        if content_string.count('\'') == 2:
            return content_string[content_string.find('\'') + 1:content_string.rfind('\'')]

    return content_string


def php_extractor(content_string):
    # eg: <meta content="[hidden_placeholder]" property="dlp:description">
    if content_string.startswith('[') and content_string.endswith(']'):
        # check if it is not only variable - some text with space
        if content_string.find(' ') > -1:
            return content_string[1:-1]
        else:
            return ''
    return content_string


def markdown_extractor(content_string):
    # eg: <meta content='**bleble.**' property='og:description'/>
    if len(content_string) > 4 and content_string.startswith('**') and content_string.endswith('**'):
        return content_string[2:-2]
    return content_string


def framework_extractor(content_string):
    return markdown_extractor(php_extractor(angular_extractor(content_string)))


def pictograms_clean(text):
    #
    # eg: https://9gag.com/
    return TEXTRULES.PICTOGRAMS.sub('', text).replace('\n', '').strip()


def non_breaking_spaces_clean(text):
    # eg: http://www.telegraph.co.uk/men/fatherhood/tragically-know-impact-losing-child-has-marriageall/
    return text.replace(u'\ufffd', ' ').replace(u'\xa0', ' ')


def html_entity_clean(text):
    # sometimes BS can`t deal with HTML entities
    # eg: http://www.calciomercato.com/news/genoamania-uno-0-0-tra-rimpianti-e-speranze-82408
    return html_parser.unescape(text or '')


def text_cleaner(text):
    return html_entity_clean(non_breaking_spaces_clean(pictograms_clean(framework_extractor(text))))


def get_language_iso(language_string):
    """Reduce language string, eg. from en-us to en"""

    language = language_string.split(",")[0].split("_")[0].split("-")[0].lower()
    return language if  len(language) == 2 else None


def find_lang_in_comments(head_soup_obj):
    """Find for comments, eg. <!--[if !IE]><html lang="fr"><![endif]-->"""

    comments = head_soup_obj.findAll(text=lambda text:(isinstance(text, Comment) and text.find("<html") > -1))
    for comment in comments:
        try:
            return re.search('lang=\"(.+?)\"', comment).group(1)
        except AttributeError:
            pass
    return None


def lower_fn(*attrs):
    """Prepare method for extract using case insensitive"""

    return lambda x: x is not None and x.lower() in attrs
