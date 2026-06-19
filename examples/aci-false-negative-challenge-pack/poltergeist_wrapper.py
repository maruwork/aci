# CI-12 fixture: pure delegation wrapper


class BillingGateway:
    def __init__(self, client):
        self.client = client

    def charge(self, account_id, amount):
        return self.client.charge(account_id, amount)
