export interface Merchant {
  merchant_id: string;
  business_name: string;
  status: string;
  risk_tier: string;
  mdr_rate: number;
  settlement_terms: string;
  daily_limit_lak: number | null;
  monthly_limit_lak: number | null;
  channels: string[];
  created_at: string;
}

export interface Transaction {
  txn_id: string;
  auth_id: string | null;
  consumer_id: string;
  merchant_id: string;
  txn_type: string;
  txn_category: string;
  amount_lak: number;
  mdr_rate: number | null;
  mdr_amount: number | null;
  net_settlement_amount: number | null;
  status: string;
  created_at: string;
}

export interface Settlement {
  settlement_id: string;
  merchant_id: string;
  settlement_date: string;
  total_txn_count: number;
  total_gross_amount: number;
  total_mdr_amount: number;
  total_net_amount: number;
  status: string;
  created_at: string;
}

export interface AuthRequest {
  auth_id: string;
  consumer_id: string;
  merchant_id: string;
  amount_lak: number;
  status: string;
  auth_code: string | null;
  created_at: string;
}

export interface Pagination {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}
