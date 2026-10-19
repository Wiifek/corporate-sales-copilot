# Corporate Sales Copilot

Conversational assistant over corporate airline sales dashboards (RAG vs agentic RAG vs context agent).
Work in progress: see the build log below.

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt                       # installs the project in editable mode
python src/copilot/data/generate_synthetic.py --csv   # 1. build the synthetic database
pytest -q                                             # 2. run the tests
streamlit run src/copilot/dashboards/app.py           # 3. open the dashboards
```

## Build log
- [x] Part 1: synthetic dataset (`src/copilot/data`)
- [x] Part 2: knowledge documents (`knowledge/`)
- [x] Part 3: Streamlit dashboards (`src/copilot/dashboards`), with role-based access (`src/copilot/security`)
- [ ] Part 4: retrieval and the three assistants
- [ ] Part 5: evaluation harness and guardrails
- [ ] Part 6: report, CI and deployment
