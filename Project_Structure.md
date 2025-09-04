stock-ai-agent/
├── README.md                  # High-level overview, setup guide
├── .gitignore                 # Ignore venv, data, secrets
├── requirements.txt           # Python dependencies (or pyproject.toml)
├── environment.yml            # Conda/Mamba env (optional, for M1)
├── docker/                    # Docker configs (optional, for containerization)
│   └── Dockerfile
├── configs/                   # Strategy configs, credentials (templated)
│   ├── config.yaml
│   └── secrets.template.yaml
├── data/                      # Local datasets, caches (gitignored)
│   └── .gitkeep
├── notebooks/                 # Jupyter notebooks for exploration/backtesting
│   └── EDA.ipynb
├── src/                       # Core Python source
│   ├── __init__.py
│   ├── main.py                # Entry point (CLI/daemon)
│   ├── agents/                # Strategy agent classes
│   │   ├── __init__.py
│   │   └── momentum_agent.py
│   ├── data/                  # Data ingestion pipelines
│   │   ├── __init__.py
│   │   └── market_data.py
│   ├── features/              # Feature engineering
│   │   ├── __init__.py
│   │   └── factor_calculator.py
│   ├── models/                # ML models and training code
│   │   ├── __init__.py
│   │   └── model_trainer.py
│   ├── risk/                  # Risk management logic
│   │   └── risk_manager.py
│   ├── execution/             # Broker/Order execution adapters
│   │   └── alpaca_adapter.py
│   └── utils/                 # Helper functions, logging, configs
│       └── logger.py
├── tests/                     # Unit and integration tests
│   ├── __init__.py
│   └── test_market_data.py
└── scripts/                   # Automation scripts (data fetch, training)
    └── fetch_data.sh