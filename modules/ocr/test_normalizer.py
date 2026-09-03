from data_normalizer import (
    convert_mrz_date,
    normalize_nationality
)


print(
    "DOB:",
    convert_mrz_date("590923", "dob")
)

print(
    "Expiry:",
    convert_mrz_date("211010", "expiry")
)

print(
    "Nationality:",
    normalize_nationality("IND")
)