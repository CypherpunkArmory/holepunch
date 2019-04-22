class TestRoot(object):
    def test_root_accessible(self, unauthenticated_client, app):
        """Root url is accessible with no login"""
        res = unauthenticated_client.get("/")
        assert res.get_data() == b"Greetings User!"

    def test_root_cors_config(self, client, app):
        """Includes wide open CORS headers"""
        res = client.get("/")
        assert res.headers["Access-Control-Allow-Origin"] == "*"

    def test_health_check_accessible(self, unauthenticated_client):
        """health_check is accessible with no login"""
        res = unauthenticated_client.get("/health_check")
        assert res.get_data() == b"OK"
