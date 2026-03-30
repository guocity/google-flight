## Google Flights: "Cheapest" vs "Best" Request Analysis

This document outlines the differences between a standard "Best" flight search and a "Cheapest" flight search in the Google Flights API.

## Core Differences in `f.req`

The `f.req` parameter is a double-encoded JSON structure: `[null, "inner_json_string"]`. When the `inner_json_string` is decoded into a list, the following indices control the search behavior:

| Index | Field Name | "Best" (Top Flights) | "Cheapest" (All Flights) | Description |
| :--- | :--- | :--- | :--- | :--- |
| **0** | **Session Token** | `[null, null, null, "TOKEN"]` | `[]` | Used for stateful/paginated results. Cheapest usually clears this. |
| **2** | **Sort Order** | `0` (or `1`) | `2` | Corresponds to `SortBy.CHEAPEST` enum. |
| **5** | **Request Mode** | `1` | `2` | **Critical:** `1` triggers "Best" heuristic; `2` triggers "All flights" (Cheapest) view. |

---

## Protobuf Representation

While Google Flights uses JSON-over-HTTP for these requests, the structure mirrors a Protobuf definition. Below is a conceptual mapping of the request into `.proto` messages based on the observed indices.

```protobuf
syntax = "proto3";

message FlightsRequest {
  repeated string session_token = 1;      // Root Index 0
  FlightSearchFilters filters = 2;       // Root Index 1
  SortBy sort_by = 3;                    // Root Index 2
  int32 constant_zero_1 = 4;             // Root Index 3
  int32 constant_zero_2 = 5;             // Root Index 4
  RequestMode mode = 6;                  // Root Index 5 (1: Best, 2: Cheapest)
}

message FlightSearchFilters {
  reserved 1, 3, 4, 8, 9, 10, 11, 12, 14, 15, 16;
  TripType trip_type = 3;                // Filter Index 2
  SeatType seat_type = 6;                // Filter Index 5
  PassengerCounts passengers = 7;        // Filter Index 6
  PriceLimit price_limit = 8;            // Filter Index 7
  repeated FlightSegment segments = 14;  // Filter Index 13
  int32 constant_one = 18;               // Filter Index 17
}

message FlightSegment {
  LocationInfo departure = 1;            // Segment Index 0
  LocationInfo arrival = 2;              // Segment Index 1
  TimeRestrictions time_limits = 3;      // Segment Index 2
  MaxStops max_stops = 4;                // Segment Index 3
  repeated string airlines = 5;          // Segment Index 4
  reserved 6;
  string travel_date = 7;                // Segment Index 6 (YYYY-MM-DD)
  MaxDuration max_duration = 8;          // Segment Index 7
  SelectedFlight selection = 9;          // Segment Index 8
  repeated string layover_airports = 10; // Segment Index 9
  reserved 11, 12;
  int32 layover_duration = 13;           // Segment Index 12
  reserved 14;
  int32 segment_code = 15;               // Segment Index 14
}

enum RequestMode {
  BEST = 1;
  ALL_FLIGHTS_CHEAPEST = 2;
}

enum SortBy {
  NONE = 0;
  TOP_FLIGHTS = 1;
  CHEAPEST = 2;
  DEPARTURE_TIME = 3;
  ARRIVAL_TIME = 4;
  DURATION = 5;
}
}

---

## Raw Index Mapping (JSBP Format)

The Google Flights API uses "JSBP" (JavaScript Binary Protocol), where Protobuf messages are serialized as JSON arrays. The **Index** in the array corresponds to the **Protobuf Tag - 1**.

Below is the raw structure with labeled indices for the "Cheapest" request:

```javascript
/* FlightsRequest (Root) */
[
  0: [],                   // Tag 1: session_token (Empty for fresh search)
  1: [                     // Tag 2: filters (FlightSearchFilters)
       0: null,            //   Tag 1: reserved
       1: null,            //   Tag 2: reserved
       2: 2,               //   Tag 3: trip_type (2: ONE_WAY)
       3: null,            //   Tag 4: reserved
       4: [],              //   Tag 5: reserved
       5: 1,               //   Tag 6: seat_type (1: ECONOMY)
       6: [1, 0, 0, 0],    //   Tag 7: passengers [Adult, Child, Inf_Lap, Inf_Seat]
       7: [null, 500],     //   Tag 8: price_limit [null, USD_Amount]
       ...
      13: [                //   Tag 14: segments (repeated FlightSegment)
            [              //     Segment Index 0
               0: [[["/m/02_286", 4]]], // Tag 1: Departure (NYC, City)
               1: [[["BUF", 0]]],       // Tag 2: Arrival (BUF, Airport)
               2: null,                 // Tag 3: time_restrictions
               3: 0,                    // Tag 4: max_stops (0: ANY)
               4: null,                 // Tag 5: airlines
               ...
               6: "2026-03-30",         // Tag 7: travel_date
               ...
              14: 3                     // Tag 15: segment_code (3: Outbound)
            ]
          ],
      17: 1                //   Tag 18: constant_one
     ],
  2: 2,                    // Tag 3: sort_by (2: CHEAPEST)
  3: 0,                    // Tag 4: constant_zero_1
  4: 0,                    // Tag 5: constant_zero_2
  5: 2                     // Tag 6: mode (2: ALL_FLIGHTS_CHEAPEST)
]
```

---

## Detailed Field Reference

 (The "Protobuf" Structure)

The inner JSON structure is a deeply nested list. Here is a field-by-field breakdown of each level.

### 1. Root Level
| Index | Type | Description |
| :--- | :--- | :--- |
| 0 | List | **Session/Context Token:** Used for pagination and keeping state between requests. `[]` for a fresh search. |
| 1 | List | **Filter Object:** Contains all search parameters (airports, dates, passengers, etc). |
| 2 | Integer | **Sort By:** `0`: None, `1`: Top Flights, `2`: Cheapest, `3`: Departure, `4`: Arrival, `5`: Duration. |
| 3 | Integer | **Constant:** Usually `0`. |
| 4 | Integer | **Constant:** Usually `0`. |
| 5 | Integer | **Mode:** `1` for "Best/Top Flights" heuristic; `2` for "All flights/Cheapest" list. |

### 2. Filter Object (Root Index 1)
| Index | Type | Description |
| :--- | :--- | :--- |
| 2 | Integer | **Trip Type:** `1`: Round Trip, `2`: One Way, `3`: Multi-City. |
| 5 | Integer | **Seat Type:** `1`: Economy, `2`: Premium Economy, `3`: Business, `4`: First. |
| 6 | List | **Passenger Counts:** `[Adults, Children, Infants_on_Lap, Infants_in_Seat]`. |
| 7 | List | **Price Limit:** `[null, MaxPrice]` (in USD). |
| 13 | List | **Segments:** A list of Segment objects (see below). |
| 17 | Integer | **Constant:** Hardcoded to `1`. |

### 3. Segment Object (Filter Index 13)
| Index | Type | Description |
| :--- | :--- | :--- |
| 0 | List | **Departure Info:** Nested list containing `[[[IATA/CityID, Type]]]`. Type 4 is City, 0 is Airport. |
| 1 | List | **Arrival Info:** Nested list containing `[[[IATA/CityID, Type]]]`. |
| 2 | List | **Time Restrictions:** `[EarliestDep, LatestDep, EarliestArr, LatestArr]` (hours from midnight). |
| 3 | Integer | **Max Stops:** `0`: Any, `1`: Non-stop, `2`: 1 stop or fewer, `3`: 2 stops or fewer. |
| 4 | List | **Airlines:** List of allowed airline codes (e.g., `["AA", "DL"]`). |
| 6 | String | **Travel Date:** Date in `YYYY-MM-DD` format. |
| 7 | List | **Max Duration:** Single element list `[Minutes]`. |
| 8 | List | **Selected Flight:** Used when searching for subsequent segments (e.g., return flights for a specific outbound). |
| 9 | List | **Layover Airports:** List of restricted/preferred layover airport codes. |
| 12 | Integer | **Layover Duration:** Maximum layover time in minutes. |
| 14 | Integer | **Segment Code:** `3` for standard/outbound; `1` for the last/return segment. |

---

## Decoded Payloads (Comparison)
...

### 1. Best / Top Flights (`requests/curl`)
```json
[
  [null, null, null, "HJE1EcIW..."], // Session Token
  [
    null, null, 2, null, [], 1, [1, 0, 0, 0], // One-way, Economy, 1 Adult
    null, null, null, null, null, null,
    [
      [
        [[["/m/02_286", 4]]], // NYC
        [[["BUF", 0]]],       // BUF
        null, 0, null, null, "2026-03-30", 
        null, null, null, null, null, null, null, 3
      ]
    ],
    null, null, null, 1
  ],
  0, // SortBy.NONE
  0,
  0,
  1  // Mode: Best
]
```

### 2. Cheapest Flights (`requests/cheapest_curl`)
```json
[
  [], // Empty Token
  [
    null, null, 2, null, [], 1, [1, 0, 0, 0], // Filters (Same as above)
    null, null, null, null, null, null,
    [
      [
        [[["/m/02_286", 4]]],
        [[["BUF", 0]]],
        null, 0, null, null, "2026-03-30",
        null, null, null, null, null, null, null, 3
      ]
    ],
    null, null, null, 1
  ],
  2, // SortBy.CHEAPEST
  0,
  0,
  2  // Mode: All/Cheapest
]
```

---

### 3. Multi-City Search (`requests/multi-city_curl`)

In a multi-city search, the `FlightSearchFilters` message contains a `repeated` list of `FlightSegment` objects.

**Multi-City Request (JSBP Index Mapping)**
```javascript
/* FlightsRequest (Root) */
[
  0: [],                   // Tag 1: session_token
  1: [                     // Tag 2: filters (FlightSearchFilters)
       2: 3,               //   Tag 3: trip_type (3: MULTI_CITY)
       5: 1,               //   Tag 6: seat_type (1: ECONOMY)
       6: [1, 0, 0, 0],    //   Tag 7: passengers [Adult, Child, Inf_Lap, Inf_Seat]
       13: [               //   Tag 14: segments (repeated FlightSegment)
            // Segment 1: NYC -> BUF (Mar 30)
            [0: [[["/m/02_286", 4]]], 1: [[["BUF", 0]]], 6: "2026-03-30", 14: 3],
            // Segment 2: BUF -> NYC (Apr 03)
            [0: [[["BUF", 0]]], 1: [[["/m/02_286", 4]]], 6: "2026-04-03", 14: 1],
            // Segment 3: NYC -> BUF (Apr 07)
            [0: [[["/m/02_286", 4]]], 1: [[["BUF", 0]]], 6: "2026-04-07", 14: 1],
            // Segment 4: BUF -> NYC (Apr 11)
            [0: [[["BUF", 0]]], 1: [[["/m/02_286", 4]]], 6: "2026-04-11", 14: 1]
          ],
       17: 1               //   Tag 18: constant_one
     ],
  2: 0,                    // Tag 3: sort_by (0: NONE)
  3: 0, 4: 0, 5: 1         // Tag 6: mode (1: BEST)
]
```

---

## 4. Response Decoding Protobuf (`multi-city_reponse`)

The Google Flights response is a `batchexecute` payload. The inner flight results map to the following Protobuf-style structure.

### Response Protobuf Definition
```protobuf
message FlightsResponse {
  string results_token = 1;              // Index 0: Pagination/Context Token
  repeated Flight best_flights = 3;      // Index 2: "Best" Flights List
  repeated Flight other_flights = 4;     // Index 3: "Other" Flights List
}

