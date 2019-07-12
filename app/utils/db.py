import sqlalchemy.event
from contextlib import contextmanager
from app.utils.json import locate
from app.utils.errors import UnprocessableEntity
from functools import wraps
from app import db
from sqlalchemy import inspect


@contextmanager
def skip_callbacks(target, *callbacks):
    hold_events: list = []
    callback_ids = {id(callback): callback for callback in callbacks}

    for ev in sqlalchemy.event.registry._key_to_collection:
        if ev[0] == id(target) and ev[2] in callback_ids.keys():
            hold_events.append(ev)

    for ev in hold_events:
        sqlalchemy.event.remove(target, ev[1], callback_ids[ev[2]])

    yield

    for ev in hold_events:
        sqlalchemy.event.listens_for(target, ev[1], callback_ids[ev[2]])


class Interactor:
    @staticmethod
    def commits(a_property):
        def commits_decorator(f):
            @wraps(f)
            def wrapper(self, *args, **kwargs):
                res = f(self, *args, **kwargs)
                self._execute_on_change_callbacks()
                db.session.add(getattr(self, a_property))
                db.session.commit()
                return res

            return wrapper

        return commits_decorator

    @staticmethod
    def flushes(a_property):
        def flushes_decorator(f):
            @wraps(f)
            def wrapper(self, *args, **kwargs):
                res = f(self, *args, **kwargs)
                self._execute_on_change_callbacks()
                db.session.add(getattr(self, a_property))
                db.session.flush()
                return res

            return wrapper

        return flushes_decorator

    @staticmethod
    def after_commit(f):
        sqlalchemy.event.listen(db.session, "after_commit", f, once=True)
        return f

    @classmethod
    def on_change(cls, a_property, an_attribute):
        def on_change_decorator(f):
            if not hasattr(cls, "_on_change_list"):
                cls._on_change_list = {}

            if a_property not in cls._on_change_list:
                cls._on_change_list[a_property] = {}

            cls._on_change_list[a_property].update({an_attribute: f})

            return f

        return on_change_decorator

    @property
    def attribute_changeset(self):
        if not hasattr(self, "_attribute_changeset"):
            self._attribute_changeset = {}

        return self._attribute_changeset

    @attribute_changeset.setter
    def attribute_changeset(self, value):
        self._attribute_changeset = value

    def update_attrs(self, interactee, attrs):
        for attr, val in attrs.items():
            old = getattr(interactee, attr)
            self.attribute_changeset[attr] = old
            setattr(interactee, attr, val)

    def record_change(self, interactee, attr):
        old = getattr(interactee, attr)
        self.attribute_changeset[attr] = old

    def update_relationships(self, interactee, rels):
        for rel, locator in rels.items():
            relation = None
            try:
                relation = inspect(interactee.__class__).relationships[rel]
            except KeyError:
                continue

            self.attribute_changeset[rel] = getattr(interactee, rel)

            # The foreign key lives on OUR object
            if relation.direction.name == "MANYTOONE":
                setattr(self.user, rel, locate(locator["data"]))
            # The foreign key lives on the OTHER object
            elif relation.direction.name == "ONETOMANY":
                for obj in locator["data"]:
                    self.user[rel].append(locate(obj))
            elif relation.direction.name == "MANYTOMANY":
                raise UnprocessableEntity(detail=f"{rel} cannot be set on this object")

    def _execute_on_change_callbacks(self):
        attr_changed = set(self.attribute_changeset.keys())

        for a_property, attribute_callbacks in self.__class__._on_change_list.items():
            for an_attribute, callback in attribute_callbacks.items():
                if an_attribute in attr_changed:
                    callback(
                        self,
                        self.attribute_changeset[an_attribute],
                        getattr(getattr(self, a_property), an_attribute),
                    )
