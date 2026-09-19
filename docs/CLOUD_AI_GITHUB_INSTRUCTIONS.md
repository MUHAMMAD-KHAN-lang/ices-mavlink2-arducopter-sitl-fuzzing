# Instructions for a cloud coding AI uploading this repository to GitHub

## Repository identity

Suggested repository name:

```text
ices-mavlink2-arducopter-sitl-fuzzing
```

Suggested short description:

```text
MAVLink 2 fuzzing of ArduCopter SITL for the ICES emergency communications research program, based on the 2016 Domin–Symeonidis–Marin MAVLink fuzzing study.
```

Suggested repository topics:

```text
mavlink
mavlink2
ardupilot
arducopter
sitl
fuzzing
uav-security
drone-security
cybersecurity
ices
emergency-communications
```

## Upload instructions

1. Preserve the directory structure.
2. Do not delete the documentation or case scripts.
3. Make the repository public only after confirming that no private credentials, IP secrets, tokens, or proprietary material are included.
4. Keep the original paper attribution and links in `docs/PAPER_REFERENCE.md` and `README.md`.
5. Do not claim that Case 2 is fully completed; the current recorded result says the corrected full rerun is pending.
6. Do not claim that no vulnerabilities exist. The measured statement is only that no crash was detected under the recorded test conditions.
7. Keep raw fuzz logs out of the repository if they become extremely large; use a release artifact or Git LFS if appropriate.

## Recommended first commit

```text
Initial public release: MAVLink 2 ArduCopter SITL fuzzing framework for ICES
```

## Recommended README title

```text
MAVLink 2 Fuzzing of ArduCopter SITL for ICES — a modern adaptation of
“Security Analysis of the Drone Communication Protocol: Fuzzing the MAVLink protocol” (2016)
```
