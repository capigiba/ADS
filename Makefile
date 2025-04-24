install:
	pip install -r requirements.txt
freeze:
	pip freeze > requirements.txt
run:
	streamlit run main.py