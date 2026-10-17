"""Pruebas del cliente de Reddit y del conteo de respuestas (sin red)."""

from types import SimpleNamespace

from whatsthenew.fetchers.reddit import RedditClient
from whatsthenew.models import Item
from whatsthenew.pipeline import enrich_reddit_replies


def test_sin_credenciales_no_autentica():
    c = RedditClient(user_agent="whatsthenew/0.1 test")
    assert c.has_credentials is False
    # No debe tocar la red ni lanzar: simplemente devuelve False.
    assert c.authenticate() is False


def test_detecta_credenciales_presentes():
    c = RedditClient(user_agent="x", client_id="id", client_secret="sec")
    assert c.has_credentials is True


def test_endpoints_son_configurables():
    c = RedditClient(
        user_agent="x",
        token_url="https://token.example/access",
        oauth_base="https://oauth.example",
        www_base="https://www.example",
        delay=10,
        limit=7,
        retries=3,
    )
    assert c.token_url == "https://token.example/access"
    assert c.oauth_base == "https://oauth.example"
    assert c.www_base == "https://www.example"
    assert c.delay == 10
    assert c.limit == 7
    assert c.retries == 3


def test_comments_feed_url():
    c = RedditClient(user_agent="x")
    got = c._comments_feed_url("https://www.reddit.com/r/devops/comments/abc/title/")
    assert got == "https://www.reddit.com/r/devops/comments/abc/title/.rss"


def test_reply_stats():
    # La primera entrada es el propio post -> se resta 1.
    assert RedditClient._reply_stats(SimpleNamespace(entries=[1, 2, 3, 4])) == (3, True)
    assert RedditClient._reply_stats(SimpleNamespace(entries=[1])) == (0, False)
    assert RedditClient._reply_stats(SimpleNamespace(entries=[])) == (0, False)
    # Sin atributo entries no debe romper.
    assert RedditClient._reply_stats(SimpleNamespace()) == (0, False)


def test_thread_replies_sin_url_no_toca_red():
    c = RedditClient(user_agent="x")
    assert c.thread_replies("") == (0, False)


def test_enrich_reddit_replies_respeta_top_n():
    class FakeReddit:
        def __init__(self):
            self.calls: list[str] = []

        def thread_replies(self, url: str):
            self.calls.append(url)
            return (5, True)

    items = [
        Item(category="reddit", source="reddit.com/r/devops", source_type="reddit", query="salary", url=f"u{i}")
        for i in range(4)
    ]
    fake = FakeReddit()
    enrich_reddit_replies(fake, items, top_n=2)

    assert fake.calls == ["u0", "u1"]  # solo los 2 primeros
    assert items[0].replies == 5 and items[0].has_replies is True
    assert items[1].replies == 5 and items[1].has_replies is True
    assert items[2].replies == 0 and items[2].has_replies is False


def test_enrich_reddit_replies_desactivado():
    class FakeReddit:
        def __init__(self):
            self.calls = []

        def thread_replies(self, url: str):
            self.calls.append(url)
            return (1, True)

    items = [Item(category="reddit", source="reddit.com/r/sre", source_type="reddit", query="hired", url="u")]
    fake = FakeReddit()
    enrich_reddit_replies(fake, items, top_n=0)
    assert fake.calls == []
