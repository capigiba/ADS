install:
	pip install -r requirements.txt
freeze:
	pip freeze > requirements.txt
run:
	source env.sh
	streamlit run main.py