from app import Q


@Q.job(func_or_queue="payment", timeout=60000)
def user_subscribed(user_id):
    pass


@Q.job(func_or_queue="payment", timeout=60000)
def user_unsubscribed(user_id):
    pass