message Flight {
  FlightMetadata metadata = 1;           // Index 0: Timing and Leg details
  PriceInfo price = 2;                   // Index 1: Pricing details
}

message FlightMetadata {
  repeated Leg legs = 3;                 // Metadata Index 2: Individual flight legs
  int32 total_duration = 10;             // Metadata Index 9: Total duration in mins
  double quality_score = 15;             // Metadata Index 14: Google Ranking Score
}

message Leg {
  string departure_airport = 4;          // Leg Index 3: IATA (e.g., "JFK")
  string arrival_airport = 7;            // Leg Index 6: IATA (e.g., "LAX")
  TimeArray departure_time = 9;          // Leg Index 8: [Hour, Minute]
  TimeArray arrival_time = 11;           // Leg Index 10: [Hour, Minute]
  int32 duration = 12;                   // Leg Index 11: Duration in mins
  DateArray departure_date = 21;         // Leg Index 20: [Year, Month, Day]
  DateArray arrival_date = 22;           // Leg Index 21: [Year, Month, Day]
  AirlineInfo airline = 23;              // Leg Index 22: [Code, FlightNumber]
}
```

### Decoded Response Example (Multi-City)
```javascript
/* FlightsResponse Chunk */
[
  0: "HdCAnwPyjQDwAK...",    // Tag 1: results_token
  2: [                       // Tag 3: best_flights
       [                     //   Flight 1
         0: [                //     Tag 1: metadata (FlightMetadata)
              2: [           //       Tag 3: legs (repeated Leg)
                   [3: "NYC", 6: "BUF", 8: [6,0], 20: [2026,3,30], 22: ["DL","421"]],
                   [3: "BUF", 6: "NYC", 8: [14,30], 20: [2026,4,3], 22: ["AA","123"]]
                 ],
              9: 595         //       Tag 10: total_duration
            ],
         1: [[null, null, null, "USD", 450.0]] // Tag 2: price (PriceInfo)
       ]
     ]
]
```

---

## Implementation Status: ✅ Implemented

The "Cheapest" search mode has been integrated into the `fli` library. The `FlightSearchFilters.format()` method now dynamically switches the API mode based on the selected sort order.

### Usage via CLI
To fetch the cheapest results, use the `--sort CHEAPEST` flag or the `--cheapest` shortcut:

```bash
# Option 1: Standard sort flag
uv run python3 -m fli.cli.api NYC BUF 3/30 --sort CHEAPEST

# Option 2: Shortcut flag
uv run python3 -m fli.cli.api NYC BUF 3/30 --cheapest
```

### Encoding Logic
The encoding process remains consistent:
1.  **Construct the List:** Create the nested list structure.
2.  **Stringify (Compact):** Convert to a JSON string (no spaces).
3.  **Wrap and URL Encode:** `f.req=%5Bnull%2C%22...%22%5D`

## Implementation Detail
In `fli/models/google_flights/flights.py`, the main filter structure now uses:
```python
2 if self.sort_by == SortBy.CHEAPEST else 1
```
This ensures that when `CHEAPEST` is selected, Google returns the full list of available flights sorted by price, rather than just the "Best" flights heuristic.
