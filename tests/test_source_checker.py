"""Tests for cited source extraction and classification."""

from unittest.mock import MagicMock, patch

from backend.source_checker import (
    build_source_summary,
    check_sources,
    classify_domain,
    extract_urls_from_text,
    fetch_url_metadata,
    is_primary_official_source,
    merge_urls,
    parse_domain,
)
from backend.trust_models import CheckedSource


def test_extract_urls_from_text():
    text = "See https://www.cdc.gov/flu and also https://example.com/article."
    urls = extract_urls_from_text(text)
    assert "https://www.cdc.gov/flu" in urls
    assert "https://example.com/article" in urls


def test_merge_urls_deduplicates_and_limits():
    text = "https://a.com https://b.com"
    merged = merge_urls(["https://a.com"], text)
    assert merged == ["https://a.com", "https://b.com"]


def test_classify_official_domain_as_high():
    quality, _ = classify_domain("cdc.gov", reachable=True)
    assert quality == "high"


def test_classify_unreachable_domain_as_low():
    quality, note = classify_domain("example.com", reachable=False)
    assert quality == "low"
    assert "inaccessible" in note.lower()


def test_classify_reddit_as_low_medium():
    quality, _ = classify_domain("reddit.com", reachable=True)
    assert quality == "low-medium"


def test_build_source_summary_counts_reachable_and_official():
    sources = [
        CheckedSource(
            url="https://www.nih.gov/study",
            domain="nih.gov",
            reachable=True,
            status_code=200,
            title="NIH Study",
            source_quality="high",
            notes="",
        ),
        CheckedSource(
            url="https://broken.example/missing",
            domain="broken.example",
            reachable=False,
            status_code=404,
            title=None,
            source_quality="low",
            notes="Broken or inaccessible citation.",
        ),
    ]
    summary = build_source_summary(sources)
    assert summary.sources_checked == 2
    assert summary.reachable_count == 1
    assert summary.primary_official_count == 1
    assert any("unreachable" in issue.lower() for issue in summary.issues)


def test_is_primary_official_source():
    source = CheckedSource(
        url="https://www.nist.gov/doc",
        domain="nist.gov",
        reachable=True,
        status_code=200,
        title="NIST",
        source_quality="high",
        notes="",
    )
    assert is_primary_official_source(source) is True


@patch("backend.source_checker.urlopen")
def test_fetch_url_metadata_parses_title(mock_urlopen):
    mock_response = MagicMock()
    mock_response.__enter__.return_value = mock_response
    mock_response.status = 200
    mock_response.headers = {"Content-Type": "text/html"}
    mock_response.read.return_value = b"<html><title>Example Article</title></html>"
    mock_urlopen.return_value = mock_response

    source = fetch_url_metadata("https://example.com/article")
    assert source.reachable is True
    assert source.title == "Example Article"
    assert source.domain == "example.com"


def test_check_sources_empty_list():
    assert check_sources([]) == []


@patch("backend.source_checker.fetch_url_metadata")
def test_check_sources_calls_fetch_for_each_url(mock_fetch):
    def fake_fetch(url):
        return {
            "https://a.com": CheckedSource(
                url="https://a.com",
                domain="a.com",
                reachable=True,
                status_code=200,
                title="A",
                source_quality="medium",
                notes="",
            ),
            "https://b.com": CheckedSource(
                url="https://b.com",
                domain="b.com",
                reachable=False,
                status_code=404,
                title=None,
                source_quality="low",
                notes="Broken",
            ),
        }[url]

    mock_fetch.side_effect = fake_fetch
    sources = check_sources(["https://a.com", "https://b.com"])
    assert len(sources) == 2
    assert [source.url for source in sources] == ["https://a.com", "https://b.com"]
    assert sources[1].reachable is False
