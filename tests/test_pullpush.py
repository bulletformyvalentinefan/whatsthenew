"""Pruebas del fetcher PullPush y de la prioridad de Reddit (sin red)."""

from dataclasses import replace

from whatsthenew.config import Settings
from whatsthenew.fetchers.pullpush import fetch_pullpush
from whatsthenew.pipeline import collect_reddit

TEMPLATE = "https://x/{subreddit}?q={query}&size={size}"


class FakeClient:
    def __init__(self, payload):
        self.payload = payload
        self.urls: list[str] = []

    def get_json(self, url):
        self.urls.append(url)
        return self.payload


def test_pullpush_mapea_campos():
    payload = {
        "data": [
            {
                "subreddit": "devops",
                "title": "Salary thread",
                "created_utc": 1700000000.0,
                "num_comments": 42,
                "permalink": "/r/devops/comments/abc/salary_thread/",
                "selftext": "hola",
            },
            {
                "subreddit": "sre",
                "title": "Sin respuestas",
                "created_utc": 1700000001.0,
                "num_comments": 0,
                "permalink": "/r/sre/comments/def/x/",
                "selftext": "",
            },
        ]
    }
    items = fetch_pullpush(FakeClient(payload), TEMPLATE, "devops", "salary", 5)

    assert len(items) == 2
    first = items[0]
    assert first.source == "reddit.com/r/devops"
    assert first.source_type == "pullpush"
    assert first.title == "Salary thread"
    assert first.posted_at == "1700000000.0"
    assert first.replies == 42 and first.has_replies is True
    assert first.url == "https://www.reddit.com/r/devops/comments/abc/salary_thread/"
    assert items[1].replies == 0 and items[1].has_replies is False


def test_pullpush_construye_url():
    client = FakeClient({"data": []})
    fetch_pullpush(client, TEMPLATE, "devops", "remote job", 7)
    assert client.urls[0] == "https://x/devops?q=remote+job&size=7"


def test_collect_reddit_usa_pullpush_primero():
    settings = replace(
        Settings.from_env(), pullpush_url=TEMPLATE, reddit_limit=3, reddit_replies_top_n=0
    )
    payload = {
        "data": [
            {
                "subreddit": "devops",
                "title": "t",
                "created_utc": 1,
                "num_comments": 1,
                "permalink": "/r/devops/comments/a/b/",
            }
        ]
    }

    class BoomReddit:
        """Si PullPush devuelve datos, no debe tocarse el RSS/OAuth."""

        def authenticate(self):  # pragma: no cover - no debería llamarse
            raise AssertionError("no debe autenticar si PullPush dio datos")

    rcfg = {"subreddits": {"role": ["devops", "sre", "kubernetes", "platformengineering", "aws"]}}
    items = collect_reddit(settings, BoomReddit(), FakeClient(payload), rcfg)

    assert items
    assert all(i.source_type == "pullpush" for i in items)
