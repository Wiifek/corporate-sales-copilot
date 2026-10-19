# Shortcuts (on Windows without make, just run the commands on the right).
data:       ## generate the synthetic database
	python src/copilot/data/generate_synthetic.py --csv
test:       ## run all tests (offline)
	pytest -q
app:        ## launch the dashboards and the assistant
	streamlit run src/copilot/dashboards/app.py
index:      ## build the vector index
	python -m copilot.rag.index
retrieval:  ## retrieval hit-rate on the benchmark questions
	python -m copilot.evaluation.retrieval
ask:        ## usage: make ask Q="What is a hub?"
	python -m copilot.ask "$(Q)" --show-context
