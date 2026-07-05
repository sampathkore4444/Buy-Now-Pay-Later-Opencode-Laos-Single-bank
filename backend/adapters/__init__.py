from adapters.base import BankAdapter
from adapters.bcel_adapter import BCELAdapter
from adapters.ldb_adapter import LDBAdapter


def get_bank_adapter(bank_code: str) -> BankAdapter:
    adapters = {
        "BCEL": BCELAdapter(),
        "LDB": LDBAdapter(),
    }
    adapter = adapters.get(bank_code)
    if not adapter:
        raise ValueError(f"Unsupported bank code: {bank_code}")
    return adapter
