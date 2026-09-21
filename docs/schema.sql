CREATE TABLE IF NOT EXISTS erp_customers (
  customer_id VARCHAR(64) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  updated_at VARCHAR(64) NOT NULL
);

CREATE TABLE IF NOT EXISTS erp_products (
  product_id VARCHAR(64) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  unit_price DECIMAL(12,2) NOT NULL,
  updated_at VARCHAR(64) NOT NULL
);

CREATE TABLE IF NOT EXISTS erp_orders (
  order_id VARCHAR(64) PRIMARY KEY,
  customer_id VARCHAR(64) NOT NULL,
  product_id VARCHAR(64) NOT NULL,
  order_date DATE NOT NULL,
  quantity INT NOT NULL,
  unit_price DECIMAL(12,2) NOT NULL,
  status VARCHAR(32) NOT NULL,
  updated_at VARCHAR(64) NOT NULL
);

CREATE TABLE IF NOT EXISTS sync_state (
  entity_name VARCHAR(64) PRIMARY KEY,
  checkpoint_value VARCHAR(64) NOT NULL
);

CREATE TABLE IF NOT EXISTS api_audit_log (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  entity_name VARCHAR(64) NOT NULL,
  outcome VARCHAR(32) NOT NULL,
  row_count INT NOT NULL,
  detail VARCHAR(255) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
