# build.py: writes the pages of the site (home, people, publications, software, news, page not found)
# from content.py, news.json and templates/. Run from anywhere:  python _sitegen/build.py
import os, re, sys, json, struct, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from content import (E, PEOPLE, PI_LINKS, SOFTWARE, RESEARCH, LINKEDIN, GITHUB, SUB, MISSION,
                     all_publications, news_items, KIND_LABEL)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(HERE, '..')
ASSETS = os.path.join(ROOT_DIR, 'assets', 'hhl')
A = '/assets/hhl/'
SITE = 'https://hiddenheartlab.com'
NAME = 'the hidden heart lab'
HEART_D = ('M0.5,0.94C0.5,0.94 0.04,0.62 0.04,0.32C0.04,0.14 0.17,0.03 0.3,0.03C0.4,0.03 0.47,0.09 0.5,0.17'
           'C0.53,0.09 0.6,0.03 0.7,0.03C0.83,0.03 0.96,0.14 0.96,0.32C0.96,0.62 0.5,0.94 0.5,0.94Z')
PAGES = [('people', '/people/'), ('publications', '/publications/'), ('software', '/software/')]
OUT = {'index': 'index.html', 'people': 'people/index.html', 'publications': 'publications/index.html',
       'software': 'software/index.html', 'news': 'news/index.html', '404': '404.html'}
URL = {'index': '/', 'people': '/people/', 'publications': '/publications/', 'software': '/software/', 'news': '/news/',
       '404': '/404.html'}
TITLES = {'index': NAME, 'people': 'People at the hidden heart lab',
          'publications': 'Publications of the hidden heart lab', 'software': 'Codes and demos of the hidden heart lab',
          'news': 'News from the hidden heart lab', '404': 'Page not found at the hidden heart lab'}
# every image path below is relative to assets/hhl/
PICS = {'purkinje-learning': ('media/drawn/purkinje-black.svg', 'A Purkinje network drawn as a fractal tree'),
        'WarpPINN': ('media/warppinn-poster.jpg', 'WarpPINN tracking the left ventricle on a cine MRI plane'),
        'Delta-fibernet': ('media/fibres-medoid.png', 'Atrial fibres learned by Delta-fibernet'),
        'reentry-eikonal': ('media/reentry-wave-poster.jpg', 'Re-entrant waves on a left atrium'),
        'logPSD-demo-FIMH': ('media/phase-map-poster.jpg', 'A phase map started by the complex eikonal solver'),
        'FKS-demo': ('media/fks-atrium-poster.jpg', 'An atrium coloured by its fibrotic kernel signature')}
PAPER_FIGS = {'warppinn-fibers': ('media/news/7387151064086626304.webp', 'Figure from the WarpPINN-fibers post'),
              'complex eikonal equation to initiate': ('media/news/7345799831262556160.webp', 'Spiral waves started by the complex eikonal solver'),
              'fibrotic kernel signature': ('media/news/7260328315943632896.jpg', 'Overview of the fibrotic kernel signature method'),
              'purkinje network from the electrocardiogram': ('media/news/7142513366824120320.jpg', 'A learned Purkinje network and its ECG'),
              'accelerated cardiac cine mri using neural fields': ('media/news/7095395379642261504.webp', 'Cine MRI reconstructed with neural fields'),
              'ensemble learning of the atrial fibre': ('media/fibres-medoid.png', 'Atrial fibres learned by Delta-fibernet'),
              'warppinn: cine-mr image registration': ('media/warppinn-poster.jpg', 'WarpPINN on a cine MRI plane')}
STRIP = ['7321606279813029888', '7369722373433880576', '7345799831262556160', '7095395379642261504']
PREVIEWS = {'warppinn-fibers': 'media/warppinn-poster.jpg', 'purkinje network from the electrocardiogram': 'media/drawn/purkinje-black.svg',
            'fibrotic kernel signature': 'media/fks-atrium-poster.jpg', 'complex eikonal': 'media/phase-map-poster.jpg',
            'atrial fibre orientation': 'media/fibres-medoid.png'}
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
METHOD = ['Probabilistic learning', 'Ensemble of physics-informed neural networks', 'Physics-informed neural networks',
          'Fibrotic kernel signature', 'Complex eikonal equation']
STARTS = ['The 12-lead ECG', 'Electroanatomical maps', 'Cine MRI', 'The atrium and its fibrosis', 'The shape of the atrium']


