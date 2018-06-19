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
