#!/usr/bin/env bash
set -euo pipefail

LOG_FILE="${1}"
OUTDIR="${2}"

AG_BIN="$(command -v agrind || command -v angle-grinder || true)"
[[ -n "$AG_BIN" ]] || { echo "Error: agrind/angle-grinder not found in PATH"; exit 1; }
[[ -f "$LOG_FILE" ]] || { echo "Error: log file not found: $LOG_FILE"; exit 1; }

run_agrind() {
  local q="$1"
  if [[ "$AG_BIN" =~ agrind$ ]]; then
    "$AG_BIN" --file "$LOG_FILE" "$q"
  else
    "$AG_BIN" -- -f "$LOG_FILE" "$q"
  fi
}

count_rows() {
  local f="$1"
  grep -c '^\[' "$f" 2>/dev/null || echo 0
}

echo "Extracting input events..."
run_agrind '
* | parse regex "\"operation\":\"(?<operation>[^\"]+)\""
  | where operation == "input_analysis"
  | parse regex "\"record_id\":\"(?<record_id>[^\"]+)\""
  | parse regex "\"timestamp\":\"(?<timestamp>[^\"]+)\""
  | fields record_id, timestamp
' > "$OUTDIR/input_events.txt" || true
echo "  input_events rows: $(count_rows "$OUTDIR/input_events.txt")"

echo "Extracting refinement events (minimal, reliable)..."
run_agrind '
* | parse regex "\"operation\":\"(?<operation>[^\"]+)\""
  | where operation == "refinement_complete"
  | parse regex "\"record_id\":\"(?<record_id>[^\"]+)\""
  | parse regex "\"timestamp\":\"(?<timestamp>[^\"]+)\""
  | parse regex "\"(?:eicr_size_reduction|size_reduction|reduction_pct|reduction_percent)\":(?<reduction>[0-9.]+)"
  | fields record_id, timestamp, reduction
' > "$OUTDIR/refinement_events.txt" || true
echo "  refinement_events rows: $(count_rows "$OUTDIR/refinement_events.txt")"

echo "Extracting size candidates..."
run_agrind '
* | parse regex "\"operation\":\"(?<operation>[^\"]+)\""
  | where operation == "refinement_complete"
  | parse regex "\"record_id\":\"(?<record_id>[^\"]+)\""
  | parse regex "\"timestamp\":\"(?<timestamp>[^\"]+)\""
  | parse regex "\"(?:eicr_size_mib|input_size_mib|input_mb|original_size_mb|original_size_mib|incoming_size_mb|incoming_size_mib|pre_refine_size_mb|pre_refine_size_mib)\":(?<input_size>[0-9.]+)"
  | parse regex "\"(?:eicr_size_mb|refined_size_mb|output_size_mb|final_size_mb|refined_size_mib|post_refine_size_mb|post_refine_size_mib)\":(?<refined_size>[0-9.]+)"
  | fields record_id, timestamp, input_size, refined_size
' > "$OUTDIR/size_events.txt" || true
echo "  size_events rows: $(count_rows "$OUTDIR/size_events.txt")"

echo "Extracting condition/jurisdiction candidates..."
run_agrind '
* | parse regex "\"operation\":\"(?<operation>[^\"]+)\""
  | where operation == "refinement_complete"
  | parse regex "\"record_id\":\"(?<record_id>[^\"]+)\""
  | parse regex "\"timestamp\":\"(?<timestamp>[^\"]+)\""
  | parse regex "\"(?:eicr_size_reduction|size_reduction|reduction_pct|reduction_percent)\":(?<reduction>[0-9.]+)"
  | parse regex "\"(?:condition|condition_name|condition_code|measure|program|trigger_condition)\":\"(?<condition>[^\"]+)\""
  | parse regex "\"(?:jurisdiction|state|county|reporting_jurisdiction|site_state|receiver_state)\":\"(?<jurisdiction>[^\"]+)\""
  | fields record_id, timestamp, reduction, condition, jurisdiction
' > "$OUTDIR/breakout_events.txt" || true
echo "  breakout_events rows: $(count_rows "$OUTDIR/breakout_events.txt")"

echo "Extracting refinement raw sample for key discovery..."
run_agrind '
* | parse regex "\"operation\":\"(?<operation>[^\"]+)\""
  | where operation == "refinement_complete"
  | limit 100
' > "$OUTDIR/refinement_raw_sample.txt" || true
echo "  refinement_raw_sample rows: $(count_rows "$OUTDIR/refinement_raw_sample.txt")"
