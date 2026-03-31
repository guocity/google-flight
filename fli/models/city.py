"""City for Google Flights style routes."""

from enum import Enum


class City(Enum):
    """Selected city codes mapped to Google Freebase IDs."""

    NYC = "/m/02_286"
    CHI = "/m/01_d4"
    BEIJING = "/m/01914"
    SHANGHAI = "/m/06wjf"
    TOKYO = "/m/07dfk"
    DELHI = "/m/0dlv0"
    MUMBAI = "/m/04vmp"
    SAO_PAULO = "/m/022pfm"
    MEXICO_CITY = "/m/04sqj"
    CAIRO = "/m/01w2v"
    SEOUL = "/m/0hsqf"
    LONDON = "/m/04jpl"
    PARIS = "/m/05qtj"

__all__ = ["City"]

# do not import just for reference, not for use
CITY_MAPPING = {
    "NYC": City.NYC.value,
    "CHI": City.CHI.value,
    "BEIJING": City.BEIJING.value,
    "SHANGHAI": City.SHANGHAI.value,
    "TOKYO": City.TOKYO.value,
    "DELHI": City.DELHI.value,
    "MUMBAI": City.MUMBAI.value,
    "SAO PAULO": City.SAO_PAULO.value,
    "SAO_PAULO": City.SAO_PAULO.value,
    "MEXICO CITY": City.MEXICO_CITY.value,
    "MEXICO_CITY": City.MEXICO_CITY.value,
    "CAIRO": City.CAIRO.value,
    "SEOUL": City.SEOUL.value,
    "LONDON": City.LONDON.value,
    "PARIS": City.PARIS.value,
}

# do not import just for reference, not for use
CITY_AIRPORTS = {
    "NYC": ["JFK", "LGA", "EWR"],
    "CHI": ["ORD", "MDW"],
    "BEIJING": ["PEK", "PKX"],
    "SHANGHAI": ["PVG", "SHA"],
    "TOKYO": ["HND", "NRT"],
    "DELHI": ["DEL"],
    "MUMBAI": ["BOM"],
    "SAO PAULO": ["GRU", "CGH", "VCP"],
    "MEXICO CITY": ["MEX", "NLU"],
    "CAIRO": ["CAI"],
    "SEOUL": ["ICN", "GMP"],
    "LONDON": ["LHR", "LGW", "STN", "LCY", "LTN", "SEN"],
    "PARIS": ["CDG", "ORY", "BVA"],
}