import pytest

from i18n_tools.models import Message as MessageModel
from i18n_tools.models.book import Book
from i18n_tools.models.message import Message


@pytest.fixture
def fr_message():
    return MessageModel(
        "1000",
        "Bonjour",
        plurals=["Bonjour à tous", "Bonjour tout le monde"],
        alternatives=[
            ["Bonjour Mme {name}", "Bonjour Mesdames", "Mesdames"],
            ["Bonjour M. {name}", "Bonjour Messieurs", "Messieurs"],
        ],
        locations=[],
        flags=["python-format"],
        user_comments=["In French, Greeting message to one or more..."],
        auto_comments=["1000_000", "1000_001", "1000_02"],
    )


@pytest.fixture
def en_message():
    return MessageModel(
        "1000",
        "Hello",
        plurals=["Hi everybody", "Hi everyone"],
        alternatives=[
            ["Hello {name}", "Hi everybody", "Ladies"],
            ["Hello {name}", "Hi everyone", "Gentlemen"],
        ],
        locations=[],
        flags=["python-format"],
        user_comments=["Greeting message to one or more..."],
        auto_comments=["1000_000", "1000_001", "1000_02"],
    )


@pytest.fixture
def empty_message():
    return MessageModel("1000")


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
        "2000",
        "Une fleur",
        plurals=["Des fleurs", "Deux fleurs"],
        alternatives=[
            ["Une {flower}"],
            [
                "Une {flower} rare",
                "Des {flower} rares",
                "Deux {flower} rares",
                "Plusieurs {flower} rares",
            ],
        ],
        context="garden",
    )


@pytest.fixture
def single_message():
    """A principal singular only."""
    return Message("2001", "Bonjour {name}")


# --- Fixtures originally from test_01_book.py ---


