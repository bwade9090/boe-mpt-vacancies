import pandas as pd

from boe_vac.parse import (
    normalise_monthly,
    parse_metadata,
    parse_table,
    split_metadata_and_table,
)

SAMPLE_CSV = """""Title","UK Vacancies (thousands) - Total"
"CDID","AP2Y"
"Source dataset ID","LMS"
"PreUnit",""
"Unit",""
"Release date","12-08-2025"
"Next release","16 September 2025"
"Important notes",
"2022","1243"
"2023","1022"
"2024","862"
"2024 Q4","806"
"2025 Q1","783"
"2025 Q2","725"
"2025 APR","738"
"2025 MAY","725"
"2025 JUN","718"
"""


def test_split_and_parse():
    meta_lines, table_lines = split_metadata_and_table(SAMPLE_CSV)
    meta = parse_metadata(meta_lines)
    assert meta["CDID"] == "AP2Y"
    assert meta["Release date"] == "12-08-2025"
    df = parse_table(table_lines)
    assert list(df.columns) == ["Period", "Value"]
    assert len(df) == 9


def test_normalise_monthly():
    # Write temp file
    from boe_vac.parse import ParsedCSV

    parsed = ParsedCSV(
        metadata=parse_metadata(split_metadata_and_table(SAMPLE_CSV)[0]),
        data=parse_table(split_metadata_and_table(SAMPLE_CSV)[1]),
    )
    df_monthly = normalise_monthly(parsed)
    # Only monthly rows retained (2 rows)
    assert len(df_monthly) == 3
    assert "vintage_date" in df_monthly.columns
    assert pd.api.types.is_datetime64_any_dtype(df_monthly["vintage_date"])
    assert df_monthly["vintage_date"].iloc[0].month == 8
