from app.models import Subdomain
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

    def test_subdomain_reserve_owned(self, client, current_user, session):
        """User cant reserve an already reserved subdomain"""

        sub = subdomain.ReservedSubdomainFactory(name="substation")
        session.add(sub)
        session.flush()

        res = client.post(
            "/subdomains",
            json={"data": {"type": "subdomain", "attributes": {"name": "substation"}}},
        )

        assert res.status_code == 400
        assert (
            res.json["data"]["attributes"]["detail"]
            == "Subdomain has already been reserved"
        )

    def test_subdomain_reserve_free_tier(self, free_client):
        """User cant reserve a subdomain if they are free tier"""

        res = free_client.post(
            "/subdomains",
            json={"data": {"type": "subdomain", "attributes": {"name": "test"}}},
        )

        assert res.status_code == 403

    def test_subdomain_reserve_paid_over_limit(self, client, current_user, session):
        """User can't reserve more than 5 subdomains if they are paid tier"""

        sub1 = subdomain.ReservedSubdomainFactory(user=current_user, name="sub")
        sub2 = subdomain.ReservedSubdomainFactory(user=current_user, name="subtract")
        sub3 = subdomain.ReservedSubdomainFactory(user=current_user, name="subwoofer")
        sub4 = subdomain.ReservedSubdomainFactory(
            user=current_user, name="subconscious"
        )
        sub5 = subdomain.ReservedSubdomainFactory(user=current_user, name="subreddit")
        session.add(sub1)
        session.add(sub2)
        session.add(sub3)
        session.add(sub4)
        session.add(sub5)
        session.flush()
        res = client.post(
            "/subdomains",
            json={"data": {"type": "subdomain", "attributes": {"name": "test"}}},
        )

        assert res.status_code == 403

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

    def test_subdomain_release_used(self, client, session, current_user):
        """User cannot release a subdomain is being used"""

        sub = subdomain.InuseSubdomainFactory(user=current_user, name="scrub")
        session.add(sub)
        session.flush()

        assert sub.in_use is True

        res = client.delete(f"/subdomains/{sub.id}")
        assert res.status_code == 403
        assert (
            res.json["data"]["attributes"]["detail"]
            == "Subdomain is associated with a running tunnel"
        )

    def test_subdomain_filter(self, client, session, current_user):
        """Can filter a subdomain using JSON-API compliant filters"""

        sub1 = subdomain.ReservedSubdomainFactory(user=current_user, name="submarine")
        sub2 = subdomain.ReservedSubdomainFactory(user=current_user, name="sublime")
        session.add(sub1, sub2)
        session.flush()

        res = client.get(f"/subdomains?filter[name]=submarine")

        assert_valid_schema(res.get_json(), "subdomains.json")
        assert str(sub1.id) in values(res.get_json(), "data/*/id")
        assert str(sub2.id) not in values(res.get_json(), "data/*/id")
