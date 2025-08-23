import pytest

from i18n_tools.models import Message as MessageModel
from i18n_tools.models.corpus import Book, Message

# Shared fixtures for models tests (Message and Book)
# These fixtures were previously defined inside test_00_message.py and test_01_book.py
# Consolidating them here allows reuse across tests in this directory and works with the root tests/conftest.py.


# Compatibility: some tests import `from conftest import conf_tests, tmp_module_repository`.
# When Python resolves the module name `conftest` to this file, ensure those names exist
# so the import does not fail. They are not used as fixtures here.
conf_tests = None
tmp_module_repository = None


# --- Fixtures originally from test_00_message.py ---


@pytest.fixture
def fr_message():
    return MessageModel(
        id="1000",
        default="Bonjour",
        options={
            1: "Bonjour Mme {name}",
            2: "Bonjour M. {name}",
        },
        default_plurals={1: "Bonjour à tous", 2: "Bonjour tout le monde"},
        options_plurals={
            1: {1: "Bonjour Mesdames", 2: "Mesdames"},
            2: {1: "Bonjour Messieurs", 2: "Messieurs"},
        },
        metadata={
            "version": "0.1.0",
            "language": "fr-FR",
            "location": [],
            "flags": ["python-format"],
            "comments": "In French, Greeting message to one or more...",
            "count": {"singular": 0, "plurals": []},
        },
    )


@pytest.fixture
def en_message():
    return MessageModel(
        id="1000",
        default="Hello",
        options={
            1: "Hello {name}",
            2: "Hello {name}",
        },
        default_plurals={1: "Hi everybody", 2: "Hi everyone"},
        options_plurals={
            1: {1: "Hi everybody", 2: "Ladies"},
            2: {1: "Hi everyone", 2: "Gentlemen"},
        },
        metadata={
            "version": "0.1.0",
            "language": "en",
            "location": [],
            "flags": ["python-format"],
            "comments": "Greeting message to one or more...",
            "count": {"singular": 0, "plurals": []},
        },
    )


@pytest.fixture
def empty_message():
    return MessageModel(id="1000", default="")


@pytest.fixture(scope="module")
def empty_module_message():
    return MessageModel(
        id="1000",
        default="",
    )


# --- Fixtures originally from test_01_book.py ---


