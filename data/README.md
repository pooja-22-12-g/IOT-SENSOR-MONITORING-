# Dataset

Source: [UCI Air Quality](https://archive.ics.uci.edu/dataset/360/air+quality) (De Vito et al., 2008).

- `AirQualityUCI.csv` — full file used by this project (9,357 hourly rows after skipping blank lines).
- `sample_48h.csv` — first 48 hours from that same file, for tests.

Missing measurements are tagged `-200`. Decimal commas in the original file are converted to floats during ingest.
