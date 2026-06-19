# CI-12 clean: wrapper adds real validation logic


class BillingGateway:
    def __init__(self, client):
        self.client = client

    def charge(self, account_id, amount):
        if amount <= 0:
            raise ValueError("amount must be positive")
        return self.client.charge(account_id, amount)
