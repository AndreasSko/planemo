#!/bin/bash

# Usage: DOC_TEST_RUNNER="https://raw.githubusercontent.com/galaxyproject/planemo/master/scripts/run_doc_test.sh"
#        DOCS=building bash <(curl -s "$DOC_TEST_RUNNER")
#        DOCS=conda bash <(curl -s "$DOC_TEST_RUNNER")
#        DOCS=conda_cwl bash <(curl -s "$DOC_TEST_RUNNER")

set -e

: ${PLANEMO_TARGET:="."}
: ${PLANEMO_VIRTUAL_ENV:=".venv-doc-tests"}
: ${DOCS:="building"}

# Ensure Planemo is installed.
if [ ! -d "${PLANEMO_VIRTUAL_ENV}" ]; then
    virtualenv "${PLANEMO_VIRTUAL_ENV}"
    . "${PLANEMO_VIRTUAL_ENV}"/bin/activate
    pip install -U pip>7
    pip install toil==3.15.0
    # Intentionally expand wildcards in PLANEMO_TARGET.
    shopt -s extglob
    pip install ${PLANEMO_TARGET}
fi
. "${PLANEMO_VIRTUAL_ENV}"/bin/activate

planemo --verbose conda_init || true
export PATH="$HOME/miniconda3/bin:$PATH"

PLANEMO_DOC_TEST_PATH="docs/tests/tests_${DOCS}.sh"
if [ -f $PLANEMO_DOC_TEST_PATH ];
then
    bash "$PLANEMO_DOC_TEST_PATH"
else
    bash <(curl -s "https://raw.githubusercontent.com/galaxyproject/planemo/master/$PLANEMO_DOC_TEST_PATH")
fi
