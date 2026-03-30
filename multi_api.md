# Google Flights Multi-City CLI API Reference

This document describes the `fli.cli.multi_api` tool, which supports complex multi-city flight searches.

## Usage

```bash
uv run python3 -m fli.cli.multi_api <origin> <dest> <date> [<origin> <dest> <date> ...] [options]
```

### Positional Arguments

- `triplets`: One or more sets of 3 arguments: `<origin> <destination> <date>`.
  - `origin`: IATA code or City Name.
  - `dest`: IATA code or City Name.
  - `date`: `M/D` or `YYYY-MM-DD`.

### Options

Supports the same options as the standard API (`--adults`, `--cabin`, `--stops`, etc.).

## Examples

### 1. 3-City Journey
```bash
uv run python3 -m fli.cli.multi_api NYC SFO 4/1 SFO LAS 4/5 LAS NYC 4/10
```

### 2. Complex Multi-City with Filters
```bash
uv run python3 -m fli.cli.multi_api NYC PAR 5/1 PAR LON 5/10 LON NYC 5/15 --cabin BUSINESS --stops NON_STOP
```

## Output Format

The tool returns a JSON object with a `"results"` key. Each result represents a complete journey.

### JSON Structure

```json
{
  "results": [
    {
      "segments": [
        {
          "legs": [...],
          "price": 770.0,
          "duration": 371,
          "stops": 0
        },
        {
          "legs": [...],
          "price": 770.0,
          "duration": 111,
          "stops": 0
        },
        {
          "legs": [...],
          "price": 770.0,
          "duration": 308,
          "stops": 0
        }
      ],
      "total_price": 770.0
    }
  ]
}
```

### Field Definitions

- `segments`: An array of flight result objects, one for each leg of the multi-city trip.
- `total_price`: The estimated total price for the entire journey (extracted from the first segment's pricing data).
