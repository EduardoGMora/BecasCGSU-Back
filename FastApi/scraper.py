"""
Web Scraping Module for External Scholarships
Implements "Scraping bajo Demanda + Caché Inteligente" strategy
"""

import hashlib
import httpx
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any
from datetime import datetime
import re


class ScraperError(Exception):
    """Custom exception for scraping errors"""
    def __init__(self, message: str, url: str = None):
        self.message = message
        self.url = url
        super().__init__(self.message)


async def fetch_page_content(url: str, timeout: int = 30) -> str:
    """
    Fetches the HTML content from a URL asynchronously.

    Args:
        url: The URL to fetch
        timeout: Request timeout in seconds

    Returns:
        The HTML content as string

    Raises:
        ScraperError: If the request fails
    """
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            response.raise_for_status()
            return response.text
    except httpx.TimeoutException:
        raise ScraperError(f"Timeout al conectar con la URL", url)
    except httpx.HTTPStatusError as e:
        raise ScraperError(f"Error HTTP {e.response.status_code}", url)
    except httpx.RequestError as e:
        raise ScraperError(f"Error de conexión: {str(e)}", url)


def extract_text_content(html: str) -> str:
    """
    Extracts clean text content from HTML.

    Args:
        html: Raw HTML string

    Returns:
        Cleaned text content
    """
    soup = BeautifulSoup(html, 'html.parser')

    # Remove script and style elements
    for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
        element.decompose()

    # Get text and clean whitespace
    text = soup.get_text(separator=' ', strip=True)
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def extract_scholarship_data(html: str, url: str) -> Dict[str, Any]:
    """
    Extracts structured scholarship data from HTML content.
    Attempts to identify common scholarship information patterns.

    Args:
        html: Raw HTML string
        url: Source URL for reference

    Returns:
        Dictionary with extracted data
    """
    soup = BeautifulSoup(html, 'html.parser')

    # Try to extract title from various common elements
    title = None
    title_candidates = [
        soup.find('h1'),
        soup.find('title'),
        soup.find('meta', {'property': 'og:title'}),
        soup.find('meta', {'name': 'title'})
    ]

    for candidate in title_candidates:
        if candidate:
            if candidate.name == 'meta':
                title = candidate.get('content', '')
            else:
                title = candidate.get_text(strip=True)
            if title:
                break

    # Try to extract description
    description = None
    desc_candidates = [
        soup.find('meta', {'name': 'description'}),
        soup.find('meta', {'property': 'og:description'}),
        soup.find('article'),
        soup.find('main'),
        soup.find('div', {'class': re.compile(r'content|descripcion|body', re.I)})
    ]

    for candidate in desc_candidates:
        if candidate:
            if candidate.name == 'meta':
                description = candidate.get('content', '')
            else:
                description = candidate.get_text(separator='\n', strip=True)
            if description and len(description) > 50:
                break

    # Extract dates (common patterns for Mexican scholarship sites)
    dates = extract_dates_from_text(soup.get_text())

    # Extract requirements (look for lists)
    requirements = extract_requirements(soup)

    # Get full text for checksum
    full_text = extract_text_content(html)

    return {
        "title": title[:200] if title else None,
        "description": description[:5000] if description else None,
        "requirements": requirements,
        "dates_found": dates,
        "source_url": url,
        "raw_text": full_text[:10000],  # Limit for storage
        "scraped_at": datetime.utcnow().isoformat()
    }


def extract_dates_from_text(text: str) -> Dict[str, Optional[str]]:
    """
    Attempts to extract date information from text.
    Looks for common Spanish date patterns.

    Args:
        text: Text content to search

    Returns:
        Dictionary with found dates
    """
    dates = {
        "start_date": None,
        "end_date": None,
        "deadline": None
    }

    # Common Spanish date patterns
    date_patterns = [
        # "del 15 de enero al 28 de febrero de 2024"
        r'del?\s+(\d{1,2})\s+de\s+(\w+)\s+(?:al|hasta)\s+(\d{1,2})\s+de\s+(\w+)\s+(?:de\s+)?(\d{4})',
        # "fecha límite: 15 de enero de 2024"
        r'(?:fecha\s+)?l[íi]mite[:\s]+(\d{1,2})\s+de\s+(\w+)\s+(?:de\s+)?(\d{4})',
        # "15/01/2024"
        r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})',
        # "convocatoria abierta hasta el 15 de enero"
        r'(?:abierta?|vigente)\s+hasta\s+(?:el\s+)?(\d{1,2})\s+de\s+(\w+)',
    ]

    text_lower = text.lower()

    for pattern in date_patterns:
        matches = re.findall(pattern, text_lower)
        if matches:
            dates["raw_matches"] = matches[:3]  # Store first 3 matches
            break

    return dates


def extract_requirements(soup: BeautifulSoup) -> list:
    """
    Extracts requirement lists from the page.

    Args:
        soup: BeautifulSoup object

    Returns:
        List of requirement strings
    """
    requirements = []

    # Look for lists near keywords
    keywords = ['requisito', 'requerimiento', 'necesita', 'documentos', 'criteria']

    for keyword in keywords:
        # Find elements containing the keyword
        elements = soup.find_all(string=re.compile(keyword, re.I))

        for element in elements:
            # Look for nearby lists
            parent = element.find_parent()
            if parent:
                # Check siblings for ul/ol
                for sibling in parent.find_next_siblings(['ul', 'ol'])[:2]:
                    items = sibling.find_all('li')
                    for item in items[:20]:  # Limit items
                        text = item.get_text(strip=True)
                        if text and len(text) > 5:
                            requirements.append(text[:500])

    # Also check for numbered items in text
    text = soup.get_text()
    numbered_pattern = r'(?:^|\n)\s*(?:\d+[\.\)\-]|\•|\-)\s*(.{10,200})'
    numbered_items = re.findall(numbered_pattern, text)

    for item in numbered_items[:10]:
        if item.strip() and item.strip() not in requirements:
            requirements.append(item.strip())

    return requirements[:20]  # Limit to 20 requirements


def calculate_checksum(content: str) -> str:
    """
    Calculates SHA256 checksum of content for change detection.

    Args:
        content: Text content to hash

    Returns:
        SHA256 hash string
    """
    # Normalize content before hashing
    normalized = re.sub(r'\s+', ' ', content.lower().strip())
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def content_has_changed(old_checksum: str, new_content: str) -> bool:
    """
    Checks if content has changed by comparing checksums.

    Args:
        old_checksum: Previously stored checksum
        new_content: New content to compare

    Returns:
        True if content has changed
    """
    new_checksum = calculate_checksum(new_content)
    return old_checksum != new_checksum


async def scrape_scholarship(url: str) -> Dict[str, Any]:
    """
    Main function to scrape scholarship data from a URL.

    Args:
        url: URL of the scholarship page

    Returns:
        Dictionary with extracted data and checksum

    Raises:
        ScraperError: If scraping fails
    """
    # Validate URL
    if not url or not url.startswith(('http://', 'https://')):
        raise ScraperError("URL inválida. Debe comenzar con http:// o https://", url)

    # Fetch page
    html = await fetch_page_content(url)

    # Extract data
    data = extract_scholarship_data(html, url)

    # Calculate checksum
    data["checksum"] = calculate_checksum(data.get("raw_text", ""))

    return data


async def check_for_updates(url: str, stored_checksum: str) -> Dict[str, Any]:
    """
    Checks if a scholarship page has been updated.

    Args:
        url: URL to check
        stored_checksum: Previously stored checksum

    Returns:
        Dictionary with update status and new data if changed
    """
    try:
        html = await fetch_page_content(url)
        text = extract_text_content(html)
        new_checksum = calculate_checksum(text)

        has_changed = stored_checksum != new_checksum

        result = {
            "has_changed": has_changed,
            "new_checksum": new_checksum,
            "checked_at": datetime.utcnow().isoformat()
        }

        if has_changed:
            # Re-extract all data since content changed
            result["new_data"] = extract_scholarship_data(html, url)
            result["new_data"]["checksum"] = new_checksum

        return result

    except ScraperError as e:
        return {
            "has_changed": None,
            "error": e.message,
            "checked_at": datetime.utcnow().isoformat()
        }