@pytest.fixture
def fr_fr_messages():
    return {
        "1100": Message(
            "1100",
            "Voici une fleur",
            plurals=["Voici des fleurs", "Voici deux fleurs"],
            alternatives=[
                [
                    "Voici une belle {flower}",
                    "Voici de belles {flower}",
                    "Voici deux belles {flower}",
                ],
                [
                    "Voici une {flower} rare",
                    "Voici des {flower} rares",
                    "Voici deux {flower} rares",
                    "Voici plusieurs {flower} rares",
                ],
                [
                    "Voici une {flower} de la région {region}",
                    "Voici des {flower} de la région {region}",
                    "Voici deux {flower} de la région {region}",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=["Message sur les fleurs"],
        ),
        "1101": Message(
            "1101",
            "J'aime cette montagne",
            plurals=["J'aime ces montagnes", "J'aime ces deux montagnes"],
            alternatives=[
                [
                    "J'aime cette montagne {mountain}",
                    "J'aime ces montagnes {mountain}",
                    "J'aime ces deux montagnes {mountain}",
                ],
                [
                    "J'aime cette montagne située à {location}",
                    "J'aime ces montagnes situées à {location}",
                    "J'aime ces deux montagnes situées à {location}",
                ],
                [
                    "J'aime cette montagne appelée {name}",
                    "J'aime ces montagnes appelées {name}",
                    "J'aime ces deux montagnes appelées {name}",
                    "J'aime ces nombreuses montagnes appelées {name}",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=["Message sur les montagnes"],
        ),
        "1102": Message(
            "1102",
            "Je pars en voyage",
            plurals=["Je pars en voyages", "Je pars en deux voyages"],
            alternatives=[
                [
                    "Je pars en voyage à {destination}",
                    "Je pars en voyages à {destination}",
                    "Je pars en deux voyages à {destination}",
                ],
                [
                    "Je pars en voyage avec {companion}",
                    "Je pars en voyages avec {companion}",
                    "Je pars en deux voyages avec {companion}",
                ],
                [
                    "Je pars en voyage pour {duration} jours",
                    "Je pars en voyages pour {duration} jours",
                    "Je pars en deux voyages pour {duration} jours",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=["Message sur les voyages"],
        ),
        "1103": Message(
            "1103",
            "L'automate est prêt",
            plurals=["Les automates sont prêts", "Les deux automates sont prêts"],
            alternatives=[
                [
                    "L'automate {automaton} est prêt",
                    "Les automates {automaton} sont prêts",
                    "Les deux automates {automaton} sont prêts",
                ],
                [
                    "L'automate conçu pour {purpose} est prêt",
                    "Les automates conçus pour {purpose} sont prêts",
                    "Les deux automates conçus pour {purpose} sont prêts",
                ],
                [
                    "L'automate de type {type} est prêt",
                    "Les automates de type {type} sont prêts",
                    "Les deux automates de type {type} sont prêts",
                    "Les nombreux automates de type {type} sont prêts",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=[
                "Message sur les automates basés sur les grammaires de Chomsky"
            ],
        ),
        "1104": Message(
            "1104",
            "Le fleur a une belle couleur",
            plurals=[
                "Les fleurs ont de belles couleurs",
                "Les deux fleurs ont de belles couleurs",
            ],
            alternatives=[
                [
                    "La {flower} a une belle couleur",
                    "Les {flower} ont de belles couleurs",
                    "Les deux {flower} ont de belles couleurs",
                ],
                [
                    "La {flower} de couleur {color} est magnifique",
                    "Les {flower} de couleur {color} sont magnifiques",
                    "Les deux {flower} de couleur {color} sont magnifiques",
                ],
                [
                    "La {flower} de l'année {year} est splendide",
                    "Les {flower} de l'année {year} sont splendides",
                    "Les deux {flower} de l'année {year} sont splendides",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=["Message sur les fleurs"],
        ),
        "1105": Message(
            "1105",
            "La montagne est couverte de neige",
            plurals=[
                "Les montagnes sont couvertes de neige",
                "Les deux montagnes sont couvertes de neige",
            ],
            alternatives=[
                [
                    "La montagne {mountain} est couverte de neige",
                    "Les montagnes {mountain} sont couvertes de neige",
                    "Les deux montagnes {mountain} sont couvertes de neige",
                ],
                [
                    "La montagne située à {location} est couverte de neige",
                    "Les montagnes situées à {location} sont couvertes de neige",
                    "Les deux montagnes situées à {location} sont couvertes de neige",
                ],
                [
                    "La montagne en {season} est couverte de neige",
                    "Les montagnes en {season} sont couvertes de neige",
                    "Les deux montagnes en {season} sont couvertes de neige",
                    "Les nombreuses montagnes en {season} sont couvertes de neige",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=["Message sur les montagnes"],
        ),
        "1106": Message(
            "1106",
            "Le voyage est long",
            plurals=["Les voyages sont longs", "Ces deux voyages sont longs"],
            alternatives=[
                [
                    "Le voyage vers {destination} est long",
                    "Les voyages vers {destination} sont longs",
                    "Ces deux voyages vers {destination} sont longs",
                ],
                [
                    "Le voyage avec {companion} est long",
                    "Les voyages avec {companion} sont longs",
                    "Ces deux voyages avec {companion} sont longs",
                ],
                [
                    "Le voyage de {duration} jours est long",
                    "Les voyages de {duration} jours sont longs",
                    "Ces deux voyages de {duration} jours sont longs",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=["Message sur les voyages"],
        ),
        "1107": Message(
            "1107",
            "L'automate fonctionne",
            plurals=["Les automates fonctionnent", "Les deux automates fonctionnent"],
            alternatives=[
                [
                    "L'automate {automaton} fonctionne",
                    "Les automates {automaton} fonctionnent",
                    "Les deux automates {automaton} fonctionnent",
                ],
                [
                    "L'automate pour {purpose} fonctionne",
                    "Les automates pour {purpose} fonctionnent",
                    "Les deux automates pour {purpose} fonctionnent",
                ],
                [
                    "L'automate de type {type} fonctionne",
                    "Les automates de type {type} fonctionnent",
                    "Les deux automates de type {type} fonctionnent",
                    "Les nombreux automates de type {type} fonctionnent",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=[
                "Message sur les automates basés sur les grammaires de Chomsky"
            ],
        ),
        "1108": Message(
            "1108",
            "Le fleur sent bon",
            plurals=["Les fleurs sentent bon", "Ces deux fleurs sentent bon"],
            alternatives=[
                [
                    "La {flower} sent bon",
                    "Les {flower} sentent bon",
                    "Ces deux {flower} sentent bon",
                ],
                [
                    "La {flower} de couleur {color} sent bon",
                    "Les {flower} de couleur {color} sentent bon",
                    "Ces deux {flower} de couleur {color} sentent bon",
                ],
                [
                    "La {flower} cultivée en {year} sent bon",
                    "Les {flower} cultivées en {year} sentent bon",
                    "Ces deux {flower} cultivées en {year} sentent bon",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=["Message sur les fleurs"],
        ),
        "1109": Message(
            "1109",
            "La montagne est enneigée",
            plurals=[
                "Les montagnes sont enneigées",
                "Ces deux montagnes sont enneigées",
            ],
            alternatives=[
                [
                    "La montagne {mountain} est enneigée",
                    "Les montagnes {mountain} sont enneigées",
                    "Ces deux montagnes {mountain} sont enneigées",
                ],
                [
                    "La montagne située à {location} est enneigée",
                    "Les montagnes situées à {location} sont enneigées",
                    "Ces deux montagnes situées à {location} sont enneigées",
                ],
                [
                    "La montagne en {season} est enneigée",
                    "Les montagnes en {season} sont enneigées",
                    "Ces deux montagnes en {season} sont enneigées",
                    "Les nombreuses montagnes en {season} sont enneigées",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=["Message sur les montagnes"],
        ),
    }


@pytest.fixture
def en_us_messages():
    return {
        "1100": Message(
            "1100",
            "Here is a flower",
            plurals=["Here are flowers", "Here are two flowers"],
            alternatives=[
                [
                    "Here is a beautiful {flower}",
                    "Here are beautiful {flower}",
                    "Here are two beautiful {flower}",
                ],
                [
                    "Here is a rare {flower}",
                    "Here are rare {flower}",
                    "Here are two rare {flower}",
                    "Here are several rare {flower}",
                ],
                [
                    "Here is a {flower} from the {region} region",
                    "Here are {flower} from the {region} region",
                    "Here are two {flower} from the {region} region",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=["Message about flowers"],
        ),
        "1101": Message(
            "1101",
            "I like this mountain",
            plurals=["I like these mountains", "I like these two mountains"],
            alternatives=[
                [
                    "I like this mountain {mountain}",
                    "I like these mountains {mountain}",
                    "I like these two mountains {mountain}",
                ],
                [
                    "I like this mountain located at {location}",
                    "I like these mountains located at {location}",
                    "I like these two mountains located at {location}",
                ],
                [
                    "I like this mountain called {name}",
                    "I like these mountains called {name}",
                    "I like these two mountains called {name}",
                    "I like these numerous mountains called {name}",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=["Message about mountains"],
        ),
        "1102": Message(
            "1102",
            "I'm going on a trip",
            plurals=["I'm going on trips", "I'm going on two trips"],
            alternatives=[
                [
                    "I'm going on a trip to {destination}",
                    "I'm going on trips to {destination}",
                    "I'm going on two trips to {destination}",
                ],
                [
                    "I'm going on a trip with {companion}",
                    "I'm going on trips with {companion}",
                    "I'm going on two trips with {companion}",
                ],
                [
                    "I'm going on a trip for {duration} days",
                    "I'm going on trips for {duration} days",
                    "I'm going on two trips for {duration} days",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=["Message about trips"],
        ),
        "1103": Message(
            "1103",
            "The automaton is ready",
            plurals=["The automatons are ready", "The two automatons are ready"],
            alternatives=[
                [
                    "The automaton {automaton} is ready",
                    "The automatons {automaton} are ready",
                    "The two automatons {automaton} are ready",
                ],
                [
                    "The automaton designed for {purpose} is ready",
                    "The automatons designed for {purpose} are ready",
                    "The two automatons designed for {purpose} are ready",
                ],
                [
                    "The automaton of type {type} is ready",
                    "The automatons of type {type} are ready",
                    "The two automatons of type {type} are ready",
                    "The numerous automatons of type {type} are ready",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=["Message about automata based on Chomsky grammars"],
        ),
        "1104": Message(
            "1104",
            "The flower has a beautiful color",
            plurals=[
                "Flowers have beautiful colors",
                "The two flowers have beautiful colors",
            ],
            alternatives=[
                [
                    "The {flower} has a beautiful color",
                    "The {flower} have beautiful colors",
                    "The two {flower} have beautiful colors",
                ],
                [
                    "The {flower} of color {color} is magnificent",
                    "The {flower} of color {color} are magnificent",
                    "The two {flower} of color {color} are magnificent",
                ],
                [
                    "The {flower} of the year {year} is splendid",
                    "The {flower} of the year {year} are splendid",
                    "The two {flower} of the year {year} are splendid",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=["Message about flowers"],
        ),
        "1105": Message(
            "1105",
            "The mountain is snow-covered",
            plurals=[
                "The mountains are snow-covered",
                "These two mountains are snow-covered",
            ],
            alternatives=[
                [
                    "The mountain {mountain} is snow-covered",
                    "The mountains {mountain} are snow-covered",
                    "These two mountains {mountain} are snow-covered",
                ],
                [
                    "The mountain located at {location} is snow-covered",
                    "The mountains located at {location} are snow-covered",
                    "These two mountains located at {location} are snow-covered",
                ],
                [
                    "The mountain in {season} is snow-covered",
                    "The mountains in {season} are snow-covered",
                    "These two mountains in {season} are snow-covered",
                    "The numerous mountains in {season} are snow-covered",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=["Message about mountains"],
        ),
        "1106": Message(
            "1106",
            "The trip is long",
            plurals=["Trips are long", "These two trips are long"],
            alternatives=[
                [
                    "The trip to {destination} is long",
                    "Trips to {destination} are long",
                    "These two trips to {destination} are long",
                ],
                [
                    "The trip with {companion} is long",
                    "Trips with {companion} are long",
                    "These two trips with {companion} are long",
                ],
                [
                    "The trip of {duration} days is long",
                    "Trips of {duration} days are long",
                    "These two trips of {duration} days are long",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=["Message about trips"],
        ),
        "1107": Message(
            "1107",
            "The automaton works",
            plurals=["The automatons work", "The two automatons work"],
            alternatives=[
                [
                    "The automaton {automaton} works",
                    "The automatons {automaton} work",
                    "The two automatons {automaton} work",
                ],
                [
                    "The automaton for {purpose} works",
                    "The automatons for {purpose} work",
                    "The two automatons for {purpose} work",
                ],
                [
                    "The automaton of type {type} works",
                    "The automatons of type {type} work",
                    "The two automatons of type {type} work",
                    "The numerous automatons of type {type} work",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=["Message about automata based on Chomsky grammars"],
        ),
        "1108": Message(
            "1108",
            "The flower smells good",
            plurals=["Flowers smell good", "These two flowers smell good"],
            alternatives=[
                [
                    "The {flower} smells good",
                    "The {flower} smell good",
                    "These two {flower} smell good",
                ],
                [
                    "The {flower} of color {color} smells good",
                    "The {flower} of color {color} smell good",
                    "These two {flower} of color {color} smell good",
                ],
                [
                    "The {flower} cultivated in {year} smells good",
                    "The {flower} cultivated in {year} smell good",
                    "These two {flower} cultivated in {year} smell good",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=["Message about flowers"],
        ),
        "1109": Message(
            "1109",
            "The mountain is snowy",
            plurals=["The mountains are snowy", "These two mountains are snowy"],
            alternatives=[
                [
                    "The mountain {mountain} is snowy",
                    "The mountains {mountain} are snowy",
                    "These two mountains {mountain} are snowy",
                ],
                [
                    "The mountain located at {location} is snowy",
                    "The mountains located at {location} are snowy",
                    "These two mountains located at {location} are snowy",
                ],
                [
                    "The mountain in {season} is snowy",
                    "The mountains in {season} are snowy",
                    "These two mountains in {season} are snowy",
                    "The numerous mountains in {season} are snowy",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=["Message about mountains"],
        ),
    }


@pytest.fixture
def en_gb_messages():
    return {
        "1100": Message(
            "1100",
            "Here is a flower",
            plurals=["Here are flowers", "Here are two flowers"],
            alternatives=[
                [
                    "Here is a beautiful {flower}",
                    "Here are beautiful {flower}",
                    "Here are two beautiful {flower}",
                ],
                [
                    "Here is a rare {flower}",
                    "Here are rare {flower}",
                    "Here are two rare {flower}",
                    "Here are several rare {flower}",
                ],
                [
                    "Here is a {flower} from the {region} region",
                    "Here are {flower} from the {region} region",
                    "Here are two {flower} from the {region} region",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=["Message about flowers"],
        ),
        "1101": Message(
            "1101",
            "I like this mountain",
            plurals=["I like these mountains", "I like these two mountains"],
            alternatives=[
                [
                    "I like this mountain {mountain}",
                    "I like these mountains {mountain}",
                    "I like these two mountains {mountain}",
                ],
                [
                    "I like this mountain located at {location}",
                    "I like these mountains located at {location}",
                    "I like these two mountains located at {location}",
                ],
                [
                    "I like this mountain called {name}",
                    "I like these mountains called {name}",
                    "I like these two mountains called {name}",
                    "I like these numerous mountains called {name}",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=["Message about mountains"],
        ),
        "1102": Message(
            "1102",
            "I'm going on a trip",
            plurals=["I'm going on trips", "I'm going on two trips"],
            alternatives=[
                [
                    "I'm going on a trip to {destination}",
                    "I'm going on trips to {destination}",
                    "I'm going on two trips to {destination}",
                ],
                [
                    "I'm going on a trip with {companion}",
                    "I'm going on trips with {companion}",
                    "I'm going on two trips with {companion}",
                ],
                [
                    "I'm going on a trip for {duration} days",
                    "I'm going on trips for {duration} days",
                    "I'm going on two trips for {duration} days",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=["Message about trips"],
        ),
        "1103": Message(
            "1103",
            "The automaton is ready",
            plurals=["The automatons are ready", "The two automatons are ready"],
            alternatives=[
                [
                    "The automaton {automaton} is ready",
                    "The automatons {automaton} are ready",
                    "The two automatons {automaton} are ready",
                ],
                [
                    "The automaton designed for {purpose} is ready",
                    "The automatons designed for {purpose} are ready",
                    "The two automatons designed for {purpose} are ready",
                ],
                [
                    "The automaton of type {type} is ready",
                    "The automatons of type {type} are ready",
                    "The two automatons of type {type} are ready",
                    "The numerous automatons of type {type} are ready",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=["Message about automata based on Chomsky grammars"],
        ),
        "1104": Message(
            "1104",
            "The flower has a beautiful colour",
            plurals=[
                "Flowers have beautiful colours",
                "The two flowers have beautiful colours",
            ],
            alternatives=[
                [
                    "The {flower} has a beautiful colour",
                    "The {flower} have beautiful colours",
                    "The two {flower} have beautiful colours",
                ],
                [
                    "The {flower} of colour {color} is magnificent",
                    "The {flower} of colour {color} are magnificent",
                    "The two {flower} of colour {color} are magnificent",
                ],
                [
                    "The {flower} of the year {year} is splendid",
                    "The {flower} of the year {year} are splendid",
                    "The two {flower} of the year {year} are splendid",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=["Message about flowers"],
        ),
        "1105": Message(
            "1105",
            "The mountain is snow-covered",
            plurals=[
                "The mountains are snow-covered",
                "These two mountains are snow-covered",
            ],
            alternatives=[
                [
                    "The mountain {mountain} is snow-covered",
                    "The mountains {mountain} are snow-covered",
                    "These two mountains {mountain} are snow-covered",
                ],
                [
                    "The mountain located at {location} is snow-covered",
                    "The mountains located at {location} are snow-covered",
                    "These two mountains located at {location} are snow-covered",
                ],
                [
                    "The mountain in {season} is snow-covered",
                    "The mountains in {season} are snow-covered",
                    "These two mountains in {season} are snow-covered",
                    "The numerous mountains in {season} are snow-covered",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=["Message about mountains"],
        ),
        "1106": Message(
            "1106",
            "The trip is long",
            plurals=["Trips are long", "These two trips are long"],
            alternatives=[
                [
                    "The trip to {destination} is long",
                    "Trips to {destination} are long",
                    "These two trips to {destination} are long",
                ],
                [
                    "The trip with {companion} is long",
                    "Trips with {companion} are long",
                    "These two trips with {companion} are long",
                ],
                [
                    "The trip of {duration} days is long",
                    "Trips of {duration} days are long",
                    "These two trips of {duration} days are long",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=["Message about trips"],
        ),
        "1107": Message(
            "1107",
            "The automaton works",
            plurals=["The automatons work", "The two automatons work"],
            alternatives=[
                [
                    "The automaton {automaton} works",
                    "The automatons {automaton} work",
                    "The two automatons {automaton} work",
                ],
                [
                    "The automaton for {purpose} works",
                    "The automatons for {purpose} work",
                    "The two automatons for {purpose} work",
                ],
                [
                    "The automaton of type {type} works",
                    "The automatons of type {type} work",
                    "The two automatons of type {type} work",
                    "The numerous automatons of type {type} work",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=["Message about automata based on Chomsky grammars"],
        ),
        "1108": Message(
            "1108",
            "The flower smells nice",
            plurals=["The flowers smell nice", "These two flowers smell nice"],
            alternatives=[
                [
                    "The {flower} smells nice",
                    "The {flower} smell nice",
                    "These two {flower} smell nice",
                ],
                [
                    "The {flower} of colour {color} smells nice",
                    "The {flower} of colour {color} smell nice",
                    "These two {flower} of colour {color} smell nice",
                ],
                [
                    "The {flower} cultivated in {year} smells nice",
                    "The {flower} cultivated in {year} smell nice",
                    "These two {flower} cultivated in {year} smell nice",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=["Message about flowers"],
        ),
        "1109": Message(
            "1109",
            "The mountain is covered with snow",
            plurals=[
                "The mountains are covered with snow",
                "These two mountains are covered with snow",
            ],
            alternatives=[
                [
                    "The mountain {mountain} is covered with snow",
                    "The mountains {mountain} are covered with snow",
                    "These two mountains {mountain} are covered with snow",
                ],
                [
                    "The mountain located at {location} is covered with snow",
                    "The mountains located at {location} are covered with snow",
                    "These two mountains located at {location} are covered with snow",
                ],
                [
                    "The mountain in {season} is covered with snow",
                    "The mountains in {season} are covered with snow",
                    "These two mountains in {season} are covered with snow",
                    "The numerous mountains in {season} are covered with snow",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=["Message about mountains"],
        ),
    }


@pytest.fixture
def it_it_messages():
    return {
        "1100": Message(
            "1100",
            "Ecco un fiore",
            plurals=["Ecco dei fiori", "Ecco due fiori"],
            alternatives=[
                [
                    "Ecco un bellissimo {flower}",
                    "Ecco dei bellissimi {flower}",
                    "Ecco due bellissimi {flower}",
                ],
                [
                    "Ecco un raro {flower}",
                    "Ecco dei {flower} rari",
                    "Ecco due {flower} rari",
                    "Ecco diversi {flower} rari",
                ],
                [
                    "Ecco un {flower} della regione {region}",
                    "Ecco dei {flower} della regione {region}",
                    "Ecco due {flower} della regione {region}",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=["Messaggio sui fiori"],
        ),
        "1101": Message(
            "1101",
            "Mi piace questa montagna",
            plurals=[
                "Mi piacciono queste montagne",
                "Mi piacciono queste due montagne",
            ],
            alternatives=[
                [
                    "Mi piace questa montagna {mountain}",
                    "Mi piacciono queste montagne {mountain}",
                    "Mi piacciono queste due montagne {mountain}",
                ],
                [
                    "Mi piace questa montagna situata a {location}",
                    "Mi piacciono queste montagne situate a {location}",
                    "Mi piacciono queste due montagne situate a {location}",
                ],
                [
                    "Mi piace questa montagna chiamata {name}",
                    "Mi piacciono queste montagne chiamate {name}",
                    "Mi piacciono queste due montagne chiamate {name}",
                    "Mi piacciono queste numerose montagne chiamate {name}",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=["Messaggio sulle montagne"],
        ),
        "1102": Message(
            "1102",
            "Parto per un viaggio",
            plurals=["Parto per dei viaggi", "Parto per due viaggi"],
            alternatives=[
                [
                    "Parto per un viaggio verso {destination}",
                    "Parto per dei viaggi verso {destination}",
                    "Parto per due viaggi verso {destination}",
                ],
                [
                    "Parto per un viaggio con {companion}",
                    "Parto per dei viaggi con {companion}",
                    "Parto per due viaggi con {companion}",
                ],
                [
                    "Parto per un viaggio di {duration} giorni",
                    "Parto per dei viaggi di {duration} giorni",
                    "Parto per due viaggi di {duration} giorni",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=["Messaggio sui viaggi"],
        ),
        "1103": Message(
            "1103",
            "L'automata è pronto",
            plurals=["Gli automi sono pronti", "I due automi sono pronti"],
            alternatives=[
                [
                    "L'automata {automaton} è pronto",
                    "Gli automi {automaton} sono pronti",
                    "I due automi {automaton} sono pronti",
                ],
                [
                    "L'automata progettato per {purpose} è pronto",
                    "Gli automi progettati per {purpose} sono pronti",
                    "I due automi progettati per {purpose} sono pronti",
                ],
                [
                    "L'automata di tipo {type} è pronto",
                    "Gli automi di tipo {type} sono pronti",
                    "I due automi di tipo {type} sono pronti",
                    "I numerosi automi di tipo {type} sono pronti",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=[
                "Messaggio sugli automi basati sulle grammatiche di Chomsky"
            ],
        ),
        "1104": Message(
            "1104",
            "Il fiore ha un bel colore",
            plurals=["I fiori hanno bei colori", "I due fiori hanno bei colori"],
            alternatives=[
                [
                    "Il {flower} ha un bel colore",
                    "I {flower} hanno bei colori",
                    "I due {flower} hanno bei colori",
                ],
                [
                    "Il {flower} di colore {color} è magnifico",
                    "I {flower} di colore {color} sono magnifici",
                    "I due {flower} di colore {color} sono magnifici",
                ],
                [
                    "Il {flower} dell'anno {year} è splendido",
                    "I {flower} dell'anno {year} sono splendidi",
                    "I due {flower} dell'anno {year} sono splendidi",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=["Messaggio sui fiori"],
        ),
        "1105": Message(
            "1105",
            "La montagna è ricoperta di neve",
            plurals=[
                "Le montagne sono ricoperte di neve",
                "Queste due montagne sono ricoperte di neve",
            ],
            alternatives=[
                [
                    "La montagna {mountain} è ricoperta di neve",
                    "Le montagne {mountain} sono ricoperte di neve",
                    "Queste due montagne {mountain} sono ricoperte di neve",
                ],
                [
                    "La montagna situata a {location} è ricoperta di neve",
                    "Le montagne situate a {location} sono ricoperte di neve",
                    "Queste due montagne situate a {location} sono ricoperte di neve",
                ],
                [
                    "La montagna in {season} è ricoperta di neve",
                    "Le montagne in {season} sono ricoperte di neve",
                    "Queste due montagne in {season} sono ricoperte di neve",
                    "Le numerose montagne in {season} sono ricoperte di neve",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=["Messaggio sulle montagne"],
        ),
        "1106": Message(
            "1106",
            "Il viaggio è lungo",
            plurals=["I viaggi sono lunghi", "Questi due viaggi sono lunghi"],
            alternatives=[
                [
                    "Il viaggio verso {destination} è lungo",
                    "I viaggi verso {destination} sono lunghi",
                    "Questi due viaggi verso {destination} sono lunghi",
                ],
                [
                    "Il viaggio con {companion} è lungo",
                    "I viaggi con {companion} sono lunghi",
                    "Questi due viaggi con {companion} sono lunghi",
                ],
                [
                    "Il viaggio di {duration} giorni è lungo",
                    "I viaggi di {duration} giorni sono lunghi",
                    "Questi due viaggi di {duration} giorni sono lunghi",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=["Messaggio sui viaggi"],
        ),
        "1107": Message(
            "1107",
            "L'automata funziona",
            plurals=["Gli automi funzionano", "I due automi funzionano"],
            alternatives=[
                [
                    "L'automata {automaton} funziona",
                    "Gli automi {automaton} funzionano",
                    "I due automi {automaton} funzionano",
                ],
                [
                    "L'automata per {purpose} funziona",
                    "Gli automi per {purpose} funzionano",
                    "I due automi per {purpose} funzionano",
                ],
                [
                    "L'automata di tipo {type} funziona",
                    "Gli automi di tipo {type} funzionano",
                    "I due automi di tipo {type} funzionano",
                    "I numerosi automi di tipo {type} funzionano",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=[
                "Messaggio sugli automi basati sulle grammatiche di Chomsky"
            ],
        ),
        "1108": Message(
            "1108",
            "Il fiore profuma bene",
            plurals=["I fiori profumano bene", "Questi due fiori profumano bene"],
            alternatives=[
                [
                    "Il {flower} profuma bene",
                    "I {flower} profumano bene",
                    "Questi due {flower} profumano bene",
                ],
                [
                    "Il {flower} di colore {color} profuma bene",
                    "I {flower} di colore {color} profumano bene",
                    "Questi due {flower} di colore {color} profumano bene",
                ],
                [
                    "Il {flower} coltivato nel {year} profuma bene",
                    "I {flower} coltivati nel {year} profumano bene",
                    "Questi due {flower} coltivati nel {year} profumano bene",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=["Messaggio sui fiori"],
        ),
        "1109": Message(
            "1109",
            "La montagna è innevata",
            plurals=["Le montagne sono innevate", "Queste due montagne sono innevate"],
            alternatives=[
                [
                    "La montagna {mountain} è innevata",
                    "Le montagne {mountain} sono innevate",
                    "Queste due montagne {mountain} sono innevate",
                ],
                [
                    "La montagna situata a {location} è innevata",
                    "Le montagne situate a {location} sono innevate",
                    "Queste due montagne situate a {location} sono innevate",
                ],
                [
                    "La montagna in {season} è innevata",
                    "Le montagne in {season} sono innevate",
                    "Queste due montagne in {season} sono innevate",
                    "Le numerose montagne in {season} sono innevate",
                ],
            ],
            locations=[],
            flags=["python-format"],
            user_comments=["Messaggio sulle montagne"],
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
