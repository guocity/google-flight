"""Tests for the GetShoppingResults helper module."""

import json
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote_plus

import pytest

from fli.api.GetShoppingResults import (
    ENDPOINT_URL,
    all_responses_as_json,
    decode_google_rpc_response,
    get_shopping_results,
    get_shopping_results_json,
    list_fixture_names,
    load_request_fixture_json,
    load_response_fixture_json,
    render_response_json,
    request_live_response,
    request_live_response_json,
    resolve_response,
    resolve_response_json,
)
from fli.models import (
    Airline,
    Airport,
    City,
    DateSearchFilters,
    FlightLeg,
    FlightResult,
    FlightSearchFilters,
    FlightSegment,
    MaxStops,
    PassengerInfo,
    SeatType,
    SortBy,
    TripType,
)

FIXTURE_DIR = (
    Path(__file__).resolve().parents[2] / "requests_json" / "GetShoppingResults"
)


def load_fixture(name: str):
    """Load a JSON fixture from the recorded request/response folder."""
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_list_fixture_names() -> None:
    """The module should discover all recorded GetShoppingResults fixtures."""
    assert list_fixture_names() == ("cheapest", "multi-city", "return", "round_trip")


def test_all_responses_as_json_round_trips() -> None:
    """The aggregate response output should be valid JSON."""
    rendered = all_responses_as_json()
    payload = json.loads(rendered)

    assert set(payload) == {"cheapest", "multi-city", "return", "round_trip"}
    assert payload["cheapest"]["success"] is True
    assert payload["cheapest"]["data_source"] == "google_flights"


def test_fixture_json_helpers_round_trip() -> None:
    """Recorded fixture helpers should also be available as JSON text."""
    request_payload = json.loads(load_request_fixture_json("cheapest"))
    response_payload = json.loads(load_response_fixture_json("cheapest"))

    assert request_payload == load_fixture("cheapest.json")
    assert response_payload["success"] is True
    assert response_payload["data_source"] == "google_flights"
    assert response_payload["count"] > 0
    assert isinstance(response_payload["results"], list)


@pytest.mark.parametrize(
    "fixture_name",
    ["cheapest", "multi-city", "return", "round_trip"],
)
def test_resolve_response_matches_recorded_response(fixture_name: str) -> None:
    """Each recorded request should resolve to its matching response payload."""
    request_payload = load_fixture(f"{fixture_name}.json")
    expected_response = load_fixture(f"{fixture_name}.response.json")

    assert resolve_response(request_payload) == expected_response


def test_resolve_response_json_matches_recorded_response() -> None:
    """Recorded responses should also be renderable as JSON text."""
    request_payload = load_fixture("return.json")
    response_payload = json.loads(resolve_response_json(request_payload))

    assert response_payload["success"] is True
    assert response_payload["data_source"] == "google_flights"
    assert response_payload["count"] > 0
    assert isinstance(response_payload["results"], list)