@pytest.fixture
def fr_fr_messages():
    return {
        "1100": Message(
            id="1100",
            default="Voici une fleur",
            options={
                1: "Voici une belle {flower}",
                2: "Voici une {flower} rare",
                3: "Voici une {flower} de la région {region}",
            },
            default_plurals={
                1: "Voici des fleurs",
                2: "Voici deux fleurs",
            },
            options_plurals={
                1: {1: "Voici de belles {flower}", 2: "Voici deux belles {flower}"},
                2: {
                    1: "Voici des {flower} rares",
                    2: "Voici deux {flower} rares",
                    3: "Voici plusieurs {flower} rares",
                },
                3: {
                    1: "Voici des {flower} de la région {region}",
                    2: "Voici deux {flower} de la région {region}",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "fr-FR",
                "location": [],
                "flags": ["python-format"],
                "comments": "Message sur les fleurs",
                "count": {"singular": 3, "plurals": [2, 3, 2]},
            },
        ),
        "1101": Message(
            id="1101",
            default="J'aime cette montagne",
            options={
                1: "J'aime cette montagne {mountain}",
                2: "J'aime cette montagne située à {location}",
                3: "J'aime cette montagne appelée {name}",
            },
            default_plurals={
                1: "J'aime ces montagnes",
                2: "J'aime ces deux montagnes",
            },
            options_plurals={
                1: {
                    1: "J'aime ces montagnes {mountain}",
                    2: "J'aime ces deux montagnes {mountain}",
                },
                2: {
                    1: "J'aime ces montagnes situées à {location}",
                    2: "J'aime ces deux montagnes situées à {location}",
                },
                3: {
                    1: "J'aime ces montagnes appelées {name}",
                    2: "J'aime ces deux montagnes appelées {name}",
                    3: "J'aime ces nombreuses montagnes appelées {name}",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "fr-FR",
                "location": [],
                "flags": ["python-format"],
                "comments": "Message sur les montagnes",
                "count": {"singular": 3, "plurals": [2, 2, 3]},
            },
        ),
        "1102": Message(
            id="1102",
            default="Je pars en voyage",
            options={
                1: "Je pars en voyage à {destination}",
                2: "Je pars en voyage avec {companion}",
                3: "Je pars en voyage pour {duration} jours",
            },
            default_plurals={
                1: "Je pars en voyages",
                2: "Je pars en deux voyages",
            },
            options_plurals={
                1: {
                    1: "Je pars en voyages à {destination}",
                    2: "Je pars en deux voyages à {destination}",
                },
                2: {
                    1: "Je pars en voyages avec {companion}",
                    2: "Je pars en deux voyages avec {companion}",
                },
                3: {
                    1: "Je pars en voyages pour {duration} jours",
                    2: "Je pars en deux voyages pour {duration} jours",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "fr-FR",
                "location": [],
                "flags": ["python-format"],
                "comments": "Message sur les voyages",
                "count": {"singular": 3, "plurals": [2, 2, 2]},
            },
        ),
        "1103": Message(
            id="1103",
            default="L'automate est prêt",
            options={
                1: "L'automate {automaton} est prêt",
                2: "L'automate conçu pour {purpose} est prêt",
                3: "L'automate de type {type} est prêt",
            },
            default_plurals={
                1: "Les automates sont prêts",
                2: "Les deux automates sont prêts",
            },
            options_plurals={
                1: {
                    1: "Les automates {automaton} sont prêts",
                    2: "Les deux automates {automaton} sont prêts",
                },
                2: {
                    1: "Les automates conçus pour {purpose} sont prêts",
                    2: "Les deux automates conçus pour {purpose} sont prêts",
                },
                3: {
                    1: "Les automates de type {type} sont prêts",
                    2: "Les deux automates de type {type} sont prêts",
                    3: "Les nombreux automates de type {type} sont prêts",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "fr-FR",
                "location": [],
                "flags": ["python-format"],
                "comments": "Message sur les automates basés sur les grammaires de Chomsky",
                "count": {"singular": 3, "plurals": [2, 2, 3]},
            },
        ),
        "1104": Message(
            id="1104",
            default="Le fleur a une belle couleur",
            options={
                1: "La {flower} a une belle couleur",
                2: "La {flower} de couleur {color} est magnifique",
                3: "La {flower} de l'année {year} est splendide",
            },
            default_plurals={
                1: "Les fleurs ont de belles couleurs",
                2: "Les deux fleurs ont de belles couleurs",
            },
            options_plurals={
                1: {
                    1: "Les {flower} ont de belles couleurs",
                    2: "Les deux {flower} ont de belles couleurs",
                },
                2: {
                    1: "Les {flower} de couleur {color} sont magnifiques",
                    2: "Les deux {flower} de couleur {color} sont magnifiques",
                },
                3: {
                    1: "Les {flower} de l'année {year} sont splendides",
                    2: "Les deux {flower} de l'année {year} sont splendides",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "fr-FR",
                "location": [],
                "flags": ["python-format"],
                "comments": "Message sur les fleurs",
                "count": {"singular": 3, "plurals": [2, 2, 2]},
            },
        ),
        "1105": Message(
            id="1105",
            default="La montagne est couverte de neige",
            options={
                1: "La montagne {mountain} est couverte de neige",
                2: "La montagne située à {location} est couverte de neige",
                3: "La montagne en {season} est couverte de neige",
            },
            default_plurals={
                1: "Les montagnes sont couvertes de neige",
                2: "Les deux montagnes sont couvertes de neige",
            },
            options_plurals={
                1: {
                    1: "Les montagnes {mountain} sont couvertes de neige",
                    2: "Les deux montagnes {mountain} sont couvertes de neige",
                },
                2: {
                    1: "Les montagnes situées à {location} sont couvertes de neige",
                    2: "Les deux montagnes situées à {location} sont couvertes de neige",
                },
                3: {
                    1: "Les montagnes en {season} sont couvertes de neige",
                    2: "Les deux montagnes en {season} sont couvertes de neige",
                    3: "Les nombreuses montagnes en {season} sont couvertes de neige",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "fr-FR",
                "location": [],
                "flags": ["python-format"],
                "comments": "Message sur les montagnes",
                "count": {"singular": 3, "plurals": [2, 2, 3]},
            },
        ),
        "1106": Message(
            id="1106",
            default="Le voyage est long",
            options={
                1: "Le voyage vers {destination} est long",
                2: "Le voyage avec {companion} est long",
                3: "Le voyage de {duration} jours est long",
            },
            default_plurals={
                1: "Les voyages sont longs",
                2: "Ces deux voyages sont longs",
            },
            options_plurals={
                1: {
                    1: "Les voyages vers {destination} sont longs",
                    2: "Ces deux voyages vers {destination} sont longs",
                },
                2: {
                    1: "Les voyages avec {companion} sont longs",
                    2: "Ces deux voyages avec {companion} sont longs",
                },
                3: {
                    1: "Les voyages de {duration} jours sont longs",
                    2: "Ces deux voyages de {duration} jours sont longs",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "fr-FR",
                "location": [],
                "flags": ["python-format"],
                "comments": "Message sur les voyages",
                "count": {"singular": 3, "plurals": [2, 2, 2]},
            },
        ),
        "1107": Message(
            id="1107",
            default="L'automate fonctionne",
            options={
                1: "L'automate {automaton} fonctionne",
                2: "L'automate pour {purpose} fonctionne",
                3: "L'automate de type {type} fonctionne",
            },
            default_plurals={
                1: "Les automates fonctionnent",
                2: "Les deux automates fonctionnent",
            },
            options_plurals={
                1: {
                    1: "Les automates {automaton} fonctionnent",
                    2: "Les deux automates {automaton} fonctionnent",
                },
                2: {
                    1: "Les automates pour {purpose} fonctionnent",
                    2: "Les deux automates pour {purpose} fonctionnent",
                },
                3: {
                    1: "Les automates de type {type} fonctionnent",
                    2: "Les deux automates de type {type} fonctionnent",
                    3: "Les nombreux automates de type {type} fonctionnent",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "fr-FR",
                "location": [],
                "flags": ["python-format"],
                "comments": "Message sur les automates basés sur les grammaires de Chomsky",
                "count": {"singular": 3, "plurals": [2, 2, 3]},
            },
        ),
        "1108": Message(
            id="1108",
            default="Le fleur sent bon",
            options={
                1: "La {flower} sent bon",
                2: "La {flower} de couleur {color} sent bon",
                3: "La {flower} cultivée en {year} sent bon",
            },
            default_plurals={
                1: "Les fleurs sentent bon",
                2: "Ces deux fleurs sentent bon",
            },
            options_plurals={
                1: {1: "Les {flower} sentent bon", 2: "Ces deux {flower} sentent bon"},
                2: {
                    1: "Les {flower} de couleur {color} sentent bon",
                    2: "Ces deux {flower} de couleur {color} sentent bon",
                },
                3: {
                    1: "Les {flower} cultivées en {year} sentent bon",
                    2: "Ces deux {flower} cultivées en {year} sentent bon",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "fr-FR",
                "location": [],
                "flags": ["python-format"],
                "comments": "Message sur les fleurs",
                "count": {"singular": 3, "plurals": [2, 2, 2]},
            },
        ),
        "1109": Message(
            id="1109",
            default="La montagne est enneigée",
            options={
                1: "La montagne {mountain} est enneigée",
                2: "La montagne située à {location} est enneigée",
                3: "La montagne en {season} est enneigée",
            },
            default_plurals={
                1: "Les montagnes sont enneigées",
                2: "Ces deux montagnes sont enneigées",
            },
            options_plurals={
                1: {
                    1: "Les montagnes {mountain} sont enneigées",
                    2: "Ces deux montagnes {mountain} sont enneigées",
                },
                2: {
                    1: "Les montagnes situées à {location} sont enneigées",
                    2: "Ces deux montagnes situées à {location} sont enneigées",
                },
                3: {
                    1: "Les montagnes en {season} sont enneigées",
                    2: "Ces deux montagnes en {season} sont enneigées",
                    3: "Les nombreuses montagnes en {season} sont enneigées",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "fr-FR",
                "location": [],
                "flags": ["python-format"],
                "comments": "Message sur les montagnes",
                "count": {"singular": 3, "plurals": [2, 2, 3]},
            },
        ),
    }


@pytest.fixture
def en_us_messages():
    return {
        "1100": Message(
            id="1100",
            default="Here is a flower",
            options={
                1: "Here is a beautiful {flower}",
                2: "Here is a rare {flower}",
                3: "Here is a {flower} from the {region} region",
            },
            default_plurals={
                1: "Here are flowers",
                2: "Here are two flowers",
            },
            options_plurals={
                1: {
                    1: "Here are beautiful {flower}",
                    2: "Here are two beautiful {flower}",
                },
                2: {
                    1: "Here are rare {flower}",
                    2: "Here are two rare {flower}",
                    3: "Here are several rare {flower}",
                },
                3: {
                    1: "Here are {flower} from the {region} region",
                    2: "Here are two {flower} from the {region} region",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "en-US",
                "location": [],
                "flags": ["python-format"],
                "comments": "Message about flowers",
                "count": {"singular": 3, "plurals": [2, 3, 2]},
            },
        ),
        "1101": Message(
            id="1101",
            default="I like this mountain",
            options={
                1: "I like this mountain {mountain}",
                2: "I like this mountain located at {location}",
                3: "I like this mountain called {name}",
            },
            default_plurals={
                1: "I like these mountains",
                2: "I like these two mountains",
            },
            options_plurals={
                1: {
                    1: "I like these mountains {mountain}",
                    2: "I like these two mountains {mountain}",
                },
                2: {
                    1: "I like these mountains located at {location}",
                    2: "I like these two mountains located at {location}",
                },
                3: {
                    1: "I like these mountains called {name}",
                    2: "I like these two mountains called {name}",
                    3: "I like these numerous mountains called {name}",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "en-US",
                "location": [],
                "flags": ["python-format"],
                "comments": "Message about mountains",
                "count": {"singular": 3, "plurals": [2, 2, 3]},
            },
        ),
        "1102": Message(
            id="1102",
            default="I'm going on a trip",
            options={
                1: "I'm going on a trip to {destination}",
                2: "I'm going on a trip with {companion}",
                3: "I'm going on a trip for {duration} days",
            },
            default_plurals={
                1: "I'm going on trips",
                2: "I'm going on two trips",
            },
            options_plurals={
                1: {
                    1: "I'm going on trips to {destination}",
                    2: "I'm going on two trips to {destination}",
                },
                2: {
                    1: "I'm going on trips with {companion}",
                    2: "I'm going on two trips with {companion}",
                },
                3: {
                    1: "I'm going on trips for {duration} days",
                    2: "I'm going on two trips for {duration} days",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "en-US",
                "location": [],
                "flags": ["python-format"],
                "comments": "Message about trips",
                "count": {"singular": 3, "plurals": [2, 2, 2]},
            },
        ),
        "1103": Message(
            id="1103",
            default="The automaton is ready",
            options={
                1: "The automaton {automaton} is ready",
                2: "The automaton designed for {purpose} is ready",
                3: "The automaton of type {type} is ready",
            },
            default_plurals={
                1: "The automatons are ready",
                2: "The two automatons are ready",
            },
            options_plurals={
                1: {
                    1: "The automatons {automaton} are ready",
                    2: "The two automatons {automaton} are ready",
                },
                2: {
                    1: "The automatons designed for {purpose} are ready",
                    2: "The two automatons designed for {purpose} are ready",
                },
                3: {
                    1: "The automatons of type {type} are ready",
                    2: "The two automatons of type {type} are ready",
                    3: "The numerous automatons of type {type} are ready",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "en-US",
                "location": [],
                "flags": ["python-format"],
                "comments": "Message about automata based on Chomsky grammars",
                "count": {"singular": 3, "plurals": [2, 2, 3]},
            },
        ),
        "1104": Message(
            id="1104",
            default="The flower has a beautiful color",
            options={
                1: "The {flower} has a beautiful color",
                2: "The {flower} of color {color} is magnificent",
                3: "The {flower} of the year {year} is splendid",
            },
            default_plurals={
                1: "Flowers have beautiful colors",
                2: "The two flowers have beautiful colors",
            },
            options_plurals={
                1: {
                    1: "The {flower} have beautiful colors",
                    2: "The two {flower} have beautiful colors",
                },
                2: {
                    1: "The {flower} of color {color} are magnificent",
                    2: "The two {flower} of color {color} are magnificent",
                },
                3: {
                    1: "The {flower} of the year {year} are splendid",
                    2: "The two {flower} of the year {year} are splendid",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "en-US",
                "location": [],
                "flags": ["python-format"],
                "comments": "Message about flowers",
                "count": {"singular": 3, "plurals": [2, 2, 2]},
            },
        ),
        "1105": Message(
            id="1105",
            default="The mountain is snow-covered",
            options={
                1: "The mountain {mountain} is snow-covered",
                2: "The mountain located at {location} is snow-covered",
                3: "The mountain in {season} is snow-covered",
            },
            default_plurals={
                1: "The mountains are snow-covered",
                2: "These two mountains are snow-covered",
            },
            options_plurals={
                1: {
                    1: "The mountains {mountain} are snow-covered",
                    2: "These two mountains {mountain} are snow-covered",
                },
                2: {
                    1: "The mountains located at {location} are snow-covered",
                    2: "These two mountains located at {location} are snow-covered",
                },
                3: {
                    1: "The mountains in {season} are snow-covered",
                    2: "These two mountains in {season} are snow-covered",
                    3: "The numerous mountains in {season} are snow-covered",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "en-US",
                "location": [],
                "flags": ["python-format"],
                "comments": "Message about mountains",
                "count": {"singular": 3, "plurals": [2, 2, 3]},
            },
        ),
        "1106": Message(
            id="1106",
            default="The trip is long",
            options={
                1: "The trip to {destination} is long",
                2: "The trip with {companion} is long",
                3: "The trip of {duration} days is long",
            },
            default_plurals={
                1: "Trips are long",
                2: "These two trips are long",
            },
            options_plurals={
                1: {
                    1: "Trips to {destination} are long",
                    2: "These two trips to {destination} are long",
                },
                2: {
                    1: "Trips with {companion} are long",
                    2: "These two trips with {companion} are long",
                },
                3: {
                    1: "Trips of {duration} days are long",
                    2: "These two trips of {duration} days are long",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "en-US",
                "location": [],
                "flags": ["python-format"],
                "comments": "Message about trips",
                "count": {"singular": 3, "plurals": [2, 2, 2]},
            },
        ),
        "1107": Message(
            id="1107",
            default="The automaton works",
            options={
                1: "The automaton {automaton} works",
                2: "The automaton for {purpose} works",
                3: "The automaton of type {type} works",
            },
            default_plurals={
                1: "The automatons work",
                2: "The two automatons work",
            },
            options_plurals={
                1: {
                    1: "The automatons {automaton} work",
                    2: "The two automatons {automaton} work",
                },
                2: {
                    1: "The automatons for {purpose} work",
                    2: "The two automatons for {purpose} work",
                },
                3: {
                    1: "The automatons of type {type} work",
                    2: "The two automatons of type {type} work",
                    3: "The numerous automatons of type {type} work",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "en-US",
                "location": [],
                "flags": ["python-format"],
                "comments": "Message about automata based on Chomsky grammars",
                "count": {"singular": 3, "plurals": [2, 2, 3]},
            },
        ),
        "1108": Message(
            id="1108",
            default="The flower smells good",
            options={
                1: "The {flower} smells good",
                2: "The {flower} of color {color} smells good",
                3: "The {flower} cultivated in {year} smells good",
            },
            default_plurals={
                1: "Flowers smell good",
                2: "These two flowers smell good",
            },
            options_plurals={
                1: {1: "The {flower} smell good", 2: "These two {flower} smell good"},
                2: {
                    1: "The {flower} of color {color} smell good",
                    2: "These two {flower} of color {color} smell good",
                },
                3: {
                    1: "The {flower} cultivated in {year} smell good",
                    2: "These two {flower} cultivated in {year} smell good",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "en-US",
                "location": [],
                "flags": ["python-format"],
                "comments": "Message about flowers",
                "count": {"singular": 3, "plurals": [2, 2, 2]},
            },
        ),
        "1109": Message(
            id="1109",
            default="The mountain is snowy",
            options={
                1: "The mountain {mountain} is snowy",
                2: "The mountain located at {location} is snowy",
                3: "The mountain in {season} is snowy",
            },
            default_plurals={
                1: "The mountains are snowy",
                2: "These two mountains are snowy",
            },
            options_plurals={
                1: {
                    1: "The mountains {mountain} are snowy",
                    2: "These two mountains {mountain} are snowy",
                },
                2: {
                    1: "The mountains located at {location} are snowy",
                    2: "These two mountains located at {location} are snowy",
                },
                3: {
                    1: "The mountains in {season} are snowy",
                    2: "These two mountains in {season} are snowy",
                    3: "The numerous mountains in {season} are snowy",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "en-US",
                "location": [],
                "flags": ["python-format"],
                "comments": "Message about mountains",
                "count": {"singular": 3, "plurals": [2, 2, 3]},
            },
        ),
    }


@pytest.fixture
def en_gb_messages():
    return {
        "1100": Message(
            id="1100",
            default="Here is a flower",
            options={
                1: "Here is a beautiful {flower}",
                2: "Here is a rare {flower}",
                3: "Here is a {flower} from the {region} region",
            },
            default_plurals={
                1: "Here are flowers",
                2: "Here are two flowers",
            },
            options_plurals={
                1: {
                    1: "Here are beautiful {flower}",
                    2: "Here are two beautiful {flower}",
                },
                2: {
                    1: "Here are rare {flower}",
                    2: "Here are two rare {flower}",
                    3: "Here are several rare {flower}",
                },
                3: {
                    1: "Here are {flower} from the {region} region",
                    2: "Here are two {flower} from the {region} region",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "en-GB",
                "location": [],
                "flags": ["python-format"],
                "comments": "Message about flowers",
                "count": {"singular": 3, "plurals": [2, 3, 2]},
            },
        ),
        "1101": Message(
            id="1101",
            default="I like this mountain",
            options={
                1: "I like this mountain {mountain}",
                2: "I like this mountain located at {location}",
                3: "I like this mountain called {name}",
            },
            default_plurals={
                1: "I like these mountains",
                2: "I like these two mountains",
            },
            options_plurals={
                1: {
                    1: "I like these mountains {mountain}",
                    2: "I like these two mountains {mountain}",
                },
                2: {
                    1: "I like these mountains located at {location}",
                    2: "I like these two mountains located at {location}",
                },
                3: {
                    1: "I like these mountains called {name}",
                    2: "I like these two mountains called {name}",
                    3: "I like these numerous mountains called {name}",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "en-GB",
                "location": [],
                "flags": ["python-format"],
                "comments": "Message about mountains",
                "count": {"singular": 3, "plurals": [2, 2, 3]},
            },
        ),
        "1102": Message(
            id="1102",
            default="I'm going on a trip",
            options={
                1: "I'm going on a trip to {destination}",
                2: "I'm going on a trip with {companion}",
                3: "I'm going on a trip for {duration} days",
            },
            default_plurals={
                1: "I'm going on trips",
                2: "I'm going on two trips",
            },
            options_plurals={
                1: {
                    1: "I'm going on trips to {destination}",
                    2: "I'm going on two trips to {destination}",
                },
                2: {
                    1: "I'm going on trips with {companion}",
                    2: "I'm going on two trips with {companion}",
                },
                3: {
                    1: "I'm going on trips for {duration} days",
                    2: "I'm going on two trips for {duration} days",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "en-GB",
                "location": [],
                "flags": ["python-format"],
                "comments": "Message about trips",
                "count": {"singular": 3, "plurals": [2, 2, 2]},
            },
        ),
        "1103": Message(
            id="1103",
            default="The automaton is ready",
            options={
                1: "The automaton {automaton} is ready",
                2: "The automaton designed for {purpose} is ready",
                3: "The automaton of type {type} is ready",
            },
            default_plurals={
                1: "The automatons are ready",
                2: "The two automatons are ready",
            },
            options_plurals={
                1: {
                    1: "The automatons {automaton} are ready",
                    2: "The two automatons {automaton} are ready",
                },
                2: {
                    1: "The automatons designed for {purpose} are ready",
                    2: "The two automatons designed for {purpose} are ready",
                },
                3: {
                    1: "The automatons of type {type} are ready",
                    2: "The two automatons of type {type} are ready",
                    3: "The numerous automatons of type {type} are ready",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "en-GB",
                "location": [],
                "flags": ["python-format"],
                "comments": "Message about automata based on Chomsky grammars",
                "count": {"singular": 3, "plurals": [2, 2, 3]},
            },
        ),
        "1104": Message(
            id="1104",
            default="The flower has a beautiful colour",
            options={
                1: "The {flower} has a beautiful colour",
                2: "The {flower} of colour {color} is magnificent",
                3: "The {flower} of the year {year} is splendid",
            },
            default_plurals={
                1: "Flowers have beautiful colours",
                2: "The two flowers have beautiful colours",
            },
            options_plurals={
                1: {
                    1: "The {flower} have beautiful colours",
                    2: "The two {flower} have beautiful colours",
                },
                2: {
                    1: "The {flower} of colour {color} are magnificent",
                    2: "The two {flower} of colour {color} are magnificent",
                },
                3: {
                    1: "The {flower} of the year {year} are splendid",
                    2: "The two {flower} of the year {year} are splendid",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "en-GB",
                "location": [],
                "flags": ["python-format"],
                "comments": "Message about flowers",
                "count": {"singular": 3, "plurals": [2, 2, 2]},
            },
        ),
        "1105": Message(
            id="1105",
            default="The mountain is snow-covered",
            options={
                1: "The mountain {mountain} is snow-covered",
                2: "The mountain located at {location} is snow-covered",
                3: "The mountain in {season} is snow-covered",
            },
            default_plurals={
                1: "The mountains are snow-covered",
                2: "These two mountains are snow-covered",
            },
            options_plurals={
                1: {
                    1: "The mountains {mountain} are snow-covered",
                    2: "These two mountains {mountain} are snow-covered",
                },
                2: {
                    1: "The mountains located at {location} are snow-covered",
                    2: "These two mountains located at {location} are snow-covered",
                },
                3: {
                    1: "The mountains in {season} are snow-covered",
                    2: "These two mountains in {season} are snow-covered",
                    3: "The numerous mountains in {season} are snow-covered",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "en-GB",
                "location": [],
                "flags": ["python-format"],
                "comments": "Message about mountains",
                "count": {"singular": 3, "plurals": [2, 2, 3]},
            },
        ),
        "1106": Message(
            id="1106",
            default="The trip is long",
            options={
                1: "The trip to {destination} is long",
                2: "The trip with {companion} is long",
                3: "The trip of {duration} days is long",
            },
            default_plurals={
                1: "Trips are long",
                2: "These two trips are long",
            },
            options_plurals={
                1: {
                    1: "Trips to {destination} are long",
                    2: "These two trips to {destination} are long",
                },
                2: {
                    1: "Trips with {companion} are long",
                    2: "These two trips with {companion} are long",
                },
                3: {
                    1: "Trips of {duration} days are long",
                    2: "These two trips of {duration} days are long",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "en-GB",
                "location": [],
                "flags": ["python-format"],
                "comments": "Message about trips",
                "count": {"singular": 3, "plurals": [2, 2, 2]},
            },
        ),
        "1107": Message(
            id="1107",
            default="The automaton works",
            options={
                1: "The automaton {automaton} works",
                2: "The automaton for {purpose} works",
                3: "The automaton of type {type} works",
            },
            default_plurals={
                1: "The automatons work",
                2: "The two automatons work",
            },
            options_plurals={
                1: {
                    1: "The automatons {automaton} work",
                    2: "The two automatons {automaton} work",
                },
                2: {
                    1: "The automatons for {purpose} work",
                    2: "The two automatons for {purpose} work",
                },
                3: {
                    1: "The automatons of type {type} work",
                    2: "The two automatons of type {type} work",
                    3: "The numerous automatons of type {type} work",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "en-GB",
                "location": [],
                "flags": ["python-format"],
                "comments": "Message about automata based on Chomsky grammars",
                "count": {"singular": 3, "plurals": [2, 2, 3]},
            },
        ),
        "1108": Message(
            id="1108",
            default="The flower smells nice",
            options={
                1: "The {flower} smells nice",
                2: "The {flower} of colour {color} smells nice",
                3: "The {flower} cultivated in {year} smells nice",
            },
            default_plurals={
                1: "The flowers smell nice",
                2: "These two flowers smell nice",
            },
            options_plurals={
                1: {1: "The {flower} smell nice", 2: "These two {flower} smell nice"},
                2: {
                    1: "The {flower} of colour {color} smell nice",
                    2: "These two {flower} of colour {color} smell nice",
                },
                3: {
                    1: "The {flower} cultivated in {year} smell nice",
                    2: "These two {flower} cultivated in {year} smell nice",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "en-GB",
                "location": [],
                "flags": ["python-format"],
                "comments": "Message about flowers",
                "count": {"singular": 3, "plurals": [2, 2, 2]},
            },
        ),
        "1109": Message(
            id="1109",
            default="The mountain is covered with snow",
            options={
                1: "The mountain {mountain} is covered with snow",
                2: "The mountain located at {location} is covered with snow",
                3: "The mountain in {season} is covered with snow",
            },
            default_plurals={
                1: "The mountains are covered with snow",
                2: "These two mountains are covered with snow",
            },
            options_plurals={
                1: {
                    1: "The mountains {mountain} are covered with snow",
                    2: "These two mountains {mountain} are covered with snow",
                },
                2: {
                    1: "The mountains located at {location} are covered with snow",
                    2: "These two mountains located at {location} are covered with snow",
                },
                3: {
                    1: "The mountains in {season} are covered with snow",
                    2: "These two mountains in {season} are covered with snow",
                    3: "The numerous mountains in {season} are covered with snow",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "en-GB",
                "location": [],
                "flags": ["python-format"],
                "comments": "Message about mountains",
                "count": {"singular": 3, "plurals": [2, 2, 3]},
            },
        ),
    }


@pytest.fixture
def it_it_messages():
    return {
        "1100": Message(
            id="1100",
            default="Ecco un fiore",
            options={
                1: "Ecco un bellissimo {flower}",
                2: "Ecco un raro {flower}",
                3: "Ecco un {flower} della regione {region}",
            },
            default_plurals={
                1: "Ecco dei fiori",
                2: "Ecco due fiori",
            },
            options_plurals={
                1: {
                    1: "Ecco dei bellissimi {flower}",
                    2: "Ecco due bellissimi {flower}",
                },
                2: {
                    1: "Ecco dei {flower} rari",
                    2: "Ecco due {flower} rari",
                    3: "Ecco diversi {flower} rari",
                },
                3: {
                    1: "Ecco dei {flower} della regione {region}",
                    2: "Ecco due {flower} della regione {region}",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "it-IT",
                "location": [],
                "flags": ["python-format"],
                "comments": "Messaggio sui fiori",
                "count": {"singular": 3, "plurals": [2, 3, 2]},
            },
        ),
        "1101": Message(
            id="1101",
            default="Mi piace questa montagna",
            options={
                1: "Mi piace questa montagna {mountain}",
                2: "Mi piace questa montagna situata a {location}",
                3: "Mi piace questa montagna chiamata {name}",
            },
            default_plurals={
                1: "Mi piacciono queste montagne",
                2: "Mi piacciono queste due montagne",
            },
            options_plurals={
                1: {
                    1: "Mi piacciono queste montagne {mountain}",
                    2: "Mi piacciono queste due montagne {mountain}",
                },
                2: {
                    1: "Mi piacciono queste montagne situate a {location}",
                    2: "Mi piacciono queste due montagne situate a {location}",
                },
                3: {
                    1: "Mi piacciono queste montagne chiamate {name}",
                    2: "Mi piacciono queste due montagne chiamate {name}",
                    3: "Mi piacciono queste numerose montagne chiamate {name}",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "it-IT",
                "location": [],
                "flags": ["python-format"],
                "comments": "Messaggio sulle montagne",
                "count": {"singular": 3, "plurals": [2, 2, 3]},
            },
        ),
        "1102": Message(
            id="1102",
            default="Parto per un viaggio",
            options={
                1: "Parto per un viaggio verso {destination}",
                2: "Parto per un viaggio con {companion}",
                3: "Parto per un viaggio di {duration} giorni",
            },
            default_plurals={
                1: "Parto per dei viaggi",
                2: "Parto per due viaggi",
            },
            options_plurals={
                1: {
                    1: "Parto per dei viaggi verso {destination}",
                    2: "Parto per due viaggi verso {destination}",
                },
                2: {
                    1: "Parto per dei viaggi con {companion}",
                    2: "Parto per due viaggi con {companion}",
                },
                3: {
                    1: "Parto per dei viaggi di {duration} giorni",
                    2: "Parto per due viaggi di {duration} giorni",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "it-IT",
                "location": [],
                "flags": ["python-format"],
                "comments": "Messaggio sui viaggi",
                "count": {"singular": 3, "plurals": [2, 2, 2]},
            },
        ),
        "1103": Message(
            id="1103",
            default="L'automata è pronto",
            options={
                1: "L'automata {automaton} è pronto",
                2: "L'automata progettato per {purpose} è pronto",
                3: "L'automata di tipo {type} è pronto",
            },
            default_plurals={
                1: "Gli automi sono pronti",
                2: "I due automi sono pronti",
            },
            options_plurals={
                1: {
                    1: "Gli automi {automaton} sono pronti",
                    2: "I due automi {automaton} sono pronti",
                },
                2: {
                    1: "Gli automi progettati per {purpose} sono pronti",
                    2: "I due automi progettati per {purpose} sono pronti",
                },
                3: {
                    1: "Gli automi di tipo {type} sono pronti",
                    2: "I due automi di tipo {type} sono pronti",
                    3: "I numerosi automi di tipo {type} sono pronti",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "it-IT",
                "location": [],
                "flags": ["python-format"],
                "comments": "Messaggio sugli automi basati sulle grammatiche di Chomsky",
                "count": {"singular": 3, "plurals": [2, 2, 3]},
            },
        ),
        "1104": Message(
            id="1104",
            default="Il fiore ha un bel colore",
            options={
                1: "Il {flower} ha un bel colore",
                2: "Il {flower} di colore {color} è magnifico",
                3: "Il {flower} dell'anno {year} è splendido",
            },
            default_plurals={
                1: "I fiori hanno bei colori",
                2: "I due fiori hanno bei colori",
            },
            options_plurals={
                1: {
                    1: "I {flower} hanno bei colori",
                    2: "I due {flower} hanno bei colori",
                },
                2: {
                    1: "I {flower} di colore {color} sono magnifici",
                    2: "I due {flower} di colore {color} sono magnifici",
                },
                3: {
                    1: "I {flower} dell'anno {year} sono splendidi",
                    2: "I due {flower} dell'anno {year} sono splendidi",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "it-IT",
                "location": [],
                "flags": ["python-format"],
                "comments": "Messaggio sui fiori",
                "count": {"singular": 3, "plurals": [2, 2, 2]},
            },
        ),
        "1105": Message(
            id="1105",
            default="La montagna è ricoperta di neve",
            options={
                1: "La montagna {mountain} è ricoperta di neve",
                2: "La montagna situata a {location} è ricoperta di neve",
                3: "La montagna in {season} è ricoperta di neve",
            },
            default_plurals={
                1: "Le montagne sono ricoperte di neve",
                2: "Queste due montagne sono ricoperte di neve",
            },
            options_plurals={
                1: {
                    1: "Le montagne {mountain} sono ricoperte di neve",
                    2: "Queste due montagne {mountain} sono ricoperte di neve",
                },
                2: {
                    1: "Le montagne situate a {location} sono ricoperte di neve",
                    2: "Queste due montagne situate a {location} sono ricoperte di neve",
                },
                3: {
                    1: "Le montagne in {season} sono ricoperte di neve",
                    2: "Queste due montagne in {season} sono ricoperte di neve",
                    3: "Le numerose montagne in {season} sono ricoperte di neve",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "it-IT",
                "location": [],
                "flags": ["python-format"],
                "comments": "Messaggio sulle montagne",
                "count": {"singular": 3, "plurals": [2, 2, 3]},
            },
        ),
        "1106": Message(
            id="1106",
            default="Il viaggio è lungo",
            options={
                1: "Il viaggio verso {destination} è lungo",
                2: "Il viaggio con {companion} è lungo",
                3: "Il viaggio di {duration} giorni è lungo",
            },
            default_plurals={
                1: "I viaggi sono lunghi",
                2: "Questi due viaggi sono lunghi",
            },
            options_plurals={
                1: {
                    1: "I viaggi verso {destination} sono lunghi",
                    2: "Questi due viaggi verso {destination} sono lunghi",
                },
                2: {
                    1: "I viaggi con {companion} sono lunghi",
                    2: "Questi due viaggi con {companion} sono lunghi",
                },
                3: {
                    1: "I viaggi di {duration} giorni sono lunghi",
                    2: "Questi due viaggi di {duration} giorni sono lunghi",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "it-IT",
                "location": [],
                "flags": ["python-format"],
                "comments": "Messaggio sui viaggi",
                "count": {"singular": 3, "plurals": [2, 2, 2]},
            },
        ),
        "1107": Message(
            id="1107",
            default="L'automata funziona",
            options={
                1: "L'automata {automaton} funziona",
                2: "L'automata per {purpose} funziona",
                3: "L'automata di tipo {type} funziona",
            },
            default_plurals={
                1: "Gli automi funzionano",
                2: "I due automi funzionano",
            },
            options_plurals={
                1: {
                    1: "Gli automi {automaton} funzionano",
                    2: "I due automi {automaton} funzionano",
                },
                2: {
                    1: "Gli automi per {purpose} funzionano",
                    2: "I due automi per {purpose} funzionano",
                },
                3: {
                    1: "Gli automi di tipo {type} funzionano",
                    2: "I due automi di tipo {type} funzionano",
                    3: "I numerosi automi di tipo {type} funzionano",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "it-IT",
                "location": [],
                "flags": ["python-format"],
                "comments": "Messaggio sugli automi basati sulle grammatiche di Chomsky",
                "count": {"singular": 3, "plurals": [2, 2, 3]},
            },
        ),
        "1108": Message(
            id="1108",
            default="Il fiore profuma bene",
            options={
                1: "Il {flower} profuma bene",
                2: "Il {flower} di colore {color} profuma bene",
                3: "Il {flower} coltivato nel {year} profuma bene",
            },
            default_plurals={
                1: "I fiori profumano bene",
                2: "Questi due fiori profumano bene",
            },
            options_plurals={
                1: {
                    1: "I {flower} profumano bene",
                    2: "Questi due {flower} profumano bene",
                },
                2: {
                    1: "I {flower} di colore {color} profumano bene",
                    2: "Questi due {flower} di colore {color} profumano bene",
                },
                3: {
                    1: "I {flower} coltivati nel {year} profumano bene",
                    2: "Questi due {flower} coltivati nel {year} profumano bene",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "it-IT",
                "location": [],
                "flags": ["python-format"],
                "comments": "Messaggio sui fiori",
                "count": {"singular": 3, "plurals": [2, 2, 2]},
            },
        ),
        "1109": Message(
            id="1109",
            default="La montagna è innevata",
            options={
                1: "La montagna {mountain} è innevata",
                2: "La montagna situata a {location} è innevata",
                3: "La montagna in {season} è innevata",
            },
            default_plurals={
                1: "Le montagne sono innevate",
                2: "Queste due montagne sono innevate",
            },
            options_plurals={
                1: {
                    1: "Le montagne {mountain} sono innevate",
                    2: "Queste due montagne {mountain} sono innevate",
                },
                2: {
                    1: "Le montagne situate a {location} sono innevate",
                    2: "Queste due montagne situate a {location} sono innevate",
                },
                3: {
                    1: "Le montagne in {season} sono innevate",
                    2: "Queste due montagne in {season} sono innevate",
                    3: "Le numerose montagne in {season} sono innevate",
                },
            },
            metadata={
                "version": "0.1.0",
                "language": "it-IT",
                "location": [],
                "flags": ["python-format"],
                "comments": "Messaggio sulle montagne",
                "count": {"singular": 3, "plurals": [2, 2, 3]},
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
