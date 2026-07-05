from adapters.base import BankAdapter, BankCustomerInfo, BankAccountBalance, BankTransactionResult


class LDBAdapter(BankAdapter):

    async def verify_customer(self, customer_id: str) -> BankCustomerInfo:
        return BankCustomerInfo(
            bank_customer_id=customer_id,
            name="[LDB] Placeholder Name",
            phone="+8562000000000",
            id_card=None,
            kyc_status="VERIFIED",
            aml_status="CLEAR",
        )

    async def check_balance(self, account_no: str) -> BankAccountBalance:
        return BankAccountBalance(
            account_no=account_no,
            available_balance=0.0,
        )

    async def debit_account(self, account_no: str, amount: float, reference: str) -> BankTransactionResult:
        return BankTransactionResult(
            success=True,
            transaction_id=f"LDB-DEBIT-{reference[:16]}",
            reference_no=reference,
        )

    async def credit_account(self, account_no: str, amount: float, reference: str) -> BankTransactionResult:
        return BankTransactionResult(
            success=True,
            transaction_id=f"LDB-CREDIT-{reference[:16]}",
            reference_no=reference,
        )

    async def get_transaction_status(self, transaction_id: str) -> dict:
        return {
            "transaction_id": transaction_id,
            "status": "COMPLETED",
            "bank": "LDB",
        }
