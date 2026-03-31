# GetShoppingResults

`fli.api.GetShoppingResults` is the low-level helper for the Google Flights `GetShoppingResults` RPC.
It supports both raw RPC envelopes and decoded shopping-results JSON. If you want actual JSON results, use the `*_json` helpers or `render_response_json()`.

## Endpoint

- `ENDPOINT_PATH`: `/_/FlightsFrontendUi/data/travel.frontend.flights.FlightsFrontendService/GetShoppingResults`
- `ENDPOINT_URL`: `https://www.google.com` plus `ENDPOINT_PATH`

## Function Reference

| Function | Returns | Use |
| --- | --- | --- |
| `load_fixtures()` | recorded fixtures | Load every captured request/response pair. |
| `list_fixture_names()` | tuple of names | List the recorded fixture names. |
| `load_request_fixture(name)` | Python data | Get a recorded request payload. |
| `load_request_fixture_json(name)` | JSON text | Get a recorded request payload as JSON. |
| `load_response_fixture(name)` | Python data | Get a recorded response payload. |
| `load_response_fixture_json(name)` | JSON text | Decode a recorded response into shopping-results JSON. |
| `resolve_fixture(payload)` | fixture record | Find the recorded fixture for a payload. |
| `resolve_response(payload)` | Python data | Get the recorded response for a payload. |
| `resolve_response_json(payload)` | JSON text | Get the recorded response for a payload as JSON. |
| `decode_google_rpc_response(text)` | Python data | Decode a live Google RPC response body. |
| `request_live_response(payload)` | Python data | Send a live request and get parsed data back. |
| `request_live_response_json(payload)` | JSON text | Send a live request and get decoded shopping-results JSON. |
| `get_shopping_results(payload)` | Python data | Try recorded fixtures first, then live requests, returning the raw RPC envelope. |
| `get_shopping_results_json(payload)` | JSON text | Try recorded fixtures first, then return decoded shopping-results JSON. |
| `render_response_json(payload)` | JSON text | Format the matching decoded response as pretty JSON. |
| `print_response(payload)` | stdout | Print one response as pretty JSON. |
| `all_responses_as_json()` | JSON text | Return every recorded response as one JSON object. |
| `print_all_responses()` | stdout | Print every recorded response as JSON. |
| `main()` | stdout | Script entry point; prints every recorded response as JSON. |

## JSON First

If you want JSON text instead of the raw Google envelope, start with these helpers:

```python
from fli.api import get_shopping_results_json, request_live_response_json, resolve_response_json
from fli.models import Airport, FlightSearchFilters, FlightSegment, MaxStops, PassengerInfo, SeatType, SortBy

filters = FlightSearchFilters(
    passenger_info=PassengerInfo(adults=1),
    flight_segments=[
        FlightSegment(
            departure_airport=[[Airport.JFK, 0]],
            arrival_airport=[[Airport.BUF, 0]],
            travel_date="2026-04-01",
        )
    ],
    stops=MaxStops.ANY,
    seat_type=SeatType.ECONOMY,
    sort_by=SortBy.CHEAPEST,
)

response_json = get_shopping_results_json(filters)
recorded_json = resolve_response_json("cheapest")
live_json = request_live_response_json(filters)
```

To convert the JSON text back into Python data:

```python
import json

response = json.loads(response_json)
```

## Recorded Fixtures

The recorded fixture names are:

- `cheapest`
- `multi-city`
- `return`
- `round_trip`

Inspect the captured request JSON and the decoded response JSON for a fixture:

```python
from fli.api import list_fixture_names, load_request_fixture_json, load_response_fixture_json

print(list_fixture_names())
print(load_request_fixture_json("cheapest"))
print(load_response_fixture_json("cheapest"))
```

To print every recorded response as JSON:

```bash
uv run python fli/api/GetShoppingResults.py > get_shopping_results.json
```

## Live JSON Examples

Use typed model objects when you want to hit the live Google Flights endpoint. The examples below use `get_shopping_results_json()` so the returned value is decoded JSON with `success`, `count`, and `results` fields.

### Cheapest One-Way

