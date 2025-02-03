class BankAPI:
    def __init__(self):
        self.balance = 5000  # Starting balance for the API

    def withdraw(self, amount):
        if amount > self.balance:
            return False, self.balance
        self.balance -= amount
        return True, self.balance

