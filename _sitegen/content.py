# content.py: the content of the site. Publications are read from _publications/; everything else is kept here.
# Only verified facts: from the lab's earlier pages, its GitHub repositories and READMEs, and its own posts.
import os, re, html

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
E = html.escape


def front(path):
    s = open(path, encoding='utf-8').read().split('---')[1]
    out = {}
    for line in s.splitlines():
        m = re.match(r"^(\w+):\s*(.*)$", line)
        if m:
            v = m.group(2).strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
                v = v[1:-1]
            out[m.group(1)] = v
    return out


# people: (name, role, department, institution, since). Edit here to add or change someone, then rebuild.
PUC = 'Pontificia Universidad Católica de Chile'
PEOPLE = [
    ('Principal investigators', [
        ('Francisco Sahli Costabal', 'Assistant Professor', 'Department of Mechanical and Metallurgical Engineering and Institute for Biological and Medical Engineering', PUC, ''),
        ('Simone Pezzuto', 'Professor', 'Department of Mathematics', 'University of Trento', ''),
    ]),
    ('Postdocs', [('Juan José Molina', 'Postdoc', 'PhD in Mathematics', PUC, '')]),
    ('PhD students', [
        ('Efraín Magaña', 'PhD candidate', 'Mechanical Engineering', PUC, '2023'),
        ('Juan Ortega', 'PhD student', 'Mechanical Engineering', PUC, '2025'),
        ('Tabita Catalán', 'PhD student', 'Electrical Engineering', PUC, '2025'),
    ]),
    ('Research engineers', [('Tomás Banduc', 'Research engineer', '', 'iHEALTH', ''), ('Jessica Espinoza', 'Research engineer', '', 'iHEALTH', '')]),
    ('Master students', [
        ('Sofía Lozano', 'Master student', 'Engineering Sciences', PUC, ''),
        ('Tomás Erdmannsdörffer', 'Master student', 'Engineering Sciences', PUC, ''),
    ]),
]


PI_LINKS = {'Francisco Sahli Costabal': 'https://fsahli.github.io', 'Simone Pezzuto': 'https://mbm.maths.unitn.it/faculty/simone_pezzuto.html'}

# repositories: (name on github.com/HiddenHeartLab, description as the repository gives it, language)
SOFTWARE = [
    ('purkinje-learning', 'Probabilistic learning of the Purkinje network from the 12-lead ECG.', 'Jupyter Notebook'),
    ('WarpPINN', 'Computing cardiac strains from cine MRI with physics-informed neural networks.', 'Jupyter Notebook'),
    ('Delta-fibernet', 'Learning fiber orientation in the atria from electroanatomical maps with physics-informed neural networks.', 'Jupyter Notebook'),
    ('reentry-eikonal', 'Eikonal solver with re-excitability.', ''),
    ('logPSD-demo-FIMH', 'A log-map-based solver of the complex eikonal equation to initiate re-entry in monodomain simulations (FIMH 2025).', 'Jupyter Notebook'),
    ('FKS-demo', 'The fibrotic kernel signature, to estimate inducibility in atrial fibrillation simulations.', 'Python'),
]

# research themes: each sentence is taken from a paper title, a README or the lab's own post
RESEARCH = [
    dict(name='The Purkinje network', src='from the 12-lead ECG', pic='purkinje',
         text='Probabilistic learning of the Purkinje network, the heart’s fast conduction system, from the electrocardiogram.',
         paper=('Medical Image Analysis, 2025', 'https://www.sciencedirect.com/science/article/pii/S1361841525000088'), code='purkinje-learning'),
    dict(name='Fibre orientation', src='from electroanatomical maps', pic='fibres',
         text='Delta-fibernet learns the fibre orientation of the atria from electroanatomical maps, with an ensemble of physics-informed neural networks.',
         paper=('The Journal of Physiology, 2025', 'https://physoc.onlinelibrary.wiley.com/doi/abs/10.1113/JP288001'), code='Delta-fibernet'),
    dict(name='Wall strain', src='from cine MRI', pic='warppinn',
         text='WarpPINN-fibers reconstructs cardiac motion from cine MRI. It exploits the near-incompressibility of cardiac tissue and minimizes stretch in the direction of the fibres.',
         paper=('Engineering with Computers, 2026', 'https://link.springer.com/article/10.1007/s00366-026-02295-4'), code='WarpPINN'),
    dict(name='Inducibility', src='without simulation', pic='fks',
         text='The fibrotic kernel signature predicts atrial fibrillation inducibility without running simulations.',
         paper=('Medical Image Analysis, 2025', 'https://www.sciencedirect.com/science/article/pii/S1361841524003001'), code='FKS-demo'),
    dict(name='Re-entry', src='from the complex eikonal equation', pic='reentry',
         text='Spiral waves are expensive to generate. We solve the complex eikonal equation on the plane and morph it to the shape of the atria, to start simulations of atrial fibrillation with stable sources of re-entry.',
         paper=('FIMH 2025', 'https://link.springer.com/chapter/10.1007/978-3-031-94559-5_15'), code='logPSD-demo-FIMH'),
]

LINKEDIN = 'https://www.linkedin.com/feed/update/'
GITHUB = 'https://github.com/HiddenHeartLab/'
# the meta description of the home page (not shown on the page)
SUB = ('The hidden heart lab, the research groups of Francisco Sahli Costabal at the Pontificia Universidad Católica de Chile '
       'and Simone Pezzuto at the University of Trento.')
MISSION = 'Our mission is to unveil the cardiac structure and function from affordable and non-invasive data.'


def _kind(venue, url):
    v, u = venue.lower(), url.lower()
    if 'arxiv' in v or 'arxiv' in u or 'biorxiv' in v or 'researchsquare' in u:
        return 'preprint'
    if 'link.springer.com/chapter' in u or 'proceedings' in v or 'ifac' in v:
        return 'chapter'
    if venue and venue != 'Working Paper':
        return 'journal'
    return 'other'


def all_publications():
    """Every entry in _publications, newest first; the arXiv copy of a published paper is shown once."""
    d = os.path.join(ROOT, '_publications')
    items = []
    for f in sorted(os.listdir(d), reverse=True):
        p = front(os.path.join(d, f))
        title = p['title'].lstrip('-').strip()
        url, venue = p.get('paperurl', ''), p.get('venue', '')
        kind = _kind(venue, url)
        if 'arxiv' in venue.lower():
            venue = 'arXiv'
        if '978-3-031-94559-5_15' in url:  # named as a FIMH paper in the lab's own post
            venue = 'Functional Imaging and Modeling of the Heart (FIMH 2025)'
        if venue == 'Working Paper':
            venue = ''
        m = re.match(r'^(.*?)\.\s*\((\d{4})\)', html.unescape(p.get('citation', '')))
        authors = ''
        if m:
            names = [a.strip() for a in m.group(1).split(' and ') if a.strip()]
            authors = ', '.join(names[:-1]) + (' and ' if len(names) > 1 else '') + names[-1] if names else ''
        items.append(dict(title=title, venue=venue, url=url, year=f[:4], kind=kind, authors=authors))
    seen, out = set(), []
    for i in sorted(items, key=lambda i: (i['year'], i['kind'] == 'journal'), reverse=True):
        k = i['title'].lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(i)
    return out


KIND_LABEL = {'journal': 'Journal article', 'preprint': 'Preprint', 'chapter': 'Chapter or proceedings', 'other': 'Other'}


def news_items():
    import json
    return json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'news.json'), encoding='utf-8'))
