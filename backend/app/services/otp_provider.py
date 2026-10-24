from abc import ABC, abstractmethod


class OtpProvider(ABC):
    @abstractmethod
    def send(self, phone: str, code: str) -> None:
        ...


class MockOtpProvider(OtpProvider):
    def send(self, phone: str, code: str) -> None:
        # In dev only; production must not log OTPs.
        import os
        if os.getenv("APP_ENV", "development") != "production":
            print(f"[MOCK OTP] phone={phone} code={code}")


def get_otp_provider(name: str) -> OtpProvider:
    if name == "mock":
        return MockOtpProvider()
    raise ValueError(f"Unknown OTP provider: {name}")
