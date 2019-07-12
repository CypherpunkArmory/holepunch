from app.models import Plan
from app.utils.json import locate


def test_locate():
    """ Convert a Json-API style locator ref to a python object """
    p = Plan.paid()

    obj = locate({"type": "plan", "id": str(p.id)})

    assert obj == p
