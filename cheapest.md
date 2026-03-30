# Google Flights: "Cheapest" vs "Best" Request Analysis

This document outlines the differences between a standard "Best" flight search and a "Cheapest" flight search in the Google Flights API.

## Core Differences in `f.req`

The `f.req` parameter is a double-encoded JSON structure: `[null, "inner_json_string"]`. When the `inner_json_string` is decoded into a list, the following indices control the search behavior:

| Index | Field Name | "Best" (Top Flights) | "Cheapest" (All Flights) | Description |
| :--- | :--- | :--- | :--- | :--- |
| **0** | **Session Token** | `[null, null, null, "TOKEN"]` | `[]` | Used for stateful/paginated results. Cheapest usually clears this. |
| **2** | **Sort Order** | `0` (or `1`) | `2` | Corresponds to `SortBy.CHEAPEST` enum. |
| **5** | **Request Mode** | `1` | `2` | **Critical:** `1` triggers "Best" heuristic; `2` triggers "All flights" (Cheapest) view. |

---

## Decoded Payloads (Comparison)

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

## How to Encode the Request

To programmatically generate these requests, follow this 3-step encoding process used in `fli/models/google_flights/flights.py`:

1.  **Construct the List:** Create the nested list structure shown above.
2.  **Stringify (Compact):** Convert the list to a JSON string with no spaces (separators `("," , ":")`).
3.  **Wrap and URL Encode:**
    ```python
    inner_json = json.dumps(my_list, separators=(",", ":"))
    wrapped = [None, inner_json]
    payload = "f.req=" + urllib.parse.quote(json.dumps(wrapped, separators=(",", ":")))
    ```

## Implementation Note
To correctly implement the "Cheapest" feature in the `fli` library, update the `format()` method in `fli/models/google_flights/flights.py` to dynamically set the last index:

```python
# Change from:
2, # constant

# To:
2 if self.sort_by == SortBy.CHEAPEST else 1,
```
