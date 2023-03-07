#!/bin/bash

# shellcheck disable=SC2016
: '
  Usage:
  `./.ci/lint.sh <command> <path-to-code-directory>`,
  example `./.gitlab/lint.sh format .`

  Default <path-to-code-directory> equals to CWD, so you may execute this script from project root dir:
  `./.ci/lint.sh format`

  Commands:

  install - install all required dependecies via pip install

  check - check all *.py files by all intsalled linters according to setup.cfg/pyproject.toml

  format - format all code files via black

  check-black - black linter
  check-flake8 - flake8 check
  check-mypy - mypy typings check

  diff-black - show difference of black linters
'

SCRIPT_NAME=$0
COMMAND=$1
FILEPATH=${2:-.}

function handle_exit {
    EXIT_CODE=$1
    if [[ $EXIT_CODE -ne 0 ]]; then
        echo $2
    fi
    exit $EXIT_CODE
}

case ${COMMAND} in
    check-black)
        black --config ./pyproject.toml --check ${FILEPATH}
        handle_exit $? "Formatting error! Run \`$SCRIPT_NAME format\` to format the code"
        ;;
    check-flake8)
        flake8 --color always --config ./setup.cfg ${FILEPATH}
        handle_exit $? "Flake8 error!"
        ;;
    check-mypy)
        mypy --config ./mypy.ini ${FILEPATH}
        handle_exit $? "Mypy error!"
        ;;
    check-pylint)
        pylint --rcfile=.pylintrc app/
        handle_exit $? "Pylint error!"
        ;;
    check)
        set -e
        echo -n "Black: " && $SCRIPT_NAME check-black
        echo "Checking Flake8..." && $SCRIPT_NAME check-flake8
        echo -n "Mypy: " && $SCRIPT_NAME check-mypy
        echo -n "Pylint: " && $SCRIPT_NAME check-pylint
        ;;

    format)
        black --config ./pyproject.toml ${FILEPATH}
        ;;

    install)
        pip install -r ./requirements.dev.txt
        pre-commit install
        ;;

    diff-black)
        black --config ./pyproject.toml --diff ${FILEPATH}
        ;;
    *)
        echo $"Usage: $SCRIPT_NAME {check|check-black|check-flake8|check-mypy|check-pylint|format|diff-black|install}"
        exit 1
esac
