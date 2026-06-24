import csv
import logging
import math
import os
import re
import sys
from collections import defaultdict

# Configure logging to replace print
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def parse_line(line: str) -> dict[str, str]:
    """Parse a log line into a dictionary of key-value pairs."""
    pairs = re.findall(r"\[([^=\]]+)=([^\]]*)\]", line)
    return {k.strip(): v.strip() for k, v in pairs}


def load(path: str) -> list[dict[str, str]]:
    """Load log events from a file."""
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8", errors="ignore") as f:
        for ln in f:
            if ln.startswith("["):
                rows.append(parse_line(ln))
    return rows


def to_float(x: str | None) -> float | None:
    """Convert a string to float, returning None on failure."""
    try:
        return float(x) if x is not None else None
    except (ValueError, TypeError):
        return None


def pct(vals: list[float], p: float) -> float | None:
    """Calculate the p-th percentile of a list of values."""
    if not vals:
        return None
    vals = sorted(vals)
    if len(vals) == 1:
        return vals[0]
    pos = (len(vals) - 1) * (p / 100.0)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return vals[lo]
    return vals[lo] + (vals[hi] - vals[lo]) * (pos - lo)


def main() -> None:
    """Main entry point for the grind logs analyzer."""
    if len(sys.argv) < 2:
        logger.error("Usage: python3 grind_logs_analyzer.py <outdir>")
        sys.exit(1)

    outdir = sys.argv[1]

    inputs = load(os.path.join(outdir, "input_events.txt"))
    refs = load(os.path.join(outdir, "refinement_events.txt"))
    sizes = load(os.path.join(outdir, "size_events.txt"))
    breakout = load(os.path.join(outdir, "breakout_events.txt"))

    input_ids = {r.get("record_id") for r in inputs if r.get("record_id")}
    ref_ids = {r.get("record_id") for r in refs if r.get("record_id")}

    # -------------------------
    # Metric 1: Refinement coverage
    # -------------------------
    total_in = len(input_ids)
    refined = len(input_ids & ref_ids)
    skipped = len(input_ids - ref_ids)
    coverage = (refined / total_in * 100.0) if total_in else 0.0

    with open(
        os.path.join(outdir, "metric_refinement_coverage.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as fp:
        w = csv.writer(fp)
        w.writerow(
            [
                "total_input_records",
                "refined_records",
                "skipped_records",
                "refinement_coverage_pct",
            ]
        )
        w.writerow([total_in, refined, skipped, round(coverage, 4)])

    # -------------------------
    # Metric 2: Avg + p50/p95 reduction
    # -------------------------
    reductions = [to_float(r.get("reduction")) for r in refs]
    reductions = [x for x in reductions if x is not None]
    avg_red = (sum(reductions) / len(reductions)) if reductions else None
    p50 = pct(reductions, 50) if reductions else None
    p95 = pct(reductions, 95) if reductions else None

    bucket_vals = defaultdict(list)
    for r in refs:
        ts = r.get("timestamp", "")
        m = re.match(r"^([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2})", ts)
        v = to_float(r.get("reduction"))
        if m and v is not None:
            bucket_vals[m.group(1)].append(v)

    with open(
        os.path.join(outdir, "metric_avg_percent_reduction.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as fp:
        w = csv.writer(fp)
        w.writerow(
            [
                "n",
                "avg_reduction_pct",
                "p50_reduction_pct",
                "p95_reduction_pct",
                "min",
                "max",
            ]
        )
        if reductions:
            w.writerow(
                [
                    len(reductions),
                    round(avg_red, 4),
                    round(p50, 4),
                    round(p95, 4),
                    min(reductions),
                    max(reductions),
                ]
            )
        else:
            w.writerow([0, "", "", "", "", ""])

    with open(
        os.path.join(outdir, "metric_reduction_over_time.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as fp:
        w = csv.writer(fp)
        w.writerow(
            [
                "hour_bucket",
                "n",
                "avg_reduction_pct",
                "p50_reduction_pct",
                "p95_reduction_pct",
                "min",
                "max",
            ]
        )
        for b in sorted(bucket_vals):
            vals = bucket_vals[b]
            w.writerow(
                [
                    b,
                    len(vals),
                    round(sum(vals) / len(vals), 4),
                    round(pct(vals, 50), 4),
                    round(pct(vals, 95), 4),
                    min(vals),
                    max(vals),
                ]
            )

    # -------------------------
    # Metric 3: # >5MB reduced below 5MB
    # -------------------------
    eligible = 0
    crossed = 0
    for r in sizes:
        i = to_float(r.get("input_size"))
        o = to_float(r.get("refined_size"))
        if i is None or o is None:
            continue
        eligible += 1
        if i > 5.0 and o < 5.0:
            crossed += 1

    rate = (crossed / eligible * 100.0) if eligible else 0.0
    with open(
        os.path.join(outdir, "metric_above5_to_below5.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as fp:
        w = csv.writer(fp)
        w.writerow(["eligible_with_sizes", "count_above5_reduced_below5", "rate_pct"])
        w.writerow([eligible, crossed, round(rate, 4)])

    # -------------------------
    # Metric 4: Breakouts (condition/jurisdiction)
    # -------------------------
    def write_breakout(key: str, filename: str) -> int:
        grp = defaultdict(list)
        for r in breakout:
            k = r.get(key)
            v = to_float(r.get("reduction"))
            if k and v is not None:
                grp[k].append(v)

        with open(
            os.path.join(outdir, filename), "w", newline="", encoding="utf-8"
        ) as fp:
            w = csv.writer(fp)
            w.writerow([key, "n", "avg_reduction_pct", "p50", "p95", "min", "max"])
            rows = []
            for k, vals in grp.items():
                rows.append(
                    (
                        k,
                        len(vals),
                        sum(vals) / len(vals),
                        pct(vals, 50),
                        pct(vals, 95),
                        min(vals),
                        max(vals),
                    )
                )
            rows.sort(key=lambda x: x[2], reverse=True)
            for k, n, avg, p50v, p95v, mn, mx in rows:
                w.writerow(
                    [k, n, round(avg, 4), round(p50v, 4), round(p95v, 4), mn, mx]
                )

        return len(grp)

    n_cond = write_breakout("condition", "metric_reduction_by_condition.csv")
    n_jur = write_breakout("jurisdiction", "metric_reduction_by_jurisdiction.csv")

    # -------------------------
    # Key discovery for missing fields
    # -------------------------
    sample_path = os.path.join(outdir, "refinement_raw_sample.txt")
    key_counts = defaultdict(int)
    if os.path.exists(sample_path):
        with open(sample_path, encoding="utf-8", errors="ignore") as sample_file:
            for ln in sample_file:
                for k, _ in re.findall(r"\[([^=\]]+)=([^\]]*)\]", ln):
                    key_counts[k] += 1

    interesting = [
        k
        for k in key_counts
        if any(
            x in k.lower()
            for x in [
                "size",
                "mb",
                "mib",
                "byte",
                "condition",
                "measure",
                "program",
                "jurisdiction",
                "state",
                "county",
                "code",
                "reduction",
            ]
        )
    ]
    interesting = sorted(interesting)

    with open(
        os.path.join(outdir, "key_discovery_candidates.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as fp:
        w = csv.writer(fp)
        w.writerow(["key", "seen_count"])
        for k in interesting:
            w.writerow([k, key_counts[k]])

    # -------------------------
    # Console summary
    # -------------------------
    logger.info("\n=== KPI Summary ===")
    logger.info(f"Refinement coverage: {refined}/{total_in} = {coverage:.2f}%")
    if reductions:
        logger.info(
            f"Average % reduction: {avg_red:.2f}% (p50={p50:.2f}, p95={p95:.2f}, n={len(reductions)})"
        )
    else:
        logger.info("Average % reduction: unavailable (no reduction field parsed)")
    logger.info(f">5MB to <5MB: {crossed}/{eligible} ({rate:.2f}%)")
    logger.info(f"Condition breakout groups: {n_cond}")
    logger.info(f"Jurisdiction breakout groups: {n_jur}")

    if eligible == 0:
        logger.info(
            "NOTE: size threshold metric is blank because no recognized input/refined size fields were found."
        )
    if n_cond == 0 or n_jur == 0:
        logger.info(
            "NOTE: condition/jurisdiction breakout is blank because those fields were not found with current key patterns."
        )

    logger.info("\nPotential useful keys seen in refinement sample:")
    if interesting:
        for k in interesting:
            logger.info(f" - {k} (seen {key_counts[k]}x)")
    else:
        logger.info(" - none found in sampled parsed fields")

    logger.info("\nCSV outputs:")
    for fn in [
        "metric_refinement_coverage.csv",
        "metric_avg_percent_reduction.csv",
        "metric_reduction_over_time.csv",
        "metric_above5_to_below5.csv",
        "metric_reduction_by_condition.csv",
        "metric_reduction_by_jurisdiction.csv",
        "key_discovery_candidates.csv",
    ]:
        logger.info(f" - {os.path.join(outdir, fn)}")


if __name__ == "__main__":
    main()
