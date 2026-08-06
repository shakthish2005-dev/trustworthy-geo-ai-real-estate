# Dataset card

## Purpose

`properties.csv` is the academic demonstration dataset inherited from the original third-year project. It supports UI demonstrations, comparable-property exploration, model training, and testing.

## Important limitations

- The 1,500 records are synthetic; they are not live listings or registered-sale records.
- Coordinates are deterministically generated near each city centre by the application. They are not parcel coordinates or cadastral boundaries.
- The `is_fraud` field is a simulated label and must not be treated as evidence of fraud.
- Price estimates and anomaly scores are illustrative decision support, not certified valuation or legal findings.
- Do not use this dataset to pay a token, execute an agreement, approve a loan, or certify ownership.

## Production replacement path

Replace the CSV with licensed or first-party data and preserve source, timestamp, consent, licence, geographic accuracy, and lineage metadata. Retrain and validate each model by city and property type before enabling production recommendations.

