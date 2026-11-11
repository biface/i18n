import pytest

from i18n_tools import __version__
from i18n_tools.models import Message as MessageModel
from i18n_tools.models.book import Book
from i18n_tools.models.message import Declension, Message


@pytest.fixture
def fr_message():
    return MessageModel(
        id="1000",
        principal=Declension("Bonjour", ("Bonjour à tous", "Bonjour tout le monde")),
        variants=[
            Declension("Bonjour Mme {name}", ("Bonjour Mesdames", "Mesdames")),
            Declension("Bonjour M. {name}", ("Bonjour Messieurs", "Messieurs")),
        ],
        metadata={
            "version": __version__,
            "language": "fr-FR",
            "locations": [],
            "flags": ["python-format"],
            "user_comments": ["In French, Greeting message to one or more..."],
            "auto_comments": ["1000_000", "1000_001", "1000_02"],
        },
    )


@pytest.fixture
def en_message():
    return MessageModel(
        id="1000",
        principal=Declension("Hello", ("Hi everybody", "Hi everyone")),
        variants=[
            Declension("Hello {name}", ("Hi everybody", "Ladies")),
            Declension("Hello {name}", ("Hi everyone", "Gentlemen")),
        ],
        metadata={
            "version": __version__,
            "language": "en",
            "locations": [],
            "flags": ["python-format"],
            "user_comments": ["Greeting message to one or more..."],
            "auto_comments": ["1000_000", "1000_001", "1000_02"],
        },
    )


@pytest.fixture
def empty_message():
    return MessageModel(id="1000")


@pytest.fixture
def draft_message():
    """
    A message whose declensions have different segment counts.

    Matrix (rows = segments, columns = declensions)::

        Une fleur    | Une {flower} | Une {flower} rare
        Des fleurs   | ""           | Des {flower} rares
        Deux fleurs  | ""           | Deux {flower} rares
        ""           | ""           | Plusieurs {flower} rares
    """
    return Message(
        id="2000",
        principal=Declension("Une fleur", ("Des fleurs", "Deux fleurs")),
        variants=[
            Declension("Une {flower}"),
            Declension(
                "Une {flower} rare",
                (
                    "Des {flower} rares",
                    "Deux {flower} rares",
                    "Plusieurs {flower} rares",
                ),
            ),
        ],
        context="garden",
        metadata={"language": "fr-FR"},
    )


@pytest.fixture
def single_message():
    """A principal singular only."""
    return Message(id="2001", principal=Declension("Bonjour {name}"))


# --- Fixtures originally from test_01_book.py ---


