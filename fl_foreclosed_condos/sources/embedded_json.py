"""Helper for pulling embedded JSON payloads out of server-rendered pages.

Modern listing sites built on frameworks like Next.js commonly embed the
data used to hydrate the page as a JSON blob inside a <script> tag (e.g.
`<script id="__NEXT_DATA__" type="application/json">`), rather than as
plain HTML. This is unrelated to any particular site's public API -- it's
just how the page happens to be rendered, and it's undocumented and can
change without notice.
"""

import json
from typing import Any, Optional

from bs4 import BeautifulSoup


def extract_json_by_script_id(html: str, script_id: str) -> Optional[dict]:
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("script", id=script_id)
    if tag is None or not tag.string:
        return None
    try:
        return json.loads(tag.string)
    except json.JSONDecodeError:
        return None


def dig(data: Any, *path: str) -> Any:
    """Walk a nested dict/list by keys/indices, returning None the moment
    any step along `path` is missing instead of raising."""
    current = data
    for key in path:
        if current is None:
            return None
        try:
            current = current[key]
        except (KeyError, IndexError, TypeError):
            return None
    return current
