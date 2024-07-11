class Prediction:
    def __init__(self, base_currency, quote_currency, timestamp):
        self.base_currency = base_currency
        self.quote_currency = quote_currency
        self.timestamp = timestamp
    
    def predict(self):
        print(f"base_currency: {self.base_currency}")
        print(f"quote_currency: {self.quote_currency}")
        print(f"timestamp: {self.timestamp}")
        return {"answer": 65232.25}

