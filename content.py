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
        "bâtiments A, B et C. L'accueil, la buvette et le village "
        "associatif sont dans le Hall C, les food trucks dans le parc.",

        "Métro ligne B, station François Verdier (5 min à pied), ou ligne A, "
        "station Jean Jaurès (10 min). Gare Matabiau à 15 min à pied. Des "
        "attaches vélo sont disponibles dans les rues alentour.",
    ],
    # The campus plan goes under the text, and a QR code to the venue on
    # OpenStreetMap for the way there.
    'plan': True,
    'map_url': 'https://www.openstreetmap.org/?mlat=43.6024&mlon=1.4545'
               '#map=17/43.6024/1.4545',
    'map_label': 'Le lieu sur OpenStreetMap',
}

BUILDINGS = {
    'title': 'Trouver sa salle',
    'body': [
        "Les salles portent le nom de leur bâtiment suivi de l'étage et du "
        "numéro : A201 est au deuxième étage du bâtiment A. B00 est "
        "l'amphithéâtre, au rez-de-chaussée du bâtiment B. Ascenseurs dans "
        "chaque bâtiment.",
    ],
    # The rooms are listed floor by floor from the schedule itself.
    'floors': True,
}

# --- the campus plan --------------------------------------------------------
#
# Taken from capitoledulibre.org/lieu/. The legend follows the numbered pins
# of assets/plan-enseeiht.svg, in the same order.

PLAN_TITLE = 'Plan du site'

PLAN_LEGEND = [
    'Accueil & buvette',
    'Village associatif',
    'Food trucks',
    'Amphi B00',
    'Atelier installation',
]

# The leaflet is handed out on site, so it carries the opening hours rather
# than directions. They replace the 'Horaires' entry of PRACTICAL there.
ACCESS_HOURS_TITLE = 'Horaires d’accès'

ACCESS_HOURS = [
    ('Samedi', "Ouverture à 9h30. Cocktail offert à 19h30 dans le hall "
               "principal. À partir de 19h30, seules les personnes déjà "
               "entrées peuvent accéder au site : les billets ne sont plus "
               "validés. Pour le cocktail, arrivez avant !"),
    ('Dimanche', "Ouverture à 9h30. L'accès ferme à 16h30."),
]

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
    ('Horaires', "Accueil dès 9h30, premières conférences à 10h. Le samedi "
                 "à 19h30, cocktail offert à toutes et tous dans le hall "
                 "principal, sans inscription."),
    ('Restauration', "Deux food trucks le midi (10 à 15 €) et buvette "
                     "associative dans le Hall C."),
    ('Wifi', "Il n'y a pas de réseau ouvert au public : le wifi du site est "
             "réservé aux stands et aux ateliers. Prévoyez votre connexion "
             "si vous en avez besoin."),
    ('Accessibilité', "Tous les bâtiments sont accessibles aux personnes à "
                      "mobilité réduite, avec ascenseurs."),
    ('Enfants', "L'initiation au code, au bâtiment B, accueille les 8-14 "
                "ans avec Scratch, le samedi seulement, de 10h à 12h et de "
                "14h à 17h."),
    ('Objets trouvés', "À l'accueil, Hall C, pendant toute la durée de "
                       "l'événement."),
    ('Bienveillance', "L'événement applique un code de conduite. Un "
                      "problème sur place : adressez-vous à l'équipe en "
                      "t-shirt rouge « STAFF », ou écrivez à "
                      "conduite@capitoledulibre.org."),
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

# Taken from capitoledulibre.org/partenaires/, sponsors by tier first.
PARTNER_GROUPS = [
    ('Platine', ['Airbus', 'Bootlin', 'CS Group', 'Thales']),
    ('Or', ['Brax Technologies', 'Data Bene', 'Linagora', 'Makina Corpus']),
    ('Argent', ['ANITI', 'Collabora', 'Evolix', 'Smile', 'Worteks', 'XWiki']),
    ('Bronze', ['Attitude SI', 'Bareos', 'Bleemeo', 'BlueMind', 'Loxodata',
                'Viveris']),
    ('Institutions', ['Conseil départemental de la Haute-Garonne',
                      'Mairie de Toulouse', 'Région Occitanie']),
    ('Média', ['SysOps Pratique']),
    ('Partenaires techniques', ['Bleemeo', 'CAn7', 'Epitech Toulouse',
                                'Etincelle Coworking', 'INP-net', 'net7',
                                'photo7', 'Scaleway', 'Tetaneutral', 'N7',
                                'Toulouse Tech Hub', 'TVn7']),
]