@pytest.fixture
def fr_fr_messages():
    return {
        "1100": Message(
            id="1100",
            principal=Declension(
                "Voici une fleur", ("Voici des fleurs", "Voici deux fleurs")
            ),
            variants=[
                Declension(
                    "Voici une belle {flower}",
                    ("Voici de belles {flower}", "Voici deux belles {flower}"),
                ),
                Declension(
                    "Voici une {flower} rare",
                    (
                        "Voici des {flower} rares",
                        "Voici deux {flower} rares",
                        "Voici plusieurs {flower} rares",
                    ),
                ),
                Declension(
                    "Voici une {flower} de la région {region}",
                    (
                        "Voici des {flower} de la région {region}",
                        "Voici deux {flower} de la région {region}",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "fr-FR",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": ["Message sur les fleurs"],
            },
        ),
        "1101": Message(
            id="1101",
            principal=Declension(
                "J'aime cette montagne",
                ("J'aime ces montagnes", "J'aime ces deux montagnes"),
            ),
            variants=[
                Declension(
                    "J'aime cette montagne {mountain}",
                    (
                        "J'aime ces montagnes {mountain}",
                        "J'aime ces deux montagnes {mountain}",
                    ),
                ),
                Declension(
                    "J'aime cette montagne située à {location}",
                    (
                        "J'aime ces montagnes situées à {location}",
                        "J'aime ces deux montagnes situées à {location}",
                    ),
                ),
                Declension(
                    "J'aime cette montagne appelée {name}",
                    (
                        "J'aime ces montagnes appelées {name}",
                        "J'aime ces deux montagnes appelées {name}",
                        "J'aime ces nombreuses montagnes appelées {name}",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "fr-FR",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": ["Message sur les montagnes"],
            },
        ),
        "1102": Message(
            id="1102",
            principal=Declension(
                "Je pars en voyage", ("Je pars en voyages", "Je pars en deux voyages")
            ),
            variants=[
                Declension(
                    "Je pars en voyage à {destination}",
                    (
                        "Je pars en voyages à {destination}",
                        "Je pars en deux voyages à {destination}",
                    ),
                ),
                Declension(
                    "Je pars en voyage avec {companion}",
                    (
                        "Je pars en voyages avec {companion}",
                        "Je pars en deux voyages avec {companion}",
                    ),
                ),
                Declension(
                    "Je pars en voyage pour {duration} jours",
                    (
                        "Je pars en voyages pour {duration} jours",
                        "Je pars en deux voyages pour {duration} jours",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "fr-FR",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": ["Message sur les voyages"],
            },
        ),
        "1103": Message(
            id="1103",
            principal=Declension(
                "L'automate est prêt",
                ("Les automates sont prêts", "Les deux automates sont prêts"),
            ),
            variants=[
                Declension(
                    "L'automate {automaton} est prêt",
                    (
                        "Les automates {automaton} sont prêts",
                        "Les deux automates {automaton} sont prêts",
                    ),
                ),
                Declension(
                    "L'automate conçu pour {purpose} est prêt",
                    (
                        "Les automates conçus pour {purpose} sont prêts",
                        "Les deux automates conçus pour {purpose} sont prêts",
                    ),
                ),
                Declension(
                    "L'automate de type {type} est prêt",
                    (
                        "Les automates de type {type} sont prêts",
                        "Les deux automates de type {type} sont prêts",
                        "Les nombreux automates de type {type} sont prêts",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "fr-FR",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": [
                    "Message sur les automates basés sur les grammaires de Chomsky"
                ],
            },
        ),
        "1104": Message(
            id="1104",
            principal=Declension(
                "Le fleur a une belle couleur",
                (
                    "Les fleurs ont de belles couleurs",
                    "Les deux fleurs ont de belles couleurs",
                ),
            ),
            variants=[
                Declension(
                    "La {flower} a une belle couleur",
                    (
                        "Les {flower} ont de belles couleurs",
                        "Les deux {flower} ont de belles couleurs",
                    ),
                ),
                Declension(
                    "La {flower} de couleur {color} est magnifique",
                    (
                        "Les {flower} de couleur {color} sont magnifiques",
                        "Les deux {flower} de couleur {color} sont magnifiques",
                    ),
                ),
                Declension(
                    "La {flower} de l'année {year} est splendide",
                    (
                        "Les {flower} de l'année {year} sont splendides",
                        "Les deux {flower} de l'année {year} sont splendides",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "fr-FR",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": ["Message sur les fleurs"],
            },
        ),
        "1105": Message(
            id="1105",
            principal=Declension(
                "La montagne est couverte de neige",
                (
                    "Les montagnes sont couvertes de neige",
                    "Les deux montagnes sont couvertes de neige",
                ),
            ),
            variants=[
                Declension(
                    "La montagne {mountain} est couverte de neige",
                    (
                        "Les montagnes {mountain} sont couvertes de neige",
                        "Les deux montagnes {mountain} sont couvertes de neige",
                    ),
                ),
                Declension(
                    "La montagne située à {location} est couverte de neige",
                    (
                        "Les montagnes situées à {location} sont couvertes de neige",
                        "Les deux montagnes situées à {location} sont couvertes de neige",
                    ),
                ),
                Declension(
                    "La montagne en {season} est couverte de neige",
                    (
                        "Les montagnes en {season} sont couvertes de neige",
                        "Les deux montagnes en {season} sont couvertes de neige",
                        "Les nombreuses montagnes en {season} sont couvertes de neige",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "fr-FR",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": ["Message sur les montagnes"],
            },
        ),
        "1106": Message(
            id="1106",
            principal=Declension(
                "Le voyage est long",
                ("Les voyages sont longs", "Ces deux voyages sont longs"),
            ),
            variants=[
                Declension(
                    "Le voyage vers {destination} est long",
                    (
                        "Les voyages vers {destination} sont longs",
                        "Ces deux voyages vers {destination} sont longs",
                    ),
                ),
                Declension(
                    "Le voyage avec {companion} est long",
                    (
                        "Les voyages avec {companion} sont longs",
                        "Ces deux voyages avec {companion} sont longs",
                    ),
                ),
                Declension(
                    "Le voyage de {duration} jours est long",
                    (
                        "Les voyages de {duration} jours sont longs",
                        "Ces deux voyages de {duration} jours sont longs",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "fr-FR",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": ["Message sur les voyages"],
            },
        ),
        "1107": Message(
            id="1107",
            principal=Declension(
                "L'automate fonctionne",
                ("Les automates fonctionnent", "Les deux automates fonctionnent"),
            ),
            variants=[
                Declension(
                    "L'automate {automaton} fonctionne",
                    (
                        "Les automates {automaton} fonctionnent",
                        "Les deux automates {automaton} fonctionnent",
                    ),
                ),
                Declension(
                    "L'automate pour {purpose} fonctionne",
                    (
                        "Les automates pour {purpose} fonctionnent",
                        "Les deux automates pour {purpose} fonctionnent",
                    ),
                ),
                Declension(
                    "L'automate de type {type} fonctionne",
                    (
                        "Les automates de type {type} fonctionnent",
                        "Les deux automates de type {type} fonctionnent",
                        "Les nombreux automates de type {type} fonctionnent",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "fr-FR",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": [
                    "Message sur les automates basés sur les grammaires de Chomsky"
                ],
            },
        ),
        "1108": Message(
            id="1108",
            principal=Declension(
                "Le fleur sent bon",
                ("Les fleurs sentent bon", "Ces deux fleurs sentent bon"),
            ),
            variants=[
                Declension(
                    "La {flower} sent bon",
                    ("Les {flower} sentent bon", "Ces deux {flower} sentent bon"),
                ),
                Declension(
                    "La {flower} de couleur {color} sent bon",
                    (
                        "Les {flower} de couleur {color} sentent bon",
                        "Ces deux {flower} de couleur {color} sentent bon",
                    ),
                ),
                Declension(
                    "La {flower} cultivée en {year} sent bon",
                    (
                        "Les {flower} cultivées en {year} sentent bon",
                        "Ces deux {flower} cultivées en {year} sentent bon",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "fr-FR",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": ["Message sur les fleurs"],
            },
        ),
        "1109": Message(
            id="1109",
            principal=Declension(
                "La montagne est enneigée",
                ("Les montagnes sont enneigées", "Ces deux montagnes sont enneigées"),
            ),
            variants=[
                Declension(
                    "La montagne {mountain} est enneigée",
                    (
                        "Les montagnes {mountain} sont enneigées",
                        "Ces deux montagnes {mountain} sont enneigées",
                    ),
                ),
                Declension(
                    "La montagne située à {location} est enneigée",
                    (
                        "Les montagnes situées à {location} sont enneigées",
                        "Ces deux montagnes situées à {location} sont enneigées",
                    ),
                ),
                Declension(
                    "La montagne en {season} est enneigée",
                    (
                        "Les montagnes en {season} sont enneigées",
                        "Ces deux montagnes en {season} sont enneigées",
                        "Les nombreuses montagnes en {season} sont enneigées",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "fr-FR",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": ["Message sur les montagnes"],
            },
        ),
    }


@pytest.fixture
def en_us_messages():
    return {
        "1100": Message(
            id="1100",
            principal=Declension(
                "Here is a flower", ("Here are flowers", "Here are two flowers")
            ),
            variants=[
                Declension(
                    "Here is a beautiful {flower}",
                    ("Here are beautiful {flower}", "Here are two beautiful {flower}"),
                ),
                Declension(
                    "Here is a rare {flower}",
                    (
                        "Here are rare {flower}",
                        "Here are two rare {flower}",
                        "Here are several rare {flower}",
                    ),
                ),
                Declension(
                    "Here is a {flower} from the {region} region",
                    (
                        "Here are {flower} from the {region} region",
                        "Here are two {flower} from the {region} region",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "en-US",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": ["Message about flowers"],
            },
        ),
        "1101": Message(
            id="1101",
            principal=Declension(
                "I like this mountain",
                ("I like these mountains", "I like these two mountains"),
            ),
            variants=[
                Declension(
                    "I like this mountain {mountain}",
                    (
                        "I like these mountains {mountain}",
                        "I like these two mountains {mountain}",
                    ),
                ),
                Declension(
                    "I like this mountain located at {location}",
                    (
                        "I like these mountains located at {location}",
                        "I like these two mountains located at {location}",
                    ),
                ),
                Declension(
                    "I like this mountain called {name}",
                    (
                        "I like these mountains called {name}",
                        "I like these two mountains called {name}",
                        "I like these numerous mountains called {name}",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "en-US",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": ["Message about mountains"],
            },
        ),
        "1102": Message(
            id="1102",
            principal=Declension(
                "I'm going on a trip", ("I'm going on trips", "I'm going on two trips")
            ),
            variants=[
                Declension(
                    "I'm going on a trip to {destination}",
                    (
                        "I'm going on trips to {destination}",
                        "I'm going on two trips to {destination}",
                    ),
                ),
                Declension(
                    "I'm going on a trip with {companion}",
                    (
                        "I'm going on trips with {companion}",
                        "I'm going on two trips with {companion}",
                    ),
                ),
                Declension(
                    "I'm going on a trip for {duration} days",
                    (
                        "I'm going on trips for {duration} days",
                        "I'm going on two trips for {duration} days",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "en-US",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": ["Message about trips"],
            },
        ),
        "1103": Message(
            id="1103",
            principal=Declension(
                "The automaton is ready",
                ("The automatons are ready", "The two automatons are ready"),
            ),
            variants=[
                Declension(
                    "The automaton {automaton} is ready",
                    (
                        "The automatons {automaton} are ready",
                        "The two automatons {automaton} are ready",
                    ),
                ),
                Declension(
                    "The automaton designed for {purpose} is ready",
                    (
                        "The automatons designed for {purpose} are ready",
                        "The two automatons designed for {purpose} are ready",
                    ),
                ),
                Declension(
                    "The automaton of type {type} is ready",
                    (
                        "The automatons of type {type} are ready",
                        "The two automatons of type {type} are ready",
                        "The numerous automatons of type {type} are ready",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "en-US",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": ["Message about automata based on Chomsky grammars"],
            },
        ),
        "1104": Message(
            id="1104",
            principal=Declension(
                "The flower has a beautiful color",
                (
                    "Flowers have beautiful colors",
                    "The two flowers have beautiful colors",
                ),
            ),
            variants=[
                Declension(
                    "The {flower} has a beautiful color",
                    (
                        "The {flower} have beautiful colors",
                        "The two {flower} have beautiful colors",
                    ),
                ),
                Declension(
                    "The {flower} of color {color} is magnificent",
                    (
                        "The {flower} of color {color} are magnificent",
                        "The two {flower} of color {color} are magnificent",
                    ),
                ),
                Declension(
                    "The {flower} of the year {year} is splendid",
                    (
                        "The {flower} of the year {year} are splendid",
                        "The two {flower} of the year {year} are splendid",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "en-US",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": ["Message about flowers"],
            },
        ),
        "1105": Message(
            id="1105",
            principal=Declension(
                "The mountain is snow-covered",
                (
                    "The mountains are snow-covered",
                    "These two mountains are snow-covered",
                ),
            ),
            variants=[
                Declension(
                    "The mountain {mountain} is snow-covered",
                    (
                        "The mountains {mountain} are snow-covered",
                        "These two mountains {mountain} are snow-covered",
                    ),
                ),
                Declension(
                    "The mountain located at {location} is snow-covered",
                    (
                        "The mountains located at {location} are snow-covered",
                        "These two mountains located at {location} are snow-covered",
                    ),
                ),
                Declension(
                    "The mountain in {season} is snow-covered",
                    (
                        "The mountains in {season} are snow-covered",
                        "These two mountains in {season} are snow-covered",
                        "The numerous mountains in {season} are snow-covered",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "en-US",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": ["Message about mountains"],
            },
        ),
        "1106": Message(
            id="1106",
            principal=Declension(
                "The trip is long", ("Trips are long", "These two trips are long")
            ),
            variants=[
                Declension(
                    "The trip to {destination} is long",
                    (
                        "Trips to {destination} are long",
                        "These two trips to {destination} are long",
                    ),
                ),
                Declension(
                    "The trip with {companion} is long",
                    (
                        "Trips with {companion} are long",
                        "These two trips with {companion} are long",
                    ),
                ),
                Declension(
                    "The trip of {duration} days is long",
                    (
                        "Trips of {duration} days are long",
                        "These two trips of {duration} days are long",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "en-US",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": ["Message about trips"],
            },
        ),
        "1107": Message(
            id="1107",
            principal=Declension(
                "The automaton works",
                ("The automatons work", "The two automatons work"),
            ),
            variants=[
                Declension(
                    "The automaton {automaton} works",
                    (
                        "The automatons {automaton} work",
                        "The two automatons {automaton} work",
                    ),
                ),
                Declension(
                    "The automaton for {purpose} works",
                    (
                        "The automatons for {purpose} work",
                        "The two automatons for {purpose} work",
                    ),
                ),
                Declension(
                    "The automaton of type {type} works",
                    (
                        "The automatons of type {type} work",
                        "The two automatons of type {type} work",
                        "The numerous automatons of type {type} work",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "en-US",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": ["Message about automata based on Chomsky grammars"],
            },
        ),
        "1108": Message(
            id="1108",
            principal=Declension(
                "The flower smells good",
                ("Flowers smell good", "These two flowers smell good"),
            ),
            variants=[
                Declension(
                    "The {flower} smells good",
                    ("The {flower} smell good", "These two {flower} smell good"),
                ),
                Declension(
                    "The {flower} of color {color} smells good",
                    (
                        "The {flower} of color {color} smell good",
                        "These two {flower} of color {color} smell good",
                    ),
                ),
                Declension(
                    "The {flower} cultivated in {year} smells good",
                    (
                        "The {flower} cultivated in {year} smell good",
                        "These two {flower} cultivated in {year} smell good",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "en-US",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": ["Message about flowers"],
            },
        ),
        "1109": Message(
            id="1109",
            principal=Declension(
                "The mountain is snowy",
                ("The mountains are snowy", "These two mountains are snowy"),
            ),
            variants=[
                Declension(
                    "The mountain {mountain} is snowy",
                    (
                        "The mountains {mountain} are snowy",
                        "These two mountains {mountain} are snowy",
                    ),
                ),
                Declension(
                    "The mountain located at {location} is snowy",
                    (
                        "The mountains located at {location} are snowy",
                        "These two mountains located at {location} are snowy",
                    ),
                ),
                Declension(
                    "The mountain in {season} is snowy",
                    (
                        "The mountains in {season} are snowy",
                        "These two mountains in {season} are snowy",
                        "The numerous mountains in {season} are snowy",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "en-US",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": ["Message about mountains"],
            },
        ),
    }


@pytest.fixture
def en_gb_messages():
    return {
        "1100": Message(
            id="1100",
            principal=Declension(
                "Here is a flower", ("Here are flowers", "Here are two flowers")
            ),
            variants=[
                Declension(
                    "Here is a beautiful {flower}",
                    ("Here are beautiful {flower}", "Here are two beautiful {flower}"),
                ),
                Declension(
                    "Here is a rare {flower}",
                    (
                        "Here are rare {flower}",
                        "Here are two rare {flower}",
                        "Here are several rare {flower}",
                    ),
                ),
                Declension(
                    "Here is a {flower} from the {region} region",
                    (
                        "Here are {flower} from the {region} region",
                        "Here are two {flower} from the {region} region",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "en-GB",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": ["Message about flowers"],
            },
        ),
        "1101": Message(
            id="1101",
            principal=Declension(
                "I like this mountain",
                ("I like these mountains", "I like these two mountains"),
            ),
            variants=[
                Declension(
                    "I like this mountain {mountain}",
                    (
                        "I like these mountains {mountain}",
                        "I like these two mountains {mountain}",
                    ),
                ),
                Declension(
                    "I like this mountain located at {location}",
                    (
                        "I like these mountains located at {location}",
                        "I like these two mountains located at {location}",
                    ),
                ),
                Declension(
                    "I like this mountain called {name}",
                    (
                        "I like these mountains called {name}",
                        "I like these two mountains called {name}",
                        "I like these numerous mountains called {name}",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "en-GB",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": ["Message about mountains"],
            },
        ),
        "1102": Message(
            id="1102",
            principal=Declension(
                "I'm going on a trip", ("I'm going on trips", "I'm going on two trips")
            ),
            variants=[
                Declension(
                    "I'm going on a trip to {destination}",
                    (
                        "I'm going on trips to {destination}",
                        "I'm going on two trips to {destination}",
                    ),
                ),
                Declension(
                    "I'm going on a trip with {companion}",
                    (
                        "I'm going on trips with {companion}",
                        "I'm going on two trips with {companion}",
                    ),
                ),
                Declension(
                    "I'm going on a trip for {duration} days",
                    (
                        "I'm going on trips for {duration} days",
                        "I'm going on two trips for {duration} days",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "en-GB",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": ["Message about trips"],
            },
        ),
        "1103": Message(
            id="1103",
            principal=Declension(
                "The automaton is ready",
                ("The automatons are ready", "The two automatons are ready"),
            ),
            variants=[
                Declension(
                    "The automaton {automaton} is ready",
                    (
                        "The automatons {automaton} are ready",
                        "The two automatons {automaton} are ready",
                    ),
                ),
                Declension(
                    "The automaton designed for {purpose} is ready",
                    (
                        "The automatons designed for {purpose} are ready",
                        "The two automatons designed for {purpose} are ready",
                    ),
                ),
                Declension(
                    "The automaton of type {type} is ready",
                    (
                        "The automatons of type {type} are ready",
                        "The two automatons of type {type} are ready",
                        "The numerous automatons of type {type} are ready",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "en-GB",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": ["Message about automata based on Chomsky grammars"],
            },
        ),
        "1104": Message(
            id="1104",
            principal=Declension(
                "The flower has a beautiful colour",
                (
                    "Flowers have beautiful colours",
                    "The two flowers have beautiful colours",
                ),
            ),
            variants=[
                Declension(
                    "The {flower} has a beautiful colour",
                    (
                        "The {flower} have beautiful colours",
                        "The two {flower} have beautiful colours",
                    ),
                ),
                Declension(
                    "The {flower} of colour {color} is magnificent",
                    (
                        "The {flower} of colour {color} are magnificent",
                        "The two {flower} of colour {color} are magnificent",
                    ),
                ),
                Declension(
                    "The {flower} of the year {year} is splendid",
                    (
                        "The {flower} of the year {year} are splendid",
                        "The two {flower} of the year {year} are splendid",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "en-GB",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": ["Message about flowers"],
            },
        ),
        "1105": Message(
            id="1105",
            principal=Declension(
                "The mountain is snow-covered",
                (
                    "The mountains are snow-covered",
                    "These two mountains are snow-covered",
                ),
            ),
            variants=[
                Declension(
                    "The mountain {mountain} is snow-covered",
                    (
                        "The mountains {mountain} are snow-covered",
                        "These two mountains {mountain} are snow-covered",
                    ),
                ),
                Declension(
                    "The mountain located at {location} is snow-covered",
                    (
                        "The mountains located at {location} are snow-covered",
                        "These two mountains located at {location} are snow-covered",
                    ),
                ),
                Declension(
                    "The mountain in {season} is snow-covered",
                    (
                        "The mountains in {season} are snow-covered",
                        "These two mountains in {season} are snow-covered",
                        "The numerous mountains in {season} are snow-covered",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "en-GB",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": ["Message about mountains"],
            },
        ),
        "1106": Message(
            id="1106",
            principal=Declension(
                "The trip is long", ("Trips are long", "These two trips are long")
            ),
            variants=[
                Declension(
                    "The trip to {destination} is long",
                    (
                        "Trips to {destination} are long",
                        "These two trips to {destination} are long",
                    ),
                ),
                Declension(
                    "The trip with {companion} is long",
                    (
                        "Trips with {companion} are long",
                        "These two trips with {companion} are long",
                    ),
                ),
                Declension(
                    "The trip of {duration} days is long",
                    (
                        "Trips of {duration} days are long",
                        "These two trips of {duration} days are long",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "en-GB",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": ["Message about trips"],
            },
        ),
        "1107": Message(
            id="1107",
            principal=Declension(
                "The automaton works",
                ("The automatons work", "The two automatons work"),
            ),
            variants=[
                Declension(
                    "The automaton {automaton} works",
                    (
                        "The automatons {automaton} work",
                        "The two automatons {automaton} work",
                    ),
                ),
                Declension(
                    "The automaton for {purpose} works",
                    (
                        "The automatons for {purpose} work",
                        "The two automatons for {purpose} work",
                    ),
                ),
                Declension(
                    "The automaton of type {type} works",
                    (
                        "The automatons of type {type} work",
                        "The two automatons of type {type} work",
                        "The numerous automatons of type {type} work",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "en-GB",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": ["Message about automata based on Chomsky grammars"],
            },
        ),
        "1108": Message(
            id="1108",
            principal=Declension(
                "The flower smells nice",
                ("The flowers smell nice", "These two flowers smell nice"),
            ),
            variants=[
                Declension(
                    "The {flower} smells nice",
                    ("The {flower} smell nice", "These two {flower} smell nice"),
                ),
                Declension(
                    "The {flower} of colour {color} smells nice",
                    (
                        "The {flower} of colour {color} smell nice",
                        "These two {flower} of colour {color} smell nice",
                    ),
                ),
                Declension(
                    "The {flower} cultivated in {year} smells nice",
                    (
                        "The {flower} cultivated in {year} smell nice",
                        "These two {flower} cultivated in {year} smell nice",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "en-GB",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": ["Message about flowers"],
            },
        ),
        "1109": Message(
            id="1109",
            principal=Declension(
                "The mountain is covered with snow",
                (
                    "The mountains are covered with snow",
                    "These two mountains are covered with snow",
                ),
            ),
            variants=[
                Declension(
                    "The mountain {mountain} is covered with snow",
                    (
                        "The mountains {mountain} are covered with snow",
                        "These two mountains {mountain} are covered with snow",
                    ),
                ),
                Declension(
                    "The mountain located at {location} is covered with snow",
                    (
                        "The mountains located at {location} are covered with snow",
                        "These two mountains located at {location} are covered with snow",
                    ),
                ),
                Declension(
                    "The mountain in {season} is covered with snow",
                    (
                        "The mountains in {season} are covered with snow",
                        "These two mountains in {season} are covered with snow",
                        "The numerous mountains in {season} are covered with snow",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "en-GB",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": ["Message about mountains"],
            },
        ),
    }


@pytest.fixture
def it_it_messages():
    return {
        "1100": Message(
            id="1100",
            principal=Declension("Ecco un fiore", ("Ecco dei fiori", "Ecco due fiori")),
            variants=[
                Declension(
                    "Ecco un bellissimo {flower}",
                    ("Ecco dei bellissimi {flower}", "Ecco due bellissimi {flower}"),
                ),
                Declension(
                    "Ecco un raro {flower}",
                    (
                        "Ecco dei {flower} rari",
                        "Ecco due {flower} rari",
                        "Ecco diversi {flower} rari",
                    ),
                ),
                Declension(
                    "Ecco un {flower} della regione {region}",
                    (
                        "Ecco dei {flower} della regione {region}",
                        "Ecco due {flower} della regione {region}",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "it-IT",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": ["Messaggio sui fiori"],
            },
        ),
        "1101": Message(
            id="1101",
            principal=Declension(
                "Mi piace questa montagna",
                ("Mi piacciono queste montagne", "Mi piacciono queste due montagne"),
            ),
            variants=[
                Declension(
                    "Mi piace questa montagna {mountain}",
                    (
                        "Mi piacciono queste montagne {mountain}",
                        "Mi piacciono queste due montagne {mountain}",
                    ),
                ),
                Declension(
                    "Mi piace questa montagna situata a {location}",
                    (
                        "Mi piacciono queste montagne situate a {location}",
                        "Mi piacciono queste due montagne situate a {location}",
                    ),
                ),
                Declension(
                    "Mi piace questa montagna chiamata {name}",
                    (
                        "Mi piacciono queste montagne chiamate {name}",
                        "Mi piacciono queste due montagne chiamate {name}",
                        "Mi piacciono queste numerose montagne chiamate {name}",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "it-IT",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": ["Messaggio sulle montagne"],
            },
        ),
        "1102": Message(
            id="1102",
            principal=Declension(
                "Parto per un viaggio", ("Parto per dei viaggi", "Parto per due viaggi")
            ),
            variants=[
                Declension(
                    "Parto per un viaggio verso {destination}",
                    (
                        "Parto per dei viaggi verso {destination}",
                        "Parto per due viaggi verso {destination}",
                    ),
                ),
                Declension(
                    "Parto per un viaggio con {companion}",
                    (
                        "Parto per dei viaggi con {companion}",
                        "Parto per due viaggi con {companion}",
                    ),
                ),
                Declension(
                    "Parto per un viaggio di {duration} giorni",
                    (
                        "Parto per dei viaggi di {duration} giorni",
                        "Parto per due viaggi di {duration} giorni",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "it-IT",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": ["Messaggio sui viaggi"],
            },
        ),
        "1103": Message(
            id="1103",
            principal=Declension(
                "L'automata è pronto",
                ("Gli automi sono pronti", "I due automi sono pronti"),
            ),
            variants=[
                Declension(
                    "L'automata {automaton} è pronto",
                    (
                        "Gli automi {automaton} sono pronti",
                        "I due automi {automaton} sono pronti",
                    ),
                ),
                Declension(
                    "L'automata progettato per {purpose} è pronto",
                    (
                        "Gli automi progettati per {purpose} sono pronti",
                        "I due automi progettati per {purpose} sono pronti",
                    ),
                ),
                Declension(
                    "L'automata di tipo {type} è pronto",
                    (
                        "Gli automi di tipo {type} sono pronti",
                        "I due automi di tipo {type} sono pronti",
                        "I numerosi automi di tipo {type} sono pronti",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "it-IT",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": [
                    "Messaggio sugli automi basati sulle grammatiche di Chomsky"
                ],
            },
        ),
        "1104": Message(
            id="1104",
            principal=Declension(
                "Il fiore ha un bel colore",
                ("I fiori hanno bei colori", "I due fiori hanno bei colori"),
            ),
            variants=[
                Declension(
                    "Il {flower} ha un bel colore",
                    ("I {flower} hanno bei colori", "I due {flower} hanno bei colori"),
                ),
                Declension(
                    "Il {flower} di colore {color} è magnifico",
                    (
                        "I {flower} di colore {color} sono magnifici",
                        "I due {flower} di colore {color} sono magnifici",
                    ),
                ),
                Declension(
                    "Il {flower} dell'anno {year} è splendido",
                    (
                        "I {flower} dell'anno {year} sono splendidi",
                        "I due {flower} dell'anno {year} sono splendidi",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "it-IT",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": ["Messaggio sui fiori"],
            },
        ),
        "1105": Message(
            id="1105",
            principal=Declension(
                "La montagna è ricoperta di neve",
                (
                    "Le montagne sono ricoperte di neve",
                    "Queste due montagne sono ricoperte di neve",
                ),
            ),
            variants=[
                Declension(
                    "La montagna {mountain} è ricoperta di neve",
                    (
                        "Le montagne {mountain} sono ricoperte di neve",
                        "Queste due montagne {mountain} sono ricoperte di neve",
                    ),
                ),
                Declension(
                    "La montagna situata a {location} è ricoperta di neve",
                    (
                        "Le montagne situate a {location} sono ricoperte di neve",
                        "Queste due montagne situate a {location} sono ricoperte di neve",
                    ),
                ),
                Declension(
                    "La montagna in {season} è ricoperta di neve",
                    (
                        "Le montagne in {season} sono ricoperte di neve",
                        "Queste due montagne in {season} sono ricoperte di neve",
                        "Le numerose montagne in {season} sono ricoperte di neve",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "it-IT",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": ["Messaggio sulle montagne"],
            },
        ),
        "1106": Message(
            id="1106",
            principal=Declension(
                "Il viaggio è lungo",
                ("I viaggi sono lunghi", "Questi due viaggi sono lunghi"),
            ),
            variants=[
                Declension(
                    "Il viaggio verso {destination} è lungo",
                    (
                        "I viaggi verso {destination} sono lunghi",
                        "Questi due viaggi verso {destination} sono lunghi",
                    ),
                ),
                Declension(
                    "Il viaggio con {companion} è lungo",
                    (
                        "I viaggi con {companion} sono lunghi",
                        "Questi due viaggi con {companion} sono lunghi",
                    ),
                ),
                Declension(
                    "Il viaggio di {duration} giorni è lungo",
                    (
                        "I viaggi di {duration} giorni sono lunghi",
                        "Questi due viaggi di {duration} giorni sono lunghi",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "it-IT",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": ["Messaggio sui viaggi"],
            },
        ),
        "1107": Message(
            id="1107",
            principal=Declension(
                "L'automata funziona",
                ("Gli automi funzionano", "I due automi funzionano"),
            ),
            variants=[
                Declension(
                    "L'automata {automaton} funziona",
                    (
                        "Gli automi {automaton} funzionano",
                        "I due automi {automaton} funzionano",
                    ),
                ),
                Declension(
                    "L'automata per {purpose} funziona",
                    (
                        "Gli automi per {purpose} funzionano",
                        "I due automi per {purpose} funzionano",
                    ),
                ),
                Declension(
                    "L'automata di tipo {type} funziona",
                    (
                        "Gli automi di tipo {type} funzionano",
                        "I due automi di tipo {type} funzionano",
                        "I numerosi automi di tipo {type} funzionano",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "it-IT",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": [
                    "Messaggio sugli automi basati sulle grammatiche di Chomsky"
                ],
            },
        ),
        "1108": Message(
            id="1108",
            principal=Declension(
                "Il fiore profuma bene",
                ("I fiori profumano bene", "Questi due fiori profumano bene"),
            ),
            variants=[
                Declension(
                    "Il {flower} profuma bene",
                    ("I {flower} profumano bene", "Questi due {flower} profumano bene"),
                ),
                Declension(
                    "Il {flower} di colore {color} profuma bene",
                    (
                        "I {flower} di colore {color} profumano bene",
                        "Questi due {flower} di colore {color} profumano bene",
                    ),
                ),
                Declension(
                    "Il {flower} coltivato nel {year} profuma bene",
                    (
                        "I {flower} coltivati nel {year} profumano bene",
                        "Questi due {flower} coltivati nel {year} profumano bene",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "it-IT",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": ["Messaggio sui fiori"],
            },
        ),
        "1109": Message(
            id="1109",
            principal=Declension(
                "La montagna è innevata",
                ("Le montagne sono innevate", "Queste due montagne sono innevate"),
            ),
            variants=[
                Declension(
                    "La montagna {mountain} è innevata",
                    (
                        "Le montagne {mountain} sono innevate",
                        "Queste due montagne {mountain} sono innevate",
                    ),
                ),
                Declension(
                    "La montagna situata a {location} è innevata",
                    (
                        "Le montagne situate a {location} sono innevate",
                        "Queste due montagne situate a {location} sono innevate",
                    ),
                ),
                Declension(
                    "La montagna in {season} è innevata",
                    (
                        "Le montagne in {season} sono innevate",
                        "Queste due montagne in {season} sono innevate",
                        "Le numerose montagne in {season} sono innevate",
                    ),
                ),
            ],
            metadata={
                "version": __version__,
                "language": "it-IT",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": ["Messaggio sulle montagne"],
            },
        ),
    }


@pytest.fixture()
def fr_fr_book(fr_fr_messages):
    return Book(list(fr_fr_messages.values()), domain="test", language="fr-FR")


@pytest.fixture()
def en_us_book(en_us_messages):
    return Book(list(en_us_messages.values()), domain="test", language="en-US")


@pytest.fixture()
def en_gb_book(en_gb_messages):
    return Book(list(en_gb_messages.values()), domain="test", language="en-GB")


@pytest.fixture()
def it_it_book(it_it_messages):
    return Book(list(it_it_messages.values()), domain="test", language="it-IT")
