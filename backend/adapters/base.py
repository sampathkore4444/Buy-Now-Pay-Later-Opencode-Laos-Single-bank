from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class BankCustomerInfo:
    bank_customer_id: str
    name: str
    phone: str
    id_card: str | None = None
    kyc_status: str | None = None
    aml_status: str | None = None


@dataclass
class BankAccountBalance:
    account_no: str
    available_balance: float
    currency: str = "LAK"


@dataclass
class BankTransactionResult:
    success: bool
    transaction_id: str | None = None
    reference_no: str | None = None
    error_message: str | None = None


class BankAdapter(ABC):

    @abstractmethod
    async def verify_customer(self, customer_id: str) -> BankCustomerInfo:
        ...

    @abstractmethod
    async def check_balance(self, account_no: str) -> BankAccountBalance:
        ...

    @abstractmethod
    async def debit_account(self, account_no: str, amount: float, reference: str) -> BankTransactionResult:
        ...

    @abstractmethod
    async def credit_account(self, account_no: str, amount: float, reference: str) -> BankTransactionResult:
        ...

    @abstractmethod
    async def get_transaction_status(self, transaction_id: str) -> dict:
        ...
