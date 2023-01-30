# Covirally backend

## First run
1. Create virtual environment and install dependencies
```{shell}
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements.dev.txt
```
2. Install `pre-commit` hooks
```{shell}
pre-commit install-hooks
pre-commit install
```
3. Create `.env` file, don't forget to set proper variables
```{shell}
cp .env_example .env
```

## Running locally
1. Run all necessary services
```{shell}
make services
```
2. Apply migrations
```{shell}
make migrate
```
3. Run backend on FastAPI
```{shell}
make dev
```
4. Check http://0.0.0.0:80/docs, everything should be OK!


## Tests
```{shell}
make run_tests
```

## Linter
```{shell}
make format
make lint
```