```python
from fli.api import get_shopping_results_json
from fli.models import Airport, City, FlightSearchFilters, FlightSegment, MaxStops, PassengerInfo, SeatType, SortBy

filters = FlightSearchFilters(
    passenger_info=PassengerInfo(adults=1),
    flight_segments=[
        FlightSegment(
            departure_airport=[[City.NYC, 4]],
            arrival_airport=[[Airport.BUF, 0]],
            travel_date="2026-04-01",
        )
    ],
    stops=MaxStops.ANY,
    seat_type=SeatType.ECONOMY,
    sort_by=SortBy.CHEAPEST,
)

response_json = get_shopping_results_json(filters)
```

### Multi-City

```python
from fli.api import get_shopping_results_json
from fli.models import Airport, City, FlightSearchFilters, FlightSegment, MaxStops, PassengerInfo, SeatType, SortBy, TripType

filters = FlightSearchFilters(
    trip_type=TripType.MULTI_CITY,
    passenger_info=PassengerInfo(adults=1),
    flight_segments=[
        FlightSegment(
            departure_airport=[[City.NYC, 4]],
            arrival_airport=[[Airport.BUF, 0]],
            travel_date="2026-04-01",
        ),
        FlightSegment(
            departure_airport=[[Airport.BUF, 0]],
            arrival_airport=[[City.NYC, 4]],
            travel_date="2026-04-05",
        ),
    ],
    stops=MaxStops.NON_STOP,
    seat_type=SeatType.ECONOMY,
    sort_by=SortBy.CHEAPEST,
)

response_json = get_shopping_results_json(filters)
```

### Round Trip

```python
from fli.api import get_shopping_results_json
from fli.models import Airport, FlightSearchFilters, FlightSegment, MaxStops, PassengerInfo, SeatType, SortBy, TripType

filters = FlightSearchFilters(
    trip_type=TripType.ROUND_TRIP,
    passenger_info=PassengerInfo(adults=1),
    flight_segments=[
        FlightSegment(
            departure_airport=[[Airport.JFK, 0]],
            arrival_airport=[[Airport.BUF, 0]],
            travel_date="2026-04-01",
        ),
        FlightSegment(
            departure_airport=[[Airport.BUF, 0]],
            arrival_airport=[[Airport.JFK, 0]],
            travel_date="2026-04-07",
        ),
    ],
    stops=MaxStops.NON_STOP,
    seat_type=SeatType.ECONOMY,
    sort_by=SortBy.CHEAPEST,
)

response_json = get_shopping_results_json(filters)
```

### Return Options After Selecting an Outbound Flight

When you want return options for a specific outbound flight, set `selected_flight` on the first segment.

```python
from datetime import datetime

from fli.api import get_shopping_results_json
from fli.models import Airline, Airport, FlightLeg, FlightResult, FlightSearchFilters, FlightSegment, MaxStops, PassengerInfo, SeatType, SortBy, TripType

selected_outbound = FlightResult(
    legs=[
        FlightLeg(
            airline=Airline.B6,
            flight_number="1202",
            departure_airport=Airport.JFK,
            arrival_airport=Airport.BUF,
            departure_datetime=datetime(2026, 3, 30, 19, 14),
            arrival_datetime=datetime(2026, 3, 30, 20, 53),
            duration=99,
        )
    ],
    price=99.0,
    duration=99,
    stops=0,
)

filters = FlightSearchFilters(
    trip_type=TripType.ROUND_TRIP,
    passenger_info=PassengerInfo(adults=1),
    flight_segments=[
        FlightSegment(
            departure_airport=[[Airport.JFK, 0]],
            arrival_airport=[[Airport.BUF, 0]],
            travel_date="2026-04-01",
            selected_flight=selected_outbound,
        ),
        FlightSegment(
            departure_airport=[[Airport.BUF, 0]],
            arrival_airport=[[Airport.JFK, 0]],
            travel_date="2026-04-07",
        ),
    ],
    stops=MaxStops.NON_STOP,
    seat_type=SeatType.ECONOMY,
    sort_by=SortBy.CHEAPEST,
)

response_json = get_shopping_results_json(filters)
```

## Notes

- `request_live_response()` and `get_shopping_results()` return the raw Google RPC envelope.
- `request_live_response_json()` and `get_shopping_results_json()` return decoded shopping-results JSON.
- `render_response_json()` is the simplest wrapper when you already have a payload and want the decoded JSON immediately.