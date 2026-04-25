from __future__ import annotations

import html
import json
import re
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote_plus, unquote, urlparse
from urllib.request import Request, urlopen

from .config import RAGConfig
from .models import WebSearchResult


class WebSearchService:
    def __init__(self, config: RAGConfig) -> None:
        self.config = config

    def search(self, query: str) -> list[WebSearchResult]:
        if not query.strip():
            return []

        results: list[WebSearchResult] = []
        seen_urls: set[str] = set()

        for result in self._search_instant_answers(query):
            self._append_unique(results, seen_urls, result)

        if len(results) < self.config.web_search_results:
            for result in self._search_duckduckgo_html(query):
                self._append_unique(results, seen_urls, result)
                if len(results) >= self.config.web_search_results:
                    break

        return results[: self.config.web_search_results]

    def _search_instant_answers(self, query: str) -> list[WebSearchResult]:
        params = (
            f"q={quote_plus(query)}&format=json&no_html=1&skip_disambig=1&no_redirect=1"
        )
        url = f"https://api.duckduckgo.com/?{params}"

        try:
            payload = self._fetch_text(url)
            data = json.loads(payload)
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, ValueError):
            return []

        results: list[WebSearchResult] = []
        abstract = _clean_text(data.get("AbstractText", ""))
        abstract_url = str(data.get("AbstractURL", "")).strip()
        if abstract and abstract_url:
            title = _clean_text(data.get("Heading", "")) or _title_from_url(abstract_url)
            results.append(WebSearchResult(title=title, url=abstract_url, snippet=abstract))

        for topic in _flatten_related_topics(data.get("RelatedTopics", [])):
            text = _clean_text(topic.get("Text", ""))
            url = str(topic.get("FirstURL", "")).strip()
            if text and url:
                results.append(
                    WebSearchResult(
                        title=_title_from_text(text, url),
                        url=url,
                        snippet=text,
                    )
                )

        return results

    def _search_duckduckgo_html(self, query: str) -> list[WebSearchResult]:
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        try:
            html_content = self._fetch_text(url)
        except (HTTPError, URLError, TimeoutError):
            return []

        pattern = re.compile(
            r'<a[^>]+class="result__a"[^>]+href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>'
            r'(?P<tail>.*?)(?=<a[^>]+class="result__a"|$)',
            re.IGNORECASE | re.DOTALL,
        )
        snippet_pattern = re.compile(
            r'class="result__snippet"[^>]*>(?P<snippet>.*?)</(?:a|div)>',
            re.IGNORECASE | re.DOTALL,
        )

        results: list[WebSearchResult] = []
        for match in pattern.finditer(html_content):
            raw_url = match.group("href")
            title = _clean_text(match.group("title"))
            snippet_match = snippet_pattern.search(match.group("tail"))
            snippet = _clean_text(snippet_match.group("snippet")) if snippet_match else ""
            resolved_url = _resolve_duckduckgo_redirect(raw_url)

            if title and resolved_url:
                results.append(
                    WebSearchResult(
                        title=title,
                        url=resolved_url,
                        snippet=snippet or f"Search result from {urlparse(resolved_url).netloc}",
                    )
                )

        return results

    def _fetch_text(self, url: str) -> str:
        request = Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
                )
            },
        )
        with urlopen(request, timeout=self.config.web_search_timeout_seconds) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="ignore")

    def _append_unique(
        self,
        results: list[WebSearchResult],
        seen_urls: set[str],
        result: WebSearchResult,
    ) -> None:
        normalized_url = result.url.rstrip("/")
        if not normalized_url or normalized_url in seen_urls:
            return
        seen_urls.add(normalized_url)
        results.append(result)


def _flatten_related_topics(topics: Iterable[dict]) -> list[dict]:
    flattened: list[dict] = []
    for topic in topics:
        nested_topics = topic.get("Topics")
        if isinstance(nested_topics, list):
            flattened.extend(_flatten_related_topics(nested_topics))
        else:
            flattened.append(topic)
    return flattened


def _resolve_duckduckgo_redirect(url: str) -> str:
    if not url:
        return ""
    if url.startswith("//"):
        url = f"https:{url}"
    if "duckduckgo.com/l/?" not in url:
        return html.unescape(url)

    parsed = urlparse(url)
    uddg = parse_qs(parsed.query).get("uddg", [""])[0]
    return unquote(uddg) if uddg else ""


def _clean_text(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    text = html.unescape(text)
    return " ".join(text.split())


def _title_from_text(text: str, url: str) -> str:
    for separator in (" - ", " | ", " — ", " – ", ": "):
        if separator in text:
            return text.split(separator, 1)[0].strip()
    return _title_from_url(url)


def _title_from_url(url: str) -> str:
    domain = urlparse(url).netloc.removeprefix("www.")
    return domain or "Web result"
