from enum import Enum
from fli.models.airport import Airport

class City(Enum):
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
    NYC = "/m/02_286"
    CHI = "/m/01_d4"

# Mapping for easy lookup
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

# Major airports for each city
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

def resolve_location(code: str):
    """Resolve IATA code or special city mapping.
    
    Returns:
        tuple: (value, type_id) where type_id is 4 for entity IDs and 0 for airports.
    
    Raises:
        KeyError: If the code cannot be resolved.
    """
    code = code.strip().upper()
    
    # Try city mapping first
    if code in CITY_MAPPING:
        return CITY_MAPPING[code], 4
    
    # Try Airport enum
    try:
        return Airport[code], 0
    except KeyError:
        raise KeyError(f"Unknown airport/city code '{code}'")
