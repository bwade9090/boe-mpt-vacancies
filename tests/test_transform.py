from boe_vac.transform import build_long

SAMPLE_CSV1 = """"Title","UK Vacancies (thousands) - Total"
"CDID","AP2Y"
"Source dataset ID","LMS"
"PreUnit",""
"Unit",""
"Release date","16-09-2025"
"Next release","14 October 2025"
"Important notes",
"2022","1243"
"2023","1022"
"2024","863"
"2024 Q4","806"
"2025 Q1","783"
"2025 Q2","726"
"2025 MAY","726"
"2025 JUN","720"
"2025 JUL","728"
"""

SAMPLE_CSV2 = """"Title","UK Vacancies (thousands) - Total"
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


def test_build_long(tmp_path):
    # create two raw CSVs with different release dates
    raw_dir = tmp_path / "raw"
    proc_dir = tmp_path / "processed"
    raw_dir.mkdir()

    (raw_dir / "a.csv").write_text(SAMPLE_CSV1, encoding="utf-8")
    (raw_dir / "b.csv").write_text(SAMPLE_CSV2, encoding="utf-8")

    df = build_long(str(raw_dir), str(proc_dir))
    assert (proc_dir / "vacancies_long.csv").exists()
    # Expect 4 rows total, with duplicates by month removed only when same vintage+month pair occurs
    assert set(df.columns) >= {"series_id", "vintage_date", "observation_month", "value"}
    assert len(df) == 6
