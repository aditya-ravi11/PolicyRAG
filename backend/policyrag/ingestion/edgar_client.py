import asyncio
import logging
from typing import Optional

import httpx

from policyrag.config import settings

logger = logging.getLogger(__name__)

EDGAR_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
EDGAR_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
EDGAR_FILING_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{filename}"

def _headers() -> dict[str, str]:
    return {"User-Agent": settings.EDGAR_USER_AGENT, "Accept-Encoding": "gzip, deflate"}


async def _get_cik_from_ticker(client: httpx.AsyncClient, ticker: str) -> Optional[str]:
    """Resolve ticker to CIK using SEC company tickers JSON."""
    resp = await client.get("https://www.sec.gov/files/company_tickers.json", headers=_headers())
    resp.raise_for_status()
    data = resp.json()
    ticker_upper = ticker.upper()
    for entry in data.values():
        if entry.get("ticker", "").upper() == ticker_upper:
            return str(entry["cik_str"]).zfill(10)
    return None


async def _get_filings(
    client: httpx.AsyncClient,
    cik: str,
    filing_type: str = "10-K",
    date_after: Optional[str] = None,
    date_before: Optional[str] = None,
) -> list[dict]:
    """Get filing metadata from EDGAR submissions API."""
    url = EDGAR_SUBMISSIONS_URL.format(cik=cik)
    resp = await client.get(url, headers=_headers())
    resp.raise_for_status()
    data = resp.json()

    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    accessions = recent.get("accessionNumber", [])
    dates = recent.get("filingDate", [])
    primary_docs = recent.get("primaryDocument", [])

    filings = []
    for i, form in enumerate(forms):
        if form != filing_type:
            continue
        filing_date = dates[i]
        if date_after and filing_date < date_after:
            continue
        if date_before and filing_date > date_before:
            continue
        filings.append({
            "accession": accessions[i].replace("-", ""),
            "accession_formatted": accessions[i],
            "date": filing_date,
            "primary_doc": primary_docs[i],
            "cik": cik,
        })

    return filings


async def download_filing(
    ticker: str,
    filing_type: str = "10-K",
    date_after: Optional[str] = None,
    date_before: Optional[str] = None,
    max_filings: int = 1,
) -> list[dict]:
    """Download SEC filings for a ticker. Returns list of {bytes, metadata}."""
    results = []
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        cik = await _get_cik_from_ticker(client, ticker)
        if not cik:
            raise ValueError(f"Could not find CIK for ticker: {ticker}")

        await asyncio.sleep(0.15)  # EDGAR rate limit

        filings = await _get_filings(client, cik, filing_type, date_after, date_before)
        filings = filings[:max_filings]

        for filing in filings:
            await asyncio.sleep(0.15)  # EDGAR rate limit
            url = EDGAR_FILING_URL.format(
                cik=cik.lstrip("0"),
                accession=filing["accession"],
                filename=filing["primary_doc"],
            )
            for attempt in range(3):
                try:
                    resp = await client.get(url, headers=_headers())
                    if resp.status_code == 429:
                        wait = (attempt + 1) * 2
                        logger.warning(f"EDGAR 429, retrying in {wait}s")
                        await asyncio.sleep(wait)
                        continue
                    resp.raise_for_status()
                    results.append({
                        "content": resp.content,
                        "filename": filing["primary_doc"],
                        "content_type": resp.headers.get("content-type", ""),
                        "metadata": {
                            "cik": cik,
                            "ticker": ticker.upper(),
                            "filing_type": filing_type,
                            "filing_date": filing["date"],
                            "accession": filing["accession_formatted"],
                            "source_url": str(resp.url),
                        },
                    })
                    break
                except httpx.HTTPStatusError as e:
                    if attempt == 2:
                        logger.error(f"Failed to download filing: {e}")
                        raise

    return results