def nice_date(iso, day=True):
    y, m, d = iso.split('-')
    return f'{int(d)} {MONTHS[int(m) - 1]} {y}' if day else f'{MONTHS[int(m) - 1]} {y}'


def img_size(rel):
    """Width and height in pixels of an image under assets/hhl/, read from the file header (png, jpg, webp, svg)."""
    b = open(os.path.join(ASSETS, rel), 'rb').read()
    if b[:8] == b'\x89PNG\r\n\x1a\n':
        return struct.unpack('>II', b[16:24])
    if b[:2] == b'\xff\xd8':
        i = 2
        while i + 9 < len(b):
            if b[i] != 0xFF:
                i += 1
                continue
            m = b[i + 1]
            if 0xC0 <= m <= 0xCF and m not in (0xC4, 0xC8, 0xCC):   # a start-of-frame segment holds the size
                h, w = struct.unpack('>HH', b[i + 5:i + 9])
                return w, h
            if m == 0xFF or m == 0x01 or 0xD0 <= m <= 0xD9:         # padding and markers without a length
                i += 1 if m == 0xFF else 2
                continue
            i += 2 + struct.unpack('>H', b[i + 2:i + 4])[0]
    if b[:4] == b'RIFF' and b[8:12] == b'WEBP':
        kind = b[12:16]
        if kind == b'VP8X':
            return 1 + int.from_bytes(b[24:27], 'little'), 1 + int.from_bytes(b[27:30], 'little')
        if kind == b'VP8 ':
            w, h = struct.unpack('<HH', b[26:30])
            return w & 0x3FFF, h & 0x3FFF
        if kind == b'VP8L':
            n = int.from_bytes(b[21:25], 'little')
            return 1 + (n & 0x3FFF), 1 + ((n >> 14) & 0x3FFF)
    m = re.search(rb'viewBox="[\d.\-]+[ ,]+[\d.\-]+[ ,]+([\d.]+)[ ,]+([\d.]+)"', b[:2000])
    if m:
        return round(float(m.group(1))), round(float(m.group(2)))
    raise ValueError(f'cannot read the size of {rel}')


def img(rel, alt, cls='', lazy=True, enter=False):
    """An <img> with its real width and height, so the page does not jump while it loads."""
    w, h = img_size(rel)
    return ('<img' + (f' class="{cls}"' if cls else '') + (' data-enter="picture"' if enter else '') + f' src="{A}{rel}" width="{w}" height="{h}" alt="{E(alt)}"'
            + (' loading="lazy"' if lazy else '') + '>')


def still_of(rel):
    """An animated image keeps a still frame beside it, named <file>-still.jpg; '' when the image does not move."""
    s = os.path.splitext(rel)[0] + '-still.jpg'
    return s if os.path.exists(os.path.join(ASSETS, s)) else ''


ENTER = ' data-enter="picture"'


def moving_img(rel, alt, enter=False):
    """An image that may be animated: it plays, and stands still (its <file>-still.jpg) under reduced motion.
    Put it inside a [data-motion] block so base.js gives it a pause button."""
    still = still_of(rel)
    if not still:
        return img(rel, alt, enter=enter)
    w, h = img_size(rel)
    return (f'<picture{ENTER if enter else ""}><source media="(prefers-reduced-motion: reduce)" srcset="{A}{still}">'
            f'<img src="{A}{rel}" data-still="{A}{still}" width="{w}" height="{h}" alt="{E(alt)}" loading="lazy"></picture>')


def moving(rel, alt, motion='the animation'):
    """A figure for an image that may be animated, with its pause button when it moves."""
    m = f' data-motion="{motion}"' if still_of(rel) else ''
    return f'<figure{ENTER}{m}>{moving_img(rel, alt)}</figure>'


def paper_fig(p):
    f = next((v for k, v in PAPER_FIGS.items() if k in p['title'].lower()), None)
    return moving(*f) if f else ''   # a paper whose figure moves keeps it moving


def post_fig(n):
    """The image of a news post. An animated one plays with a pause button (base.js) and stays still under reduced motion."""
    if not n['img']:
        return ''
    if not n.get('alt'):
        print('  note: news post', n['id'], 'has an image without "alt" in news.json')
    return moving(n['img'], n.get('alt', ''))


def slug(name):
    s = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode().lower()
    return '-'.join(s.split())


