from abc import ABC, abstractmethod


class PaymentProvider(ABC):
    @abstractmethod
    def create_subscription(self, user_id: int) -> dict:
        ...


class MockPaymentProvider(PaymentProvider):
    def create_subscription(self, user_id: int) -> dict:
        return {"status": "active", "provider": "mock", "note": "DEMO ONLY - no real payment processed"}


def get_payment_provider(name: str):
    if name == "mock":
        return MockPaymentProvider()
    raise ValueError(f"Unknown payment provider: {name}")
