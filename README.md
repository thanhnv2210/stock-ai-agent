
python3.12 -m venv venv

source venv/bin/activate

pip3 install -r requirements.txt


pip3 list
Package Version
------- -------
pip     25.0.1


python3 scripts/fetch_data.py --symbol AAPL --start 2020-01-01 --end 2025-01-01


python3 src/features/factor_calculator.py

python3 src/agents/momentum_agent.py

python3 src/backtester/backtester.py

```text
Best Practice: Use __init__.py + python -m approach. This is the cleanest for a multi-module project.
```
python3 -m src.backtester.backtester 


python3 -m src.visualization.visualizer
