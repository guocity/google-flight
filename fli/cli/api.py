import sys
import json
import argparse
from datetime import datetime
from fli.models import FlightSearchFilters, PassengerInfo, Airport, Airline
from fli.models.google_flights.base import (
    TripType, FlightSegment, SeatType, MaxStops, SortBy, 
    PriceLimit, TimeRestrictions
)
from fli.models.google_flights.city import resolve_location
from fli.search.flights import SearchFlights

def parse_date(date_str):
    """Parse M/D or YYYY-MM-DD into YYYY-MM-DD. Defaults to current year for M/D."""
    try:
        if "-" in date_str:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        else:
            current_year = datetime.now().year
            dt = datetime.strptime(f"{current_year}/{date_str}", "%Y/%m/%d")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format '{date_str}'. Use M/D or YYYY-MM-DD")

def parse_time_range(tr):
    if not tr: return None
    try:
        parts = tr.split("-")
        return int(parts[0]), int(parts[1])
    except:
        raise argparse.ArgumentTypeError("Time range must be HH-HH (e.g. 6-22)")

def main():
    parser = argparse.ArgumentParser(description="Google Flights API CLI")
    
    # Required
    parser.add_argument("origin", type=str, help="Origin IATA code or City Name")
    parser.add_argument("dest", type=str, help="Destination IATA code or City Name")
    parser.add_argument("outbound", type=parse_date, help="Outbound date (M/D or YYYY-MM-DD)")
    
    # Optional positional return date
    parser.add_argument("inbound", type=parse_date, nargs="?", help="Optional return date (M/D or YYYY-MM-DD)")
    
    # Optional flags
    parser.add_argument("--return-date", type=parse_date, help="Return date (alternative to positional)")
    
    # Passenger Info
    parser.add_argument("--adults", type=int, default=1)
    parser.add_argument("--children", type=int, default=0)
    parser.add_argument("--infants-lap", type=int, default=0)
    parser.add_argument("--infants-seat", type=int, default=0)
    
    # Preferences
    parser.add_argument("--cabin", type=str, choices=["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"], default="ECONOMY")
    parser.add_argument("--stops", type=str, choices=["ANY", "NON_STOP", "ONE_STOP", "TWO_PLUS"], default="ANY")
    parser.add_argument("--price", type=int, help="Max price in USD")
    parser.add_argument("--airlines", type=str, help="Comma-separated airline codes (e.g. AA,DL)")
    parser.add_argument("--max-duration", type=int, help="Max duration in minutes")
    parser.add_argument("--sort", type=str, choices=["NONE", "TOP_FLIGHTS", "CHEAPEST", "DEPARTURE", "ARRIVAL", "DURATION"], default="NONE")
    
    # Time Windows
    parser.add_argument("--outbound-time", type=str, help="Outbound departure window HH-HH")
    parser.add_argument("--return-time", type=str, help="Return departure window HH-HH")

    args = parser.parse_args()

    # Resolve locations
    try:
        origin_val, origin_type = resolve_location(args.origin)
        dest_val, dest_type = resolve_location(args.dest)
    except KeyError as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

    # Resolve return date (positional wins)
    return_date = args.inbound or args.return_date

    # Trip type
    trip_type = TripType.ROUND_TRIP if return_date else TripType.ONE_WAY

    # Passenger Info
    passenger_info = PassengerInfo(
        adults=args.adults,
        children=args.children,
        infants_on_lap=args.infants_lap,
        infants_in_seat=args.infants_seat
    )

    # Enums
    seat_type = SeatType[args.cabin]
    
    stops_map = {
        "ANY": MaxStops.ANY,
        "NON_STOP": MaxStops.NON_STOP,
        "ONE_STOP": MaxStops.ONE_STOP_OR_FEWER,
        "TWO_PLUS": MaxStops.TWO_OR_FEWER_STOPS
    }
    stops = stops_map[args.stops]

    sort_map = {
        "NONE": SortBy.NONE,
        "TOP_FLIGHTS": SortBy.TOP_FLIGHTS,
        "CHEAPEST": SortBy.CHEAPEST,
        "DEPARTURE": SortBy.DEPARTURE_TIME,
        "ARRIVAL": SortBy.ARRIVAL_TIME,
        "DURATION": SortBy.DURATION
    }
    sort_by = sort_map[args.sort]

    # Optional filters
    price_limit = PriceLimit(max_price=args.price) if args.price else None
    
    airline_list = None
    if args.airlines:
        airline_list = []
        for code in args.airlines.split(","):
            try:
                airline_list.append(Airline[code.strip().upper()])
            except KeyError:
                print(f"Error: Unknown airline code '{code}'", file=sys.stderr)
                sys.exit(1)

    # Build segments
    out_time = None
    if args.outbound_time:
        start, end = parse_time_range(args.outbound_time)
        out_time = TimeRestrictions(earliest_departure=start, latest_departure=end)

    segments = [
        FlightSegment.model_construct(
            departure_airport=[[origin_val, origin_type]],
            arrival_airport=[[dest_val, dest_type]],
            travel_date=args.outbound,
            time_restrictions=out_time
        )
    ]

    if return_date:
        ret_time = None
        if args.return_time:
            start, end = parse_time_range(args.return_time)
            ret_time = TimeRestrictions(earliest_departure=start, latest_departure=end)
            
        segments.append(
            FlightSegment.model_construct(
                departure_airport=[[dest_val, dest_type]],
                arrival_airport=[[origin_val, origin_type]],
                travel_date=return_date,
                time_restrictions=ret_time
            )
        )

    # Final Filters
    filters = FlightSearchFilters.model_construct(
        trip_type=trip_type,
        passenger_info=passenger_info,
        flight_segments=segments,
        seat_type=seat_type,
        stops=stops,
        sort_by=sort_by,
        price_limit=price_limit,
        airlines=airline_list,
        max_duration=args.max_duration
    )

    searcher = SearchFlights()
    try:
        results = searcher.search(filters)
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))
        return

    if not results:
        print(json.dumps({"results": []}, indent=2))
        return

    output = []
    for res in results:
        if isinstance(res, tuple):
            out_res, ret_res = res
            output.append({
                "outbound": json.loads(out_res.model_dump_json()),
                "return": json.loads(ret_res.model_dump_json()),
                "total_price": ret_res.price
            })
        else:
            output.append(json.loads(res.model_dump_json()))

    print(json.dumps({"results": output}, indent=2))

if __name__ == "__main__":
    main()
