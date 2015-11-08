PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE nodes (
  node_id INTEGER PRIMARY KEY,
  port1 REAL,
  port2 REAL,
  port3 REAL,
  port4 REAL,
  low_battery REAL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TRIGGER nodes_updated_at AFTER UPDATE ON nodes
  FOR EACH ROW
  BEGIN
  UPDATE nodes SET updated_at = CURRENT_TIMESTAMP WHERE node_id = old.node_id;
  END;
COMMIT;
