class TestRoot(object):
    """Includes wide open CORS headers"""

    def test_root_cors_config(self, client, app):
        with app.app_context():
            res = client.get("/")
            assert res.headers["Access-Control-Allow-Origin"] == "*"
