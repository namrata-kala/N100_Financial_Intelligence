.PHONY: load ratios test report dashboard api clean

load:
	@echo "Loading Excel files into nifty100.db..."
	python3 src/db/load_data.py

ratios:
	@echo "Generating and populating financial_ratios table..."
	python3 src/analytics/populate_financial_ratios.py

test:
	@echo "Running full pytest suite..."
	PYTHONPATH=. python3 -m pytest tests/ --html=reports/pytest_report.html

report:
	@echo "Generating PDF reports (Tearsheets, Sector, Portfolio)..."
	python3 src/reports/batch_generator.py

dashboard:
	@echo "Launching Streamlit Dashboard..."
	streamlit run src/dashboard/app.py --server.port 8501

api:
	@echo "Launching FastAPI server..."
	uvicorn src.api.main:app --port 8000 --reload

clean:
	@echo "Cleaning cache and test artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache
	rm -f reports/pytest_report.html
	@echo "Clean complete. Database remains untouched."
