# Google Flights: Response Decoding

This document explains how the Google Flights API response is structured and how it's parsed into structured flight data.

## Envelope Structure: `batchexecute`

The API returns data in the `batchexecute` format. The core flight results are usually within the `wrb.fr` response chunk.

```javascript
/* batchexecute response (high-level) */
)
]
}'
59649
[["wrb.fr", null, "[[null, ...]]"]]
```

The third element of the `wrb.fr` array is a JSON-encoded string. Once decoded, it contains the search results payload.

## Main Results Payload (`encoded_filters_res`)

The decoded search results payload is a list where specific indices hold the flight listings.

| Index | Name | Content |
| :--- | :--- | :--- |
| **2** | `best_flights` | List of flights classified by Google as "Best" (Top flights). |
| **3** | `other_flights` | List of other available flights, often including cheaper but less convenient options. |

Each of these is a nested list: `[ [Flight_1, Flight_2, ...] ]`.

## Flight Data Object (Root Index 0 & 1)

Each flight item is a complex nested list. The most important parts are:

### Price (`index 1`)
- **Index:** `1 -> 0 -> index-1`
- **Example:** `item[1][0][-1]` (The last element of the first sub-list in index 1).

### Flight Metadata (`index 0`)
| Index | Field | Description |
| :--- | :--- | :--- |
| **2** | `legs` | A list of individual flight legs (see below). |
| **9** | `duration` | Total travel time in minutes. |
| **14** | `score` | Google's internal quality score (optional). |

## Flight Leg Detail (`item[0][2][...]`)

Each element in the `legs` list represents a single non-stop flight segment.

| Index | Field | Data Format | Description |
| :--- | :--- | :--- | :--- |
| **3** | `departure_airport` | String | IATA code (e.g., "JFK"). |
| **6** | `arrival_airport` | String | IATA code (e.g., "LAX"). |
| **8** | `departure_time` | `[hour, minute]` | Local time at origin. |
| **10** | `arrival_time` | `[hour, minute]` | Local time at destination. |
| **11** | `leg_duration` | Integer | Duration in minutes. |
| **20** | `departure_date` | `[YYYY, MM, DD]` | Local date at origin. |
| **21** | `arrival_date` | `[YYYY, MM, DD]` | Local date at destination. |
| **22** | `airline_info` | `[Code, FlightNumber]` | e.g., `["DL", "421"]`. |
| **23** | `aircraft_info` | String | Aircraft model (e.g., "Boeing 737"). |

---

## Example Decoding (One-way JFK to LAX)

```json
[
  [
    null,
    null,
    [
      [
        null, null, null, "JFK", null, null, "LAX", null, [6, 0], null, [9, 15], 375, 
        null, null, null, null, null, null, null, null, [2026, 3, 30], [2026, 3, 30], 
        ["DL", "421"], "Boeing 737"
      ]
    ],
    null, null, null, null, null, null, 375, null, null, null, null, 8.5
  ],
  [
    [null, null, null, "USD", 249.0]
  ]
]
```
- **Price:** $249.00
- **Departure:** JFK at 06:00
- **Arrival:** LAX at 09:15
- **Total Duration:** 375 mins (6h 15m)
- **Airline:** Delta (DL 421)
