LOG_FILE := env('LOG_FILE', '~/Downloads/production-refiner-lambda.log')
OUTDIR := env('OUTDIR', '~/Downloads/refiner_reports')

EXTRACT_SCRIPT := '../sh/grind_logs_extract.sh'
ANALYZER_SCRIPT := '../py/grind_logs_analyzer.py'

alias h := _default
alias help := _default
alias kpi := kpi-extract
alias r := run

@_default:
    just --list logs

[doc('Extract the KPI metrics using `angle-grinder` from a APHL-provided log file. Define `LOG_FILE` and `OUTDIR` environment variables prior to recipe to override the defaults (e.g. `LOG_FILE=/some/path.log OUTDIR=/some/directory just logs kpi-extract`)')]
[group('logs')]
kpi-extract:
    mkdir -p {{ OUTDIR }}
    bash {{ EXTRACT_SCRIPT }} {{ LOG_FILE }} {{ OUTDIR }}
    python3 {{ ANALYZER_SCRIPT }} {{ OUTDIR }}

[doc('Run arbitrary queries on `LOG_FILE` using `angle-grinder`')]
[group('logs')]
run query:
    AG_BIN=$(command -v agrind || command -v angle-grinder) \
    if [ -z "$AG_BIN" ]; then echo "agrind not found"; exit 1; fi \
    if [[ "$AG_BIN" =~ agrind$ ]]; then \
        $AG_BIN --file {{ LOG_FILE }} "{{ query }}"; \
    else \
        $AG_BIN -- -f {{ LOG_FILE }} "{{ query }}"; \
    fi
