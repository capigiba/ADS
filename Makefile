install:
	pip install -r requirements.txt
freeze:
	pip freeze > requirements.txt
run:
	streamlit run main.py

clean:
	rm -rf folder_pdf/* scan_results/* evaluate_results/*
	rm -f data/records.csv