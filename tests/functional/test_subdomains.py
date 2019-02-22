from app.models import Subdomain
from app import db
from tests.factories import subdomain
from tests.support.assertions import assert_valid_schema
from dpath.util import values


class TestSubdomain(object):
    """Logged in Users can manage their subdomains"""

    def test_empty_subdomain_index(self, client):
        """User can list all of their subdomains when empty"""
        res = client.get("/subdomains")
        assert_valid_schema(res.get_json(), "subdomains.json")

    def test_subdomain_index(self, client, current_user):
        """User can list all of their subdomains"""

        sub = subdomain.SubdomainFactory.create(user=current_user)
        res3 = client.get("/subdomains")
        assert_valid_schema(res3.get_json(), "subdomains.json")
        assert str(sub.id) in values(res3.get_json(), "data/*/id")

    def test_subdomain_get(self, client, current_user):
        """User can get a single subdomain"""

        sub = subdomain.SubdomainFactory.create(user=current_user)
        res3 = client.get(f"/subdomains/{sub.id}")
        assert_valid_schema(res3.get_json(), "subdomain.json")
        assert str(sub.id) in values(res3.get_json(), "data/id")

    def test_subdomain_reserve(self, client, current_user):
        """User can reserve a subdomain"""

        pre_subdomain_count = Subdomain.query.filter_by(user_id=current_user.id).count()

        res = client.post(
            "/subdomains",
            json={"data": {"type": "subdomain", "attributes": {"name": "test"}}},
        )

        post_subdomain_count = Subdomain.query.filter_by(
            user_id=current_user.id
        ).count()

        assert_valid_schema(res.get_data(), "subdomain.json")
        assert post_subdomain_count > pre_subdomain_count

    def test_subdomain_release_owned(self, client, current_user):
        """User can release a subdomain they own"""

        sub = subdomain.ReservedSubdomainFactory(user=current_user, name="domainiown")
        res = client.delete(f"/subdomains/{sub.id}")

        assert res.status_code == 204

    def test_subdomain_release_phantom(self, client):
        """User cant release a subdomain that doesn't exist"""

        res = client.delete(f"/subdomains/5")

        assert res.status_code == 404

    def test_subdomain_release_unowned(self, client, session):
        """User cant release a subdomain is owned by someone else"""

        sub = subdomain.ReservedSubdomainFactory(name="domainyouown")
        session.add(sub)
        session.flush()

        res = client.delete(f"/subdomains/{sub.id}")

        assert res.status_code == 404

    def test_subdomain_filter(self, client, session, current_user):
        """Can filter a subdomain using JSON-API compliant filters"""

        sub1 = subdomain.ReservedSubdomainFactory(user=current_user, name="subby-sub")
        sub2 = subdomain.ReservedSubdomainFactory(user=current_user, name="sub-subby")
        session.add(sub1, sub2)
        session.flush()

        res = client.get(f"/subdomains?filter[name]=subby-sub")

        assert_valid_schema(res.get_json(), "subdomains.json")
        assert str(sub1.id) in values(res.get_json(), "data/*/id")
        assert str(sub2.id) not in values(res.get_json(), "data/*/id")
