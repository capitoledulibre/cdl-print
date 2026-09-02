"""Booklet content that does not come from the schedule export.

Everything here is placeholder copy for the mockup. The editorial text, the
stands, the partners and the maps come from the organising team, not from
Pretalx, so they live in one file that a non-programmer can edit.
"""

EDITORIAL_TITLE = 'Bienvenue au Capitole du Libre'

EDITORIAL = [
    "Pour cette nouvelle édition, une équipe de bénévoles a passé l'année à "
    "monter un programme qui, nous l'espérons, vous donnera envie de rester "
    "les deux jours entiers.",

    "Le Capitole du Libre, c'est deux journées de conférences et d'ateliers "
    "autour du logiciel libre et de la culture libre, un village associatif "
    "de plus de trente stands, et surtout des gens à rencontrer. C'est "
    "gratuit, sur inscription : profitez-en pour amener quelqu'un qui n'y "
    "connaît rien.",

    "Ce livret est un condensé. Le programme complet, les résumés détaillés "
    "et les éventuels changements de dernière minute sont en ligne, et "
    "chaque conférence de ce livret porte un QR code qui y mène "
    "directement.",

    "Bonne édition à toutes et à tous.",
]

EDITORIAL_SIGNATURE = "L'équipe du Capitole du Libre"

VENUE = {
    'title': 'Le site',
    'body': [
        "Le Capitole du Libre se tient à l'ENSEEIHT, en plein centre de "
        "Toulouse, au 2 rue Charles Camichel. Les conférences occupent les "
        "bâtiments A, B et C ; le village associatif et la restauration se "
        "trouvent dans le Hall C.",

        "Métro ligne B, station Carmes ou Palais de Justice. Tram T1, arrêt "
        "Palais de Justice. Les vélos peuvent être attachés le long de la "
        "grille, côté rue Camichel.",
    ],
    'map_caption': 'Plan d’accès — à remplacer par le plan définitif',
}

BUILDINGS = {
    'title': 'Trouver sa salle',
    'body': [
        "Les salles portent le nom de leur bâtiment suivi de l'étage et du "
        "numéro : A201 est au deuxième étage du bâtiment A. Le Hall C, au "
        "rez-de-chaussée, accueille le village associatif, la restauration "
        "et le buffet du samedi soir.",
    ],
    'floors': [
        ('Bâtiment A', 'A001, A002 au rez-de-chaussée · A201 à A203 au 2e · '
                       'A301 à A304 au 3e'),
        ('Bâtiment B', 'B00 en amphithéâtre · B105 au 1er · B205 à B208 au 2e '
                       '· B306 à B308 au 3e'),
        ('Bâtiment C', 'C002 au rez-de-chaussée · Hall C pour le village '
                       'associatif'),
    ],
    'map_caption': 'Plan des étages — à remplacer par le plan définitif',
}

STANDS_TITLE = 'Le village associatif'

STANDS_INTRO = (
    "Le village associatif occupe le Hall C pendant les deux journées. "
    "C'est l'endroit où poser les questions qu'on n'ose pas poser en "
    "conférence."
)

STANDS = [
    ('Toulibre', "L'association qui organise le Capitole du Libre, et anime "
                 "des permanences toute l'année à Toulouse."),
    ('April', "Promotion et défense du logiciel libre depuis 1996."),
    ('Framasoft', "Éducation populaire aux enjeux du numérique et services "
                  "libres en ligne."),
    ('Debian France', "La distribution universelle et sa communauté "
                      "francophone."),
    ('Mozilla', "Firefox, Thunderbird et un web qui reste ouvert."),
    ('OpenStreetMap France', "La carte du monde libre, contribuée par ses "
                             "usagers."),
    ('Wikimédia France', "Wikipédia et les projets frères."),
    ('LinuxFr.org', "L'actualité du logiciel libre en français."),
    ('Emmabuntüs', "Reconditionnement de matériel et lutte contre "
                   "l'obsolescence programmée."),
    ('Chatons', "Le collectif des hébergeurs alternatifs, transparents, "
                "ouverts, neutres et solidaires."),
]

PRACTICAL_TITLE = 'Infos pratiques'

PRACTICAL = [
    ('Restauration', "Food trucks sur site le midi et buvette associative "
                     "dans le Hall C. Le cocktail du samedi soir est offert "
                     "et ouvert à toutes et tous."),
    ('Wifi', "Il n'y a pas de réseau ouvert au public : le wifi du site est "
             "réservé aux stands et aux ateliers. Prévoyez votre connexion "
             "si vous en avez besoin."),
    ('Accessibilité', "Les bâtiments A et C sont accessibles en fauteuil. "
                      "Pour le bâtiment B, demandez à un bénévole : un "
                      "itinéraire par l'arrière existe."),
    ('Enfants', "Un espace calme est disponible au Hall C. Les ateliers "
                "d'initiation sont ouverts dès 8 ans accompagnés."),
    ('Objets trouvés', "À l'accueil, Hall C, pendant toute la durée de "
                       "l'événement."),
]

EMERGENCY_TITLE = 'En cas de pépin'

