from boe_vac.ingest import extract_csv_links_from_html

SAMPLE_HTML = """
<html><body>
<h2>Latest version</h2>
<a href="/generator?format=csv&uri=/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/timeseries/ap2y/lms">Download time series (csv)</a>
<h2>Previous versions</h2>
<ul>
<li><a href="/generator?format=csv&uri=/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/timeseries/ap2y/lms?edition=2024-09-01">Download .csv</a></li>
<li><a href="/generator?format=csv&uri=/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/timeseries/ap2y/lms?edition=2024-08-01">Download .csv</a></li>
</ul>
</body></html>
"""


def test_extract_csv_links_from_html():
    links = extract_csv_links_from_html(SAMPLE_HTML, base_url="https://www.ons.gov.uk")
    assert len(links) == 3
    assert all(link.startswith("https://www.ons.gov.uk") for link in links)
    assert all("csv" in link for link in links)
