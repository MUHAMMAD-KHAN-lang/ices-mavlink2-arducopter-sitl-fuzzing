# Raw fuzz logs

This directory holds the raw evidence produced by the fuzzing runs, copied
unmodified from the Windows working tree (`pymav/caseN/Fuzz_logs/`).

```text
logs/
├── case1/                  # 100 per-test files, test_000001.txt .. test_000100.txt
├── case2_results.txt
├── case3_results.txt
├── case4_results.txt
├── case5_results.txt
├── case6_results.txt
└── case7_results.txt
```

Case 1 writes one file per test case; Cases 2-7 append to a single results
file. Nothing here has been edited, filtered, or regenerated.

## Which code produced these logs

These logs were produced by the working scripts in `scripts/as-run/`, not by
the cleaned-up release copies in `scripts/windows/`. The two are functionally
the same experiment but are not byte-identical: the release copies were
reformatted and pick up a few explicit settings (`PROCESS_DELAY`,
`SOCKET_TIMEOUT`, `INTER_TEST_DELAY`, named-exception handling) that the
as-run versions either inlined or did not have. Use `scripts/as-run/` when the
question is "what exactly generated this evidence" and `scripts/windows/` when
the question is "how do I run this myself".

## Case 2

`case2_results.txt` is the log of the run recorded in `results/RESULTS_SUMMARY.md`
as a corrected rerun that was started but not completed. It is published as-is.
It is not a record of a full clean 65,280-test pass.