def portrait(name):
    """The person's photo, or '' when assets/hhl/media/people/<firstname-lastname>.jpg does not exist yet."""
    for ext in ('jpg', 'jpeg', 'png', 'webp'):
        rel = f'media/people/{slug(name)}.{ext}'
        if os.path.exists(os.path.join(ASSETS, rel)):
            return f'<div class="portrait">{img(rel, name)}</div>'
    return ''


def link_name(n):
    return f'<a href="{PI_LINKS[n]}">{E(n)}</a>' if n in PI_LINKS else E(n)


def parts(page, desc):
    head = [
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f'<title>{TITLES[page]}</title>',
        f'<meta name="description" content="{E(desc)}">',
        '<meta name="theme-color" content="#121212">',
        # "enter" switches the scroll entrances on; the page drops it again if base.js, which plays them, did not load
        "<script>(function(d){d.classList.add('js','enter');addEventListener('load',function(){if(!window.HHEnter)d.classList.remove('enter')})})(document.documentElement)</script>",
        f'<link rel="preload" href="{A}fonts/texgyreheros-bold.woff2" as="font" type="font/woff2" crossorigin>',
        f'<link rel="preload" href="{A}fonts/redhattext-latin.woff2" as="font" type="font/woff2" crossorigin>',
        f'<link rel="stylesheet" href="{A}base.css">',
        f'<link rel="stylesheet" href="{A}site.css">',
        f'<link rel="icon" href="{A}favicon.svg" type="image/svg+xml">']
    if page == '404':
        head.append('<meta name="robots" content="noindex">')
    else:
        head += [
            f'<link rel="canonical" href="{SITE}{URL[page]}">',
            '<meta property="og:type" content="website">',
            f'<meta property="og:site_name" content="{NAME}">',
            f'<meta property="og:title" content="{TITLES[page]}">',
            f'<meta property="og:description" content="{E(desc)}">',
            f'<meta property="og:url" content="{SITE}{URL[page]}">',
            f'<meta property="og:image" content="{SITE}{A}media/logo-foot.png">',
            '<meta name="twitter:card" content="summary_large_image">']
    if page == 'index':   # tells search engines what the site is; every value is already on the page
        ld = {'@context': 'https://schema.org', '@type': 'ResearchOrganization', 'name': NAME, 'url': SITE + '/',
              'logo': f'{SITE}{A}media/logo-foot.png', 'description': SUB, 'sameAs': [GITHUB.rstrip('/')]}
        head.append('<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + '</script>')
    nav = ''.join(f'<a href="{href}"' + (' aria-current="page"' if key == page else '') + f'>{key}</a>' for key, href in PAGES)
    home = '#top' if page == 'index' else '/'
    bar = ('<header class="' + ('bar dock' if page == 'index' else 'bar') + '"><a class="skip" href="#main">Skip to the content</a>'
           # the lab's logo (logo-foot.png): its lattice square, and the wordmark set in white beside it;
           # on the home page the banner's logo docks into it (dock.js)
           f'<a class="mark" href="{home}" aria-label="the hidden heart lab, home">'
           f'<span class="sq"><img src="{A}media/logo-square.jpg" width="192" height="192" alt=""></span>'
           '<span class="mini" aria-hidden="true"><span class="x">the</span><span class="hh">hidden</span><span class="hh">heart</span>'
           '<span class="x">lab</span></span></a>'
           f'<nav aria-label="Pages">{nav}</nav></header>')
    foot = '\n'.join([
        '<footer class="foot">',
        '  <div class="foot-logo">',
        f'    <img src="{A}media/logo-foot.png" width="1220" height="638" alt="the hidden heart lab" loading="lazy">',
        '  </div>',
        '  <div class="foot-side">',
        '    <ul class="foot-groups">',
        # the universities' own logos (white originals from uc.cl and unitn.it, set in the site's black), linked to them
        f'      <li><a class="uni" href="https://www.uc.cl/">{img("media/logos/uc.svg", "Pontificia Universidad Católica de Chile")}</a>'
        f'{link_name("Francisco Sahli Costabal")}<span>Pontificia Universidad Católica de Chile, Santiago</span></li>',
        f'      <li><a class="uni" href="https://www.unitn.it/en">{img("media/logos/unitn.svg", "University of Trento")}</a>'
        f'{link_name("Simone Pezzuto")}<span>University of Trento, Italy</span></li>',
        '    </ul>',
        '    <p class="foot-links"><a href="/people/">People</a><a href="/publications/">Publications</a><a href="/software/">Software</a><a href="/news/">News</a><a href="https://github.com/HiddenHeartLab">GitHub</a></p>',
        '  </div>',
        '</footer>'])
    return {'head': '\n'.join(head), 'bar': bar, 'foot': foot, 'mission': E(MISSION), 'heart_d': HEART_D}


def content():
    out = {}
    news = news_items()
    pubs = all_publications()
    years_all = [p['year'] for p in pubs]
    out['news_since'] = nice_date(news[-1]['date'], False)
    out['pub_count'] = str(len(pubs))
    out['pub_first'], out['pub_last'] = min(years_all), max(years_all)
    # the five latest posts, each with its picture or video beside it
    out['latest'] = '\n'.join(
        f'    <li class="nrow"><a href="/news/#post-{n["id"]}"><span class="when">{nice_date(n["date"])}</span>'
        f'<span class="t">{E(n["title"])}</span><span class="by">Posted by {E(n["actor"])}</span></a>{post_fig(n)}</li>'
        for n in news[:5])

    # the two groups under the banner: the PI's name (to their page), the university and its logo
    out['pis'] = '\n'.join(
        f'    <li><a class="pi" href="{PI_LINKS[n]}">{E(n)}</a><span class="inst">{E(u)}</span>'
        f'<a class="pi-uni" href="{h}">{img(logo, u)}</a></li>'
        for n, u, h, logo in [('Francisco Sahli Costabal', 'Pontificia Universidad Católica de Chile', 'https://www.uc.cl/', 'media/logos/uc.svg'),
                              ('Simone Pezzuto', 'University of Trento', 'https://www.unitn.it/en', 'media/logos/unitn.svg')])

    rows, shown = [], 0
    for p in pubs[:6]:
        pic = next((v for k, v in PREVIEWS.items() if k in p['title'].lower()), '')
        pv = ''
        if pic:
            shown += 1
            pv = img(pic, '', 'pv first' if shown <= 3 else 'pv')
        rows.append(f'      <li><a href="{E(p["url"])}"><span class="t">{E(p["title"])}</span>'
                    f'<span class="v">{E(p["venue"])}</span><span class="y">{p["year"]}</span></a>{pv}</li>')
    out['ledger'] = '\n'.join(rows)

    # research table: what each line starts from, its method with the paper, and its repository
    out['table'] = '\n'.join(
        f'      <div class="tr" role="row"><div class="th" role="rowheader">{E(r["name"])}</div><div class="td feat" role="cell">{E(STARTS[i])}</div>'
        f'<div class="td" role="cell">{E(METHOD[i])}<a class="src" href="{E(r["paper"][1])}">{E(r["paper"][0])}</a></div>'
        f'<div class="td" role="cell"><a href="{GITHUB}{r["code"]}">{E(r["code"])}</a></div></div>'
        for i, r in enumerate(RESEARCH))

    # people: one block per role. A person with a photo gets a portrait card; without one, a line of type.
    blocks = []
    for gi, (g, ps) in enumerate(PEOPLE):
        cards, lines = [], []
        for n, r, d, pl, y in ps:
            facts = '<br>'.join([E(f'{r}, {d}' if d else r), E(pl)] + ([f'Since {y}'] if y else []))
            ph = portrait(n)
            if ph:
                cards.append(f'        <li class="person">{ph}<h3>{link_name(n)}</h3><p>{facts}</p></li>')
            else:
                lines.append(f'        <li><span class="a">{link_name(n)}</span><span class="b">{facts}</span></li>')
        body = ''
        if cards:
            body += '      <ul class="ppl">\n' + '\n'.join(cards) + '\n      </ul>\n'
        if lines:
            body += '      <ul class="lineup">\n' + '\n'.join(lines) + '\n      </ul>\n'
        blocks.append(f'  <section class="role" aria-labelledby="role-{gi}">\n    <h2 id="role-{gi}" data-enter="title">{E(g)}</h2>\n'
                      f'    <div class="who">\n{body}    </div>\n  </section>')
    out['people_groups'] = '\n'.join(blocks)

    code_of = {r['paper'][1]: r['code'] for r in RESEARCH}   # papers that have a public repository
    years = {}
    for p in pubs:
        years.setdefault(p['year'], []).append(p)
    out['year_links'] = ''.join(f'<a href="#y{y}">{y}</a>' for y in years)
    blocks = []
    for y, items in years.items():
        lis = []
        for p in items:
            code = (f'<p class="co"><a href="{GITHUB}{code_of[p["url"]]}">Code on GitHub</a></p>' if p['url'] in code_of else '')
            lis.append(
                f'        <li class="paper" data-kind="{p["kind"]}"><a class="t" href="{E(p["url"])}">{E(p["title"])}</a>'
                f'<p class="au">{E(p["authors"])}</p>'
                f'<p class="ve">{E(", ".join(x for x in (p["venue"], KIND_LABEL[p["kind"]]) if x))}</p>{code}{paper_fig(p)}</li>')
        blocks.append(f'    <section class="year" id="y{y}" aria-labelledby="h{y}"><h2 id="h{y}" data-enter="title">{y}</h2>\n      <ol>\n'
                      + '\n'.join(lis) + '\n      </ol>\n    </section>')
    out['years'] = '\n'.join(blocks)

    repos = []
    for n, d, l in SOFTWARE:
        if n == 'WarpPINN':
            fig = (f'<figure data-enter="picture" data-motion="the video"><video src="{A}media/warppinn.mp4" poster="{A}media/warppinn-poster.jpg" width="1080" height="810" '
                   f'autoplay muted loop playsinline aria-label="{E(PICS[n][1])}"></video></figure>')
        else:
            fig = f'<figure data-enter="picture">{img(*PICS[n])}</figure>'
        repos.append(f'    <li class="repo"><h2 data-enter="title"><a href="{GITHUB}{n}">{E(n)}</a></h2>'
                     f'<div class="desc">{E(d)}<span>{(E(l) + ". ") if l else ""}<a href="{GITHUB}{n}">Open on GitHub</a></span></div>{fig}</li>')
    out['repos'] = '\n'.join(repos)

    posts = []
    members = {p[0] for _, ps in PEOPLE for p in ps}
    for n in news:
        # posts written by people outside the lab keep only title, author and link; their wording is theirs
        body = ''.join(f'<p>{E(b)}</p>' for b in n['body']) if n['actor'] in members else ''
        posts.append(
            f'  <article class="post" id="post-{n["id"]}" aria-labelledby="t-{n["id"]}">\n'
            f'    <p class="when" data-enter="title">{nice_date(n["date"])}</p>\n'
            f'    <div class="body"><h2 id="t-{n["id"]}">{E(n["title"])}</h2><p class="by">Posted by {E(n["actor"])}</p>{body}'
            f'<a class="read" href="{LINKEDIN}{n["urn"]}">Read the full post on LinkedIn</a></div>\n    {post_fig(n)}\n  </article>')
    out['posts'] = '\n'.join(posts)
    byid = {n['id']: n for n in news}
    # the strip's pictures are decoration beside the post title, so their alt is empty; animated ones show their still
    out['strip'] = '\n'.join(
        f'    <a href="/news/#post-{i}">{moving_img(byid[i]["img"], "", enter=True)}<span>{E(byid[i]["title"])}</span></a>'
        for i in STRIP)
    return out


def build():
    c = content()
    desc = {'index': SUB, '404': SUB,
            'people': 'People at the hidden heart lab, in Francisco Sahli Costabal’s group in Santiago and Simone Pezzuto’s group in Trento.',
            'publications': f'Publications of the hidden heart lab from {c["pub_first"]} to {c["pub_last"]}, newest first.',
            'software': 'Codes and demos of the hidden heart lab. The lab’s public repositories on GitHub.',
            'news': f'News from the hidden heart lab. Posts from LinkedIn since {c["news_since"]}.'}
    for page, rel in OUT.items():
        s = open(os.path.join(HERE, 'templates', page + '.html'), encoding='utf-8').read()
        vals = {**parts(page, desc[page]), **c}

        def sub(m):
            k = m.group(1)
            if k not in vals:
                raise KeyError(f'{page}: no content for marker {k}')
            return vals[k]
        s = re.sub(r'<!--@(\w+)-->', sub, s)
        s = s.replace('<!doctype html>\n', '<!doctype html>\n<!-- Generated by _sitegen/build.py from _sitegen/templates/' + page
                      + '.html. Edit the template or the data, then run: python _sitegen/build.py -->\n', 1)
        out = os.path.join(ROOT_DIR, rel)
        os.makedirs(os.path.dirname(out) or ROOT_DIR, exist_ok=True)
        open(out, 'w', encoding='utf-8', newline='\n').write(s)
        print('built', rel)


if __name__ == '__main__':
    build()