# Logos under assets/partners/, downloaded from the same page. A partner
# without one is printed as its name.
PARTNER_LOGOS = {
    'Airbus': 'airbus.png',
    'Bootlin': 'bootlin.png',
    'CS Group': 'cs-group.svg',
    'Thales': 'thales.svg',
    'Brax Technologies': 'brax-technologies.svg',
    'Data Bene': 'databene.png',
    'Linagora': 'linagora.svg',
    'Makina Corpus': 'makina-corpus.png',
    'ANITI': 'aniti.png',
    'Collabora': 'collabora.svg',
    'Evolix': 'evolix.png',
    'Smile': 'smile.png',
    'Worteks': 'worteks.png',
    'XWiki': 'xwiki.svg',
    'Attitude SI': 'attitudesi.png',
    'Bareos': 'bareos.png',
    'Bleemeo': 'bleemeo.svg',
    'BlueMind': 'bluemind.png',
    'Loxodata': 'loxodata.png',
    'Viveris': 'viveris.svg',
    'Conseil départemental de la Haute-Garonne': 'haute-garonne.svg',
    'Mairie de Toulouse': 'mairie-toulouse.svg',
    'Région Occitanie': 'region-occitanie.png',
    'TVn7': 'tvn7.png',
    'CAn7': 'can7.png',
    'net7': 'net7.png',
    'photo7': 'photo7.png',
}

# The leaflet has room for the sponsors and the institutions only.
LEAFLET_PARTNER_GROUPS = ('Platine', 'Or', 'Argent', 'Bronze', 'Institutions')

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
# note were checked against capitoledulibre.org/lieu/ with the team.

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
     "prendra mal."),

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

# The leaflet is handed out at the event, so telling its reader to register
# is moot. It says instead what keeps the event free, and how to help.
LEAFLET_SUPPORT = (
    'C’est gratuit grâce à vous',
    "Le Capitole du Libre vit grâce à ses partenaires et à vos dons. Pour "
    "nous soutenir : faites un don, prenez un café à la buvette, ou un café "
    "soutien, un peu plus cher, dont la différence est un don, ou passez "
    "à la boutique.",
)

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
    "commencer, voilà quelques rendez-vous."
)

HIGHLIGHTS = [
    ('Bienvenue au', "L'ouverture : ce qui vous attend, en vingt minutes."),
    ('Concevoir un réseau informatique mondial',
     "La keynote du samedi, par Stéphane Bortzmeyer."),
    ('Dépendances numériques',
     "La dernière conférence du samedi dans le grand amphi."),
    ('Linux Tracing Escape Game',
     "Un escape game pour démasquer les anomalies d'un système."),
    ('Sauvegarder librement',
     "Deux heures pour repartir avec ses sauvegardes en place."),
    ('Conférence de clôture', "Le mot de la fin, dimanche en fin d'après-midi."),
]

# Highlights the leaflet leaves to the booklet, by the same title fragments.
LEAFLET_HIGHLIGHTS_LEFT_OUT = ('Linux Tracing Escape Game',
                               'Sauvegarder librement')


# --- the stand briefing -----------------------------------------------------
#
# One A4 handed to each stand when it sets up, the associations' and the
# sponsors' alike: hence no mention of the village associatif.

STAND_BRIEF_TITLE = 'Briefing stands'

STAND_BRIEF_LEDE = (
    "Merci d'être avec nous ce week-end ! L'essentiel pour votre stand, "
    "sur une page."
)

# What only the team knows. A field left as None prints as a blank line to
# fill in by hand, and the build warns about it. The wifi password is never
# written here, since this file is published: it is read from the
# environment, see STAND_BRIEF_SECRETS in standbrief.py.
STAND_BRIEF_FIELDS = {
    'Réseau wifi': 'wifinp',
    'Identifiant wifi': 'capitole',
    'Mot de passe wifi': None,
}

# Fixed points of the day the schedule export does not carry.
STAND_OPENING = '09:30'
STAND_COCKTAIL = '19:30'

# The network sits behind a captive portal, so a QR code could join the
# network but not log in: the credentials are printed instead.
STAND_WIFI_STEPS = (
    "Connectez-vous au réseau, puis saisissez l'identifiant et le mot de "
    "passe sur la page qui s'ouvre."
)

STAND_WIFI_NOTE = (
    "Réservé aux stands et aux ateliers. Merci de ne pas le communiquer aux "
    "visiteurs : il n'y a pas de réseau ouvert au public."
)

STAND_HELP = [
    "L'équipe porte un t-shirt rouge « STAFF » : arrêtez la première "
    "personne venue, elle saura qui appeler.",
    "L'accueil, au Hall C, répond aux questions et garde les objets trouvés "
    "pendant tout l'événement.",
    "Un comportement problématique : prévenez l'équipe, ou écrivez à "
    "conduite@capitoledulibre.org.",
    "Urgences : 15 (SAMU) · 17 (police) · 18 (pompiers) · 112.",
]

STAND_TIPS_TITLE = 'Pour orienter les visiteurs'

STAND_TIPS = [
    ('Le programme', "Le dépliant, et capitoledulibre.org/programme pour "
                     "les changements de dernière minute."),
    ('Manger', "Deux food trucks dans le parc le midi, buvette au Hall C."),
    ('Les enfants', "L'initiation au code, pour les 8-14 ans, le samedi au "
                    "bâtiment B."),
    ('Soutenir', "Un don, un café soutien à la buvette, ou un passage à "
                 "la boutique."),
    ('Accessibilité', "Tous les bâtiments, avec ascenseurs."),
    ('Le cocktail', "Samedi à 19h30 dans le hall principal, offert à tous, "
                    "exposants compris."),
]