EMERGENCY = [
    "Les bénévoles portent un t-shirt rouge : n'hésitez pas à les "
    "solliciter, c'est fait pour ça.",
    "Accueil et poste de secours : Hall C, rez-de-chaussée.",
    "Urgences : 15 (SAMU) · 17 (police) · 18 (pompiers) · 112 (numéro "
    "européen).",
    "Comportement problématique : signalez-le à un membre de l'équipe. "
    "Le Capitole du Libre applique un code de conduite, consultable en "
    "ligne.",
]

PARTNERS_TITLE = 'Nos partenaires'

PARTNERS_INTRO = (
    "Le Capitole du Libre est gratuit grâce au soutien de ses partenaires "
    "et au travail de ses bénévoles."
)

PARTNER_GROUPS = [
    ('Institutions', ['Toulouse Métropole', 'Région Occitanie', 'ENSEEIHT',
                      'Toulouse INP']),
    ('Entreprises', ['Partenaire Or 1', 'Partenaire Or 2', 'Partenaire Argent 1',
                     'Partenaire Argent 2', 'Partenaire Argent 3',
                     'Partenaire Bronze 1']),
    ('Associations', ['April', 'Framasoft', 'LinuxFr.org', 'Chatons']),
]

JOIN_TITLE = 'Rejoindre Toulibre'

JOIN = [
    "Le Capitole du Libre est organisé par Toulibre, association loi 1901 "
    "qui promeut le logiciel libre en Occitanie toute l'année.",
    "Adhérer, c'est soutenir l'événement et les permanences mensuelles. "
    "C'est aussi le meilleur moyen de donner un coup de main à la prochaine "
    "édition : il y a toujours de la place pour une paire de bras.",
    "Adhésion à prix libre, à partir de 10 €, sur place au stand Toulibre "
    "ou en ligne sur toulibre.org.",
]


# --- what to point a first-time visitor at ----------------------------------
#
# Drawn from capitoledulibre.org, then corrected by the team. Careful: the
# site's front page mentions a welcome breakfast and the venue has wifi, but
# neither is for the public -- the breakfast is not offered to visitors and
# the wifi carries the stands and the workshops. Do not "fix" these back from
# the site. The venue address, the transport details and the accessibility
# note still need checking against the definitive practical page.

FIRST_TIME_TITLE = 'Premier Capitole du Libre ?'

FIRST_TIME_LEDE = (
    "Deux journées, une trentaine de salles, plus de cent conférences et "
    "ateliers. Voilà l'essentiel pour ne pas être perdu."
)

FIRST_TIME = [
    ('C’est gratuit, mais il faut s’inscrire',
     "L'entrée ne coûte rien. L'inscription est en revanche obligatoire, en "
     "ligne sur tickets.capitoledulibre.org. Elle prend deux minutes et sert "
     "à dimensionner l'accueil et la restauration."),

    ('On entre et on sort quand on veut',
     "Aucune conférence ne se réserve : on s'assoit dans la salle, et on "
     "repart si le sujet n'est pas celui qu'on croyait. Personne ne le "
     "prendra mal. Les ateliers, eux, demandent parfois une inscription sur "
     "place et commencent à l'heure."),

    ('Commencez par le village associatif',
     "Plus de trente stands dans le Hall C : distributions, outils de "
     "protection de la vie privée, création artistique, matériel libre, "
     "associations locales. C'est le meilleur endroit pour poser les "
     "questions qu'on n'ose pas poser en conférence."),

    ('Il n’y a pas de prérequis',
     "Beaucoup de conférences s'adressent à qui n'a jamais installé Linux. "
     "L'atelier d'installation vous accompagne machine en main, et "
     "l'initiation au code accueille les enfants dès 8 ans."),

    ('Si vous ratez quelque chose',
     "Les conférences sont filmées et publiées sur "
     "videos.capitoledulibre.org. Deux conférences intéressantes en même "
     "temps n'est donc pas un drame : choisissez, et regardez l'autre plus "
     "tard."),

    ('Les bénévoles sont là pour ça',
     "T-shirt rouge, présents partout. Une salle introuvable, une question "
     "sur le programme, un souci quelconque : demandez-leur."),
]

FIRST_TIME_DAY = [
    ('9h30', "Ouverture de l'accueil"),
    ('10h00', "Premières conférences"),
    ('12h30', "Pause déjeuner, food trucks sur site"),
    ('14h00', "Reprise, conférences et ateliers"),
    ('19h30', "Le samedi : cocktail convivial, offert"),
]

# --- the handful of things to put in front of a newcomer --------------------
#
# Curated by the team: each entry matches a talk by a fragment of its title.
# A fragment that matches nothing is reported when the booklet is built, so a
# renamed talk cannot silently drop off the page.

HIGHLIGHTS_TITLE = 'À ne pas manquer'

HIGHLIGHTS_LEDE = (
    "Le programme est dense et tout s'y vaut. Si vous ne savez pas par où "
    "commencer, voilà quatre rendez-vous."
)

HIGHLIGHTS = [
    ('Bienvenue au', "L'ouverture : ce qui vous attend, en vingt minutes."),
    ('Linux Tracing Escape Game',
     "Un escape game pour démasquer les anomalies d'un système."),
    ('Sauvegarder librement',
     "Deux heures pour repartir avec ses sauvegardes en place."),
    ('Conférence de clôture', "Le mot de la fin, dimanche en fin d'après-midi."),
]
