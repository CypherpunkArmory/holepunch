from app.services import authentication
from app.models import User, Plan
from app.utils.errors import AccessDenied, UserError
from app.services.user.user_notification import UserNotification
from app.services.user.user_stripe import UserStripe
from app.jobs.payment import user_subscribed, user_unsubscribed
import uuid
from app.utils.db import Interactor


class UserUpdate(Interactor):
    def __init__(self, user: User, scopes=None, rels=None, attrs=None):
        scopes = {} if scopes is None else scopes
        rels = {} if rels is None else rels
        attrs = {} if attrs is None else attrs
        self.user = user
        self.scopes = scopes
        authentication.validate_scope_permissions("update:user", self.scopes, attrs)
        self.new_password = attrs.pop("new_password", None)
        self.old_password = attrs.pop("old_password", None)
        self.email = attrs.pop("email", None)
        self.rels = rels
        self.attrs = attrs

    @Interactor.on_change("user", "password_hash")
    def password_was_changed(self, *_):
        UserNotification(self.user).password_changed_email()

    @Interactor.on_change("user", "email")
    def email_was_changed(self, old_value, *_):
        UserNotification(self.user).email_changed_email(old_value)

    @Interactor.on_change("user", "stripe_payment_method")
    def stripe_payment_method_was_changed(self, old_value, *_):
        if old_value is not None:
            UserStripe(self.user).update_stripe_customer("stripe_payment_method")

    @Interactor.on_change("user", "stripe_id")
    def user_changed_stripe_id(self, old_value, *_):
        UserStripe(self.user).update_stripe_customer("stripe_id")

    @Interactor.on_change("user", "plan")
    def user_tier_change(self, old_value, new_value):
        if self.user.tier in Plan.paid_plans():

            @Interactor.after_commit
            def subscribe_after_commit(_):
                user_subscribed.queue(self.user.id, self.user.plan.id)

        else:

            @Interactor.after_commit
            def unsubscribe_after_commit(_):
                user_unsubscribed.queue(self.user.id, old_value.id)

    @Interactor.flushes("user")
    def update(self) -> User:
        self.update_attrs(self.user, self.attrs)
        self.update_relationships(self.user, self.rels)

        # password is special cased because we encrypt it before
        # we actually store it.
        if self.new_password:
            if (
                "update:user:new_password" not in self.scopes
                and not self.user.check_password(self.old_password)
            ):
                raise AccessDenied("Wrong password")
            self.record_change(self.user, "password_hash")
            self.user.set_password(self.new_password)
            self.user.uuid = str(uuid.uuid4())

        # email is also special cased in the sense of we do not attempt
        # to perform the write if we know there is a conflicting email
        if self.email:
            if User.query.filter_by(email=self.email).first() is not None:
                raise UserError(detail="Email already in use")
            self.record_change(self.user, "email")
            self.user.email = self.email

        return self.user
