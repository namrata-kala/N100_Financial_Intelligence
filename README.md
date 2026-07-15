N100 Financial Intelligence Platform

Sprint 1 - Data Foundation

Features
- Excel Loader
- Data Normalization
- Data Quality Validation (DQ-01 to DQ-03)
- SQLite Database
- ETL Pipeline
- Load Audit
- Database Verification

Project Structure

How to Run

python -m src.etl.loader
python -m src.db.init_db
python -m src.db.load_data
python -m src.db.verify_database

Outputs
- output/load_audit.csv
- output/validation_failures.csv