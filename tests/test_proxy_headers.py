from conftest import DOCKER_GATEWAY, flask_app


def test_only_headers_nginx_sets_are_trusted(client, monkeypatch):
    # nginx overwrites X-Forwarded-For/-Proto but passes X-Forwarded-Host through
    # from the client, so ProxyFix must not trust it.
    seen = {}
    proxied = flask_app.wsgi_app.app

    def spy(environ, start_response):
        seen.update(environ)
        return proxied(environ, start_response)

    monkeypatch.setattr(flask_app.wsgi_app, "app", spy)
    client.get(
        "/about",
        base_url="http://theorem-marketplace.com",
        environ_base={"REMOTE_ADDR": DOCKER_GATEWAY},
        headers={
            "X-Forwarded-For": "1.1.1.1",
            "X-Forwarded-Proto": "https",
            "X-Forwarded-Host": "evil.example",
        },
    )

    assert seen["REMOTE_ADDR"] == "1.1.1.1"
    assert seen["wsgi.url_scheme"] == "https"
    assert seen["HTTP_HOST"] == "theorem-marketplace.com"
