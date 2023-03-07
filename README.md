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
1. Run all necessary services (DB and so on)
```{shell}
make services
```
2. Apply migrations
```{shell}
make migrate
```
3. Run backend on FastAPI (in separate terminal window)
```{shell}
make dev
```
4. Check http://0.0.0.0:80/docs, everything should be OK!


## Testing
Some steps should be made to run tests.

1. Tests must be run only with `APP_ENV=test`, there will be an error otherwise.
2. Test database must be running. One can do this via command:
    ```shell
    make test_services
    ```
   **NB**: It's not necessary to change your `DATABASE_URL` env.
   There is automatic replacemet of database name while running tests.

After that you can run your tests:

```{shell}
make run_tests
```

## Linter
```{shell}
make format
make linters
```
