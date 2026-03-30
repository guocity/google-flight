# Google Flights CLI API Reference

This document describes the `api.py` CLI tool, which provides a JSON-based interface to the Google Flights search engine.

## Usage

```bash
uv run python3 -m fli.cli.api <origin> <dest> <outbound> [inbound] [options]
```

### Positional Arguments

- `origin`: IATA code (e.g., `JFK`) or City Name (`NYC`, `Beijing`, `Shanghai`, etc.).
- `dest`: IATA code for the destination (e.g., `LAS`).
- `outbound`: Departure date in `M/D` (defaults to current year) or `YYYY-MM-DD` format.
- `inbound`: (Optional) Return date in `M/D` or `YYYY-MM-DD` format.

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--return-date` | Date | None | Enables Round-Trip search. Format: `M/D` or `YYYY-MM-DD`. |
| `--adults` | Int | 1 | Number of adult passengers. |
| `--children` | Int | 0 | Number of children (2-12). |
| `--infants-lap`| Int | 0 | Infants on lap. |
| `--infants-seat`| Int | 0 | Infants in seat. |
| `--cabin` | Enum | `ECONOMY` | `ECONOMY`, `PREMIUM_ECONOMY`, `BUSINESS`, `FIRST`. |
| `--stops` | Enum | `ANY` | `ANY`, `NON_STOP`, `ONE_STOP`, `TWO_PLUS`. |
| `--price` | Int | None | Maximum price in USD. |
| `--airlines` | String| None | Comma-separated IATA codes (e.g., `AA,DL,UA`). |
| `--max-duration`| Int | None | Maximum total travel time in minutes. |
| `--sort` | Enum | `NONE` | `NONE`, `TOP_FLIGHTS`, `CHEAPEST`, `DEPARTURE`, `ARRIVAL`, `DURATION`. |
| `--outbound-time`| String| None | Outbound departure window in `HH-HH` (e.g., `06-12`). |
| `--return-time` | String| None | Return departure window in `HH-HH`. |

## Examples

### 1. Simple One-Way Search
```bash
uv run python3 -m fli.cli.api NYC LAX 4/1
```

### 2. Round-Trip with Filters
```bash
uv run python3 -m fli.cli.api NYC LAS 4/1 --return-date 4/10 --adults 2 --cabin BUSINESS --stops NON_STOP
```

### 3. Price-Limited Search with Preferred Airlines
```bash
uv run python3 -m fli.cli.api JFK SFO 5/15 --price 400 --airlines AA,UA
```

### 4. Specific Time Windows
```bash
uv run python3 -m fli.cli.api EWR ORD 6/1 --outbound-time 08-11
```

## Output Format

The tool returns a JSON object with a `"results"` key containing an array of flight objects.

### JSON Structure

#### One-Way Result
```json
{
  "results": [
    {
      "legs": [
        {
          "airline": "United Airlines",
          "flight_number": "889",
          "departure_airport": "Beijing Capital International Airport",
          "arrival_airport": "San Francisco International Airport",
          "departure_datetime": "2026-04-01T17:25:00",
          "arrival_datetime": "2026-04-01T14:05:00",
          "duration": 700
        }
      ],
      "price": 696.0,
      "duration": 700,
      "stops": 0
    }
  ]
}
```

#### Round-Trip Result
```json
{
  "results": [
    {
      "outbound": {
        "legs": [...],
        "price": 562.0,
        "duration": 349,
        "stops": 0
      },
      "return": {
        "legs": [...],
        "price": 562.0,
        "duration": 308,
        "stops": 0
      },
      "total_price": 562.0
    }
  ]
}
```

### Field Definitions

- `legs`: Array of individual flight segments (for connecting flights).
- `price`: Price for that specific journey (One-way or individual direction).
- `total_price`: (Round-trip only) The combined price for both outbound and return.
- `duration`: Total travel time in minutes.
- `stops`: Number of layovers.
- `departure_datetime` / `arrival_datetime`: ISO 8601 formatted timestamps.
