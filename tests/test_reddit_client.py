"""Pruebas del cliente de Reddit (sin red)."""

from whatsthenew.fetchers.reddit import RedditClient


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
    )
    assert c.token_url == "https://token.example/access"
    assert c.oauth_base == "https://oauth.example"
    assert c.www_base == "https://www.example"
    assert c.delay == 10
    assert c.limit == 7
