# Restricted analytical-data schema

The source dataset is not distributed. An authorised CSV must contain these fields:

| Field | Purpose |
|---|---|
| adm2_pcode | Stable district identifier used for grouping |
| Year, Month | Monthly temporal index |
| COUNT_OBJECTID | Aggregated monthly case count and target source |
| Incidence_100k | District-month incidence per 100,000 |
| population | District population denominator |
| area_sqkm | District area used for population density |
| Rainfall_mm | Monthly rainfall predictor |
| Temperature_C | Monthly temperature predictor |

No person-level identifiers, coordinates, credentials or restricted source records are included in this package.
