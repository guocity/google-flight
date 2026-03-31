"""GetShoppingResults RPC helper.

This module loads recorded Google Flights GetShoppingResults fixtures and uses
the shared HTTP client for live requests when needed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from collections import deque
from functools import lru_cache
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote_plus

from fli.models import Airline, Airport, DateSearchFilters, FlightLeg, FlightResult, FlightSearchFilters
import time

ENDPOINT_PATH = "/_/FlightsFrontendUi/data/travel.frontend.flights.FlightsFrontendService/GetShoppingResults"
ENDPOINT_URL = f"https://www.google.com{ENDPOINT_PATH}"
FIXTURE_DIR = Path(__file__).resolve().parents[2] / "requests_json" / "GetShoppingResults"
client = None


@dataclass(frozen=True)
class ShoppingResultsFixture:
    """Recorded request/response pair for GetShoppingResults."""

    name: str
    request_path: Path
    response_path: Path
    request: Any
    response: Any


class Client:
    """HTTP client with built-in rate limiting, retry and user agent impersonation functionality."""

    DEFAULT_HEADERS = {
        "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
    }

    _MAX_CALLS = 10
    _PERIOD_SECONDS = 1.0
    _MAX_RETRIES = 3

    def __init__(self):
        """Initialize a new client session with default headers."""
        from curl_cffi import requests

        self._client = requests.Session()
        self._client.headers.update(self.DEFAULT_HEADERS)
        self._recent_calls: deque[float] = deque()

    def __del__(self):
        """Clean up client session on deletion."""
        if hasattr(self, "_client"):
            self._client.close()

    def _throttle(self) -> None:
        """Enforce a simple 10 requests/second limit."""
        now = time.monotonic()
        while self._recent_calls and now - self._recent_calls[0] >= self._PERIOD_SECONDS:
            self._recent_calls.popleft()

        if len(self._recent_calls) >= self._MAX_CALLS:
            sleep_for = self._PERIOD_SECONDS - (now - self._recent_calls[0])
            if sleep_for > 0:
                time.sleep(sleep_for)

            now = time.monotonic()
            while self._recent_calls and now - self._recent_calls[0] >= self._PERIOD_SECONDS:
                self._recent_calls.popleft()

        self._recent_calls.append(time.monotonic())

    def _request(self, method: str, url: str, **kwargs: Any) -> Any:
        """Make a rate-limited request with simple retry handling."""
        last_error: Exception | None = None
        for attempt in range(self._MAX_RETRIES):
            self._throttle()
            try:
                response = getattr(self._client, method)(url, **kwargs)
                response.raise_for_status()
                return response
            except Exception as exc:
                last_error = exc
                if attempt >= self._MAX_RETRIES - 1:
                    break
                time.sleep(2**attempt)

        raise Exception(f"{method.upper()} request failed: {str(last_error)}") from last_error

    def get(self, url: str, **kwargs: Any) -> Any:
        """Make a rate-limited GET request with automatic retries."""
        return self._request("get", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> Any:
        """Make a rate-limited POST request with automatic retries."""
        return self._request("post", url, **kwargs)


def get_client() -> Client:
    """Get or create a shared HTTP client instance."""
    global client
    if not client:
        client = Client()
    return client


def _load_json(path: Path) -> Any:
    """Load a JSON fixture from disk."""
    return json.loads(path.read_text(encoding="utf-8"))


def _fixture_name(path: Path) -> str:
    """Convert a request fixture path into its logical fixture name."""
    return path.stem


@lru_cache(maxsize=1)
def load_fixtures() -> tuple[ShoppingResultsFixture, ...]:
    """Load all recorded GetShoppingResults fixtures."""
    fixtures: list[ShoppingResultsFixture] = []
    for request_path in sorted(FIXTURE_DIR.glob("*.json")):
        if request_path.name.endswith(".response.json"):
            continue

        response_path = request_path.with_name(f"{request_path.stem}.response.json")
        if not response_path.exists():
            raise FileNotFoundError(
                f"Missing response fixture for {request_path.name}: {response_path.name}"
            )

        fixtures.append(
            ShoppingResultsFixture(
                name=_fixture_name(request_path),
                request_path=request_path,
                response_path=response_path,
                request=_load_json(request_path),
                response=_load_json(response_path),
            )
        )

    return tuple(fixtures)


@lru_cache(maxsize=1)
def _fixture_index() -> dict[str, ShoppingResultsFixture]:
    """Index fixtures by name for quick lookups."""
    return {fixture.name: fixture for fixture in load_fixtures()}


def _fixture_by_name(name: str) -> ShoppingResultsFixture:
    """Return a fixture by name."""
    fixture = _fixture_index().get(name)
    if fixture is None:
        raise ValueError(f"Unknown GetShoppingResults fixture: {name}")
    return fixture


def list_fixture_names() -> tuple[str, ...]:
    """Return the available recorded fixture names."""
    return tuple(fixture.name for fixture in load_fixtures())


def load_request_fixture(name: str) -> Any:
    """Return the recorded request payload for a fixture name."""
    return _fixture_by_name(name).request


def load_response_fixture(name: str) -> Any:
    """Return the recorded response payload for a fixture name."""
    return _fixture_by_name(name).response


def load_request_fixture_json(name: str) -> str:
    """Return the recorded request payload for a fixture name as JSON text."""
    return json.dumps(load_request_fixture(name), indent=2, ensure_ascii=False)


def load_response_fixture_json(name: str) -> str:
    """Return the decoded recorded shopping result for a fixture name as JSON text."""
    return json.dumps(_shopping_results_json_data(load_response_fixture(name)), indent=2, ensure_ascii=False)


def _resolve_named_fixture(payload: Any) -> Any:
    """Resolve a string fixture name to the recorded request payload."""
    if isinstance(payload, str):
        fixture = _fixture_index().get(payload)
        if fixture is not None:
            return fixture.request
    return payload


def _decode_model_payload(payload: FlightSearchFilters | DateSearchFilters) -> Any:
    """Convert a typed filter model into the recorded request payload shape."""
    wrapped_payload = json.loads(unquote_plus(payload.encode()))
    if not isinstance(wrapped_payload, list) or len(wrapped_payload) != 2:
        raise ValueError("Encoded filter payload is not a valid Google Flights request")

    request_payload = wrapped_payload[1]
    if not isinstance(request_payload, str):
        raise ValueError("Encoded filter payload did not contain a JSON request body")

    return json.loads(request_payload)


def _extract_form_request(body: str) -> str | None:
    """Extract the f.req payload from a Google RPC form body."""
    if "f.req=" not in body:
        return None

    value = body.split("f.req=", 1)[1]
    if "&" in value:
        value = value.split("&", 1)[0]
    return value


def _decode_request_payload(payload: Any) -> Any:
    """Normalize raw endpoint input into a JSON-compatible Python object."""
    if isinstance(payload, (FlightSearchFilters, DateSearchFilters)):
        return _decode_model_payload(payload)

    payload = _resolve_named_fixture(payload)

    if isinstance(payload, (list, dict)):
        return payload

    if isinstance(payload, (bytes, bytearray)):
        payload_text = payload.decode("utf-8")
    elif isinstance(payload, str):
        payload_text = payload
    else:
        raise TypeError(
            "Request payload must be a JSON string, form body, bytes, list, dict, or fixture name"
        )

    payload_text = payload_text.strip()
    if not payload_text:
        raise ValueError("Request payload cannot be empty")

    try:
        return json.loads(payload_text)
    except json.JSONDecodeError:
        form_request = _extract_form_request(payload_text)
        if form_request is None:
            raise ValueError("Request payload must be JSON or contain f.req") from None

        for candidate in (form_request, unquote_plus(form_request)):
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue

        raise ValueError("Unable to parse the GetShoppingResults request payload") from None


def _request_body_from_payload(payload: Any) -> str:
    """Serialize a request payload into the Google RPC form body."""
    if isinstance(payload, (FlightSearchFilters, DateSearchFilters)):
        encoded_payload = payload.encode()
    else:
        request_payload = _decode_request_payload(payload)
        formatted_json = json.dumps(request_payload, separators=(',', ':'), ensure_ascii=False)
        encoded_payload = quote(
            json.dumps([None, formatted_json], separators=(',', ':'), ensure_ascii=False)
        )

    return f"f.req={encoded_payload}"


def resolve_fixture(payload: Any) -> ShoppingResultsFixture:
    """Return the recorded fixture that matches the given request payload."""
    decoded_payload = _decode_request_payload(payload)
    for fixture in load_fixtures():
        if decoded_payload == fixture.request:
            return fixture

    raise ValueError("Unsupported GetShoppingResults request payload")


def resolve_response(payload: Any) -> Any:
    """Return the recorded response payload that matches the given request."""
    return resolve_fixture(payload).response


def resolve_response_json(payload: Any) -> str:
    """Return the decoded recorded shopping result that matches the given request as JSON text."""
    return json.dumps(_shopping_results_json_data(resolve_response(payload)), indent=2, ensure_ascii=False)


def _strip_google_rpc_prefix(text: str) -> str:
    """Remove the standard Google RPC anti-XSSI prefix from response text."""
    prefix = ")]}'"
    if text.startswith(prefix):
        text = text[len(prefix) :].lstrip("\r\n")
    return text


def decode_google_rpc_response(text: str) -> Any:
    """Decode a Google RPC response body into Python data."""
    cleaned_text = _strip_google_rpc_prefix(text)
    try:
        return json.loads(cleaned_text)
    except json.JSONDecodeError as exc:
        raise ValueError("Google RPC response was not valid JSON") from exc


def _find_rpc_frame(payload: Any) -> list[Any] | None:
    """Find the first wrb.fr frame anywhere in the decoded response."""
    if isinstance(payload, list):
        if len(payload) >= 3 and isinstance(payload[0], str) and payload[0] == "wrb.fr":
            return payload

        for item in payload:
            frame = _find_rpc_frame(item)
            if frame is not None:
                return frame

    return None


def _extract_rpc_payload(payload: Any) -> Any:
    """Extract the useful payload from a Google RPC response envelope."""
    frame = _find_rpc_frame(payload)
    if frame is None:
        return payload

    if len(frame) > 2:
        inner_payload = frame[2]
        if isinstance(inner_payload, str):
            try:
                return json.loads(inner_payload)
            except json.JSONDecodeError:
                return inner_payload
        if inner_payload is not None:
            return inner_payload

    if len(frame) > 5:
        return {
            "success": False,
            "error": _serialize_rpc_error(frame),
        }

    return payload


def _find_type_url(payload: Any) -> str | None:
    """Find the first protobuf type URL in a nested payload."""
    if isinstance(payload, str) and payload.startswith("type.googleapis.com/"):
        return payload.removeprefix("type.googleapis.com/")

    if isinstance(payload, list):
        for item in payload:
            found = _find_type_url(item)
            if found is not None:
                return found

    if isinstance(payload, dict):
        for item in payload.values():
            found = _find_type_url(item)
            if found is not None:
                return found

    return None


def _serialize_rpc_error(frame: list[Any]) -> dict[str, Any]:
    """Convert a Google RPC error frame into a JSON-friendly error object."""
    error_payload = frame[5] if len(frame) > 5 else None
    return {
        "rpc_id": frame[0],
        "type": _find_type_url(error_payload) or "google_rpc_error",
        "message": "Google Flights returned an error response",
        "details": error_payload,
    }


def _extract_flight_items(payload: Any) -> list[Any]:
    """Extract raw flight items from a decoded Google Flights shopping payload."""
    if not isinstance(payload, list):
        return []

    flight_items: list[Any] = []

    for index in (2, 3):
        if len(payload) <= index:
            continue

        slot = payload[index]
        if isinstance(slot, list) and slot and isinstance(slot[0], list):
            flight_items.extend(slot[0])

    return flight_items


def _serialize_search_result(result: FlightResult | tuple[FlightResult, FlightResult]) -> dict[str, Any]:
    """Serialize a single search result or round-trip pair."""
    if isinstance(result, tuple):
        outbound, return_flight = result
        return {
            "price": outbound.price,
            "currency": "USD",
            "duration": outbound.duration + return_flight.duration,
            "stops": outbound.stops + return_flight.stops,
            "outbound": outbound.model_dump(mode="json"),
            "return": return_flight.model_dump(mode="json"),
        }

    return result.model_dump(mode="json")


def _parse_price(data: list) -> float:
    """Extract price from raw flight data."""
    try:
        if data[1] and data[1][0]:
            return data[1][0][-1]
    except (IndexError, TypeError):
        pass
    return 0.0


def _parse_datetime(date_arr: list[int], time_arr: list[int]) -> datetime:
    """Convert date and time arrays to datetime."""
    if not any(x is not None for x in date_arr) or not any(x is not None for x in time_arr):
        raise ValueError("Date and time arrays must contain at least one non-None value")

    return datetime(*(x or 0 for x in date_arr), *(x or 0 for x in time_arr))


def _parse_airline(airline_code: str) -> Airline:
    """Convert airline code to Airline enum."""
    if airline_code[0].isdigit():
        airline_code = f"_{airline_code}"
    return getattr(Airline, airline_code)


def _parse_airport(airport_code: str) -> Airport:
    """Convert airport code to Airport enum."""
    return getattr(Airport, airport_code)


def _parse_flights_data(data: list) -> FlightResult:
    """Parse raw flight data into a structured FlightResult."""
    flight = FlightResult(
        price=_parse_price(data),
        duration=data[0][9],
        stops=len(data[0][2]) - 1,
        legs=[
            FlightLeg(
                airline=_parse_airline(fl[22][0]),
                flight_number=fl[22][1],
                departure_airport=_parse_airport(fl[3]),
                arrival_airport=_parse_airport(fl[6]),
                departure_datetime=_parse_datetime(fl[20], fl[8]),
                arrival_datetime=_parse_datetime(fl[21], fl[10]),
                duration=fl[11],
            )
            for fl in data[0][2]
        ],
    )
    return flight


def _shopping_results_json_data(payload: Any) -> Any:
    """Convert a GetShoppingResults payload into actual JSON-friendly data."""
    decoded_payload = _extract_rpc_payload(payload)

    if isinstance(decoded_payload, dict) and decoded_payload.get("success") is False:
        return decoded_payload

    flight_items = _extract_flight_items(decoded_payload)
    if flight_items:
        results: list[FlightResult] = []
        for item in flight_items:
            try:
                results.append(_parse_flights_data(item))
            except Exception:
                continue

        if results:
            return {
                "success": True,
                "data_source": "google_flights",
                "count": len(results),
                "results": [_serialize_search_result(result) for result in results],
            }

    return decoded_payload


def request_live_response(payload: Any, client: Any | None = None) -> Any:
    """Send a live GetShoppingResults request using the shared HTTP client."""
    active_client = client or get_client()
    response = active_client.post(
        url=ENDPOINT_URL,
        data=_request_body_from_payload(payload),
        impersonate="chrome",
        allow_redirects=True,
    )
    response.raise_for_status()
    return decode_google_rpc_response(response.text)


def request_live_response_json(payload: Any, client: Any | None = None) -> str:
    """Send a live GetShoppingResults request and return decoded shopping-result JSON."""
    return json.dumps(
        _shopping_results_json_data(request_live_response(payload, client=client)),
        indent=2,
        ensure_ascii=False,
    )


def get_shopping_results(payload: Any, client: Any | None = None) -> Any:
    """Return a recorded or live GetShoppingResults response."""
    try:
        return resolve_response(payload)
    except (TypeError, ValueError):
        return request_live_response(payload, client=client)


def get_shopping_results_json(payload: Any, client: Any | None = None) -> str:
    """Return a recorded or live GetShoppingResults response as decoded JSON text."""
    return json.dumps(
        _shopping_results_json_data(get_shopping_results(payload, client=client)),
        indent=2,
        ensure_ascii=False,
    )


def render_response_json(payload: Any, client: Any | None = None) -> str:
    """Render the matching decoded response payload as pretty-printed JSON."""
    return json.dumps(
        _shopping_results_json_data(get_shopping_results(payload, client=client)),
        indent=2,
        ensure_ascii=False,
    )


def print_response(payload: Any, client: Any | None = None) -> None:
    """Print the matching response payload as JSON."""
    print(render_response_json(payload, client=client))


def all_responses_as_json() -> str:
    """Render every recorded response as decoded JSON in a single object."""
    responses = {
        fixture.name: _shopping_results_json_data(fixture.response) for fixture in load_fixtures()
    }
    return json.dumps(responses, indent=2, ensure_ascii=False)


def print_all_responses() -> None:
    """Print all recorded responses as a single JSON object."""
    print(all_responses_as_json())


def main() -> None:
    """Print all recorded responses as JSON."""
    print_all_responses()


if __name__ == "__main__":
    main()