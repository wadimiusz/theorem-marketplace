HOURLY_LIMIT = 50  # default_limits in app.py


def exhaust(get_as, path, xff):
    codes = [get_as(path, xff).status_code for _ in range(HOURLY_LIMIT + 1)]
    assert codes[:HOURLY_LIMIT] == [200] * HOURLY_LIMIT
    assert codes[HOURLY_LIMIT] == 429


def test_clients_behind_proxy_have_separate_buckets(get_as):
    # Regression: Oct 2026 a single scanner exhausted the limit for every visitor,
    # because all requests looked like they came from the docker gateway.
    exhaust(get_as, "/about", "1.1.1.1")
    assert get_as("/about", "2.2.2.2").status_code == 200


def test_forged_forwarded_for_does_not_reset_bucket(get_as):
    # nginx appends the real peer IP last; anything before it is client-controlled.
    exhaust(get_as, "/about", "1.1.1.1")
    assert get_as("/about", "9.9.9.9, 1.1.1.1").status_code == 429
