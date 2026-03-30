import sys
import json
import argparse
from datetime import datetime
from fli.models import FlightSearchFilters, PassengerInfo, Airline
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

def main():
    parser = argparse.ArgumentParser(description="Google Flights Multi-City API CLI")
    
    # Required: Origin Destination Date (repeating)
    parser.add_argument("triplets", nargs="+", help="Origin Destination Date triplets (e.g. JFK LAX 4/1 SFO ORD 4/5)")
    
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

    args = parser.parse_args()

    # Parse triplets
    if len(args.triplets) % 3 != 0:
        print("Error: Arguments must be in sets of 3: <origin> <dest> <date>", file=sys.stderr)
        sys.exit(1)

    segments = []
    for i in range(0, len(args.triplets), 3):
        origin_raw = args.triplets[i]
        dest_raw = args.triplets[i+1]
        date_raw = args.triplets[i+2]
        
        try:
            origin_val, origin_type = resolve_location(origin_raw)
            dest_val, dest_type = resolve_location(dest_raw)
            travel_date = parse_date(date_raw)
            
            segments.append(
                FlightSegment.model_construct(
                    departure_airport=[[origin_val, origin_type]],
                    arrival_airport=[[dest_val, dest_type]],
                    travel_date=travel_date
                )
            )
        except (KeyError, argparse.ArgumentTypeError) as e:
            print(f"Error at triplet {i//3 + 1}: {str(e)}", file=sys.stderr)
            sys.exit(1)

    # Determine trip type
    if len(segments) == 1:
        trip_type = TripType.ONE_WAY
    elif len(segments) == 2 and segments[0].arrival_airport == segments[1].departure_airport and segments[0].departure_airport == segments[1].arrival_airport:
        trip_type = TripType.ROUND_TRIP
    else:
        trip_type = TripType.MULTI_CITY

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
        results = searcher.search(filters, top_n=2)
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))
        return

    if not results:
        print(json.dumps({"results": []}, indent=2))
        return

    output = []
    for journey in results:
        if isinstance(journey, tuple):
            journey_data = []
            for segment_res in journey:
                journey_data.append(json.loads(segment_res.model_dump_json()))
            
            output.append({
                "segments": journey_data,
                "total_price": journey[-1].price
            })
        else:
            output.append(json.loads(journey.model_dump_json()))

    print(json.dumps({"results": output}, indent=2))

if __name__ == "__main__":
    main()
