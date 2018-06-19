import re


class RERULES:
    DESCRIPTION = re.compile("description", re.I)
    KEYWORDS = re.compile("keywords", re.I)
    ARTICLETAG = re.compile("article:tag", re.I)
    TITLE = re.compile("title", re.I)
    FAVICON_TOUCH_LABELS = re.compile("apple-touch-icon*", re.IGNORECASE)
    IMAGESRC = re.compile("image_src", re.IGNORECASE)  # for rel image_src
    IMAGEOG = re.compile("image$", re.IGNORECASE)  # for og image
    HEAD = re.compile("^(.+?)(</head>|<body)", re.IGNORECASE | re.DOTALL)  # everything from the start, for lang sake
    REFRESH = re.compile("(\d+)?;?url=(.+)", re.IGNORECASE)
    ENCODINGMETA = re.compile(r'<meta http-equiv=.content-type.{0,100}?charset=(.{1,100}?)[\"|\'|\s|/]>',
                              re.IGNORECASE | re.DOTALL)
    ENCODINGMETA5 = re.compile(r'<meta\s+charset=(.{1,100}?)[\"|\'|\s|/|>]',
                               re.IGNORECASE | re.DOTALL)


class TEXTRULES:
    PICTOGRAMS = re.compile(u"[\U0001F300-\U0001F5FF]", flags=re.UNICODE)