def test_request_live_response_accepts_city_model_payload(monkeypatch) -> None:
    """A City-backed FlightSearchFilters payload should be encoded for live requests."""

    class DummyResponse:
        def __init__(self, text: str):
            self.text = text

        def raise_for_status(self) -> None:
            return None

    class DummyClient:
        def __init__(self):
            self.calls: list[tuple[str, dict]] = []

        def post(self, url: str, **kwargs):
            self.calls.append((url, kwargs))
            return DummyResponse(
                ")]}'\n" + json.dumps([["live"]])
            )

    dummy_client = DummyClient()
    monkeypatch.setattr("fli.api.GetShoppingResults.get_client", lambda: dummy_client)

    filters = FlightSearchFilters(
        passenger_info=PassengerInfo(
            adults=1,
            children=0,
            infants_in_seat=0,
            infants_on_lap=0,
        ),
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

    assert request_live_response(filters) == [["live"]]
    assert json.loads(request_live_response_json(filters)) == [["live"]]
    assert dummy_client.calls[0][0] == ENDPOINT_URL
    assert dummy_client.calls[0][1]["data"].startswith("f.req=")


def test_get_shopping_results_prefers_recorded_fixture(monkeypatch) -> None:
    """Recorded requests should be served from fixtures without using the live client."""
    request_payload = load_fixture("round_trip.json")

    monkeypatch.setattr(
        "fli.api.GetShoppingResults.get_client",
        lambda: pytest.fail("live client should not be used for recorded fixtures"),
    )

    assert get_shopping_results(request_payload) == load_fixture("round_trip.response.json")
    response_payload = json.loads(get_shopping_results_json(request_payload))
    assert response_payload["success"] is True
    assert response_payload["data_source"] == "google_flights"
    assert response_payload["count"] > 0
    assert isinstance(response_payload["results"], list)


def test_request_live_response_uses_shared_client(monkeypatch) -> None:
    """Live requests should be sent with the shared HTTP client from search.client."""

    class DummyResponse:
        def __init__(self, text: str):
            self.text = text

        def raise_for_status(self) -> None:
            return None

    class DummyClient:
        def __init__(self):
            self.calls: list[tuple[str, dict]] = []

        def post(self, url: str, **kwargs):
            self.calls.append((url, kwargs))
            return DummyResponse(
                ")]}'\n" + json.dumps([["live"]])
            )

    dummy_client = DummyClient()
    monkeypatch.setattr("fli.api.GetShoppingResults.get_client", lambda: dummy_client)

    payload = DateSearchFilters(
        passenger_info=PassengerInfo(
            adults=1,
            children=0,
            infants_in_seat=0,
            infants_on_lap=0,
        ),
        flight_segments=[
            FlightSegment(
                departure_airport=[[Airport.JFK, 0]],
                arrival_airport=[[Airport.BUF, 0]],
                travel_date="2026-04-01",
            )
        ],
        stops=MaxStops.NON_STOP,
        seat_type=SeatType.ECONOMY,
        from_date="2026-04-01",
        to_date="2026-04-10",
    )
    assert request_live_response(payload) == [["live"]]
    assert json.loads(get_shopping_results_json(payload)) == [["live"]]
    assert dummy_client.calls[0][0] == ENDPOINT_URL
    assert dummy_client.calls[0][1]["data"].startswith("f.req=")
    assert isinstance(json.loads(unquote_plus(dummy_client.calls[0][1]["data"][6:])), list)


def test_request_live_response_accepts_selected_flight_payload(monkeypatch) -> None:
    """A typed round-trip payload with a selected flight should be encoded and sent."""

    class DummyResponse:
        def __init__(self, text: str):
            self.text = text

        def raise_for_status(self) -> None:
            return None

    class DummyClient:
        def __init__(self):
            self.calls: list[tuple[str, dict]] = []

        def post(self, url: str, **kwargs):
            self.calls.append((url, kwargs))
            return DummyResponse(
                ")]}'\n" + json.dumps([["live"]])
            )

    dummy_client = DummyClient()
    monkeypatch.setattr("fli.api.GetShoppingResults.get_client", lambda: dummy_client)

    selected_leg = FlightLeg(
        airline=Airline.B6,
        flight_number="1202",
        departure_airport=Airport.JFK,
        arrival_airport=Airport.BUF,
        departure_datetime=datetime(2026, 3, 30, 19, 14),
        arrival_datetime=datetime(2026, 3, 30, 20, 53),
        duration=99,
    )
    selected_flight = FlightResult(legs=[selected_leg], price=0.0, duration=99, stops=0)
    payload = FlightSearchFilters(
        trip_type=TripType.ROUND_TRIP,
        passenger_info=PassengerInfo(
            adults=1,
            children=0,
            infants_in_seat=0,
            infants_on_lap=0,
        ),
        flight_segments=[
            FlightSegment(
                departure_airport=[[Airport.JFK, 0]],
                arrival_airport=[[Airport.BUF, 0]],
                travel_date="2026-04-01",
                selected_flight=selected_flight,
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

    assert request_live_response(payload) == [["live"]]
    assert json.loads(get_shopping_results_json(payload)) == [["live"]]
    assert dummy_client.calls[0][0] == ENDPOINT_URL
    assert dummy_client.calls[0][1]["data"].startswith("f.req=")


def test_decode_google_rpc_response_strips_prefix() -> None:
    """The Google RPC prefix should be removed before JSON decoding."""
    assert decode_google_rpc_response(")]}'\n[1, 2, 3]") == [1, 2, 3]


def test_render_response_json_round_trips() -> None:
    """Pretty-printed response output should still parse back to the same payload."""
    request_payload = load_fixture("cheapest.json")
    response_payload = json.loads(render_response_json(request_payload))

    assert response_payload["success"] is True
    assert response_payload["data_source"] == "google_flights"
    assert response_payload["count"] > 0
    assert isinstance(response_payload["results"], list)