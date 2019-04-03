import pytest

from app.services.subdomain import SubdomainCreationService


class TestSubdomainCreationService(object):
    """Email creation service has correct business logic"""

    def test_create_reserve_subdomain(self, current_free_user, current_user):
        """ Raises an exception when too many reserved subdomains"""
        with pytest.raises(Exception):
            SubdomainCreationService(current_free_user, "subsub").reserve(True)
        for x in range(0, 5):
            SubdomainCreationService(current_user, "subsub" + str(x)).reserve(True)
        with pytest.raises(Exception):
            SubdomainCreationService(current_user, "subsub10").reserve(True)

    def test_create_unreserved_subdomain(self, current_free_user, current_user):
        """ Does not raise an exception creating an unreserved subdomain"""
        for x in range(0, 10):
            SubdomainCreationService(current_free_user, "free" + str(x)).reserve(False)
        for x in range(0, 10):
            SubdomainCreationService(current_user, "paid" + str(x)).reserve(False)
        # make sure unreserved subdomains were not counted
        SubdomainCreationService(current_user, "subsub-paid-reserved").reserve(True)
