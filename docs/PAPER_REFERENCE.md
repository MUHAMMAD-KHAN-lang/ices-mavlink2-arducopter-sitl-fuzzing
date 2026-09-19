# Original paper reference

**Domin, Karel; Symeonidis, Iraklis; Marin, Eduard. (2016). _Security Analysis of the Drone Communication Protocol: Fuzzing the MAVLink protocol_.** E-print / working paper, 7 pages.

Official University of Luxembourg record:
https://hdl.handle.net/10993/37613

ORBilu record:
https://orbilu.uni.lu/handle/10993/37613

Open-access full text (publisher-hosted):
https://publications.uni.lu/bitstream/10993/37613/1/article-2667.pdf

**This repository does not host or redistribute a copy of the paper.** The paper
is the copyrighted work of its authors and publisher; obtain it from the ORBilu
record above.

## How this repository relates to the paper

The paper proposes fuzzing MAVLink implementations by injecting invalid or semi-valid data and observing unexpected software behaviour. It describes a Python fuzzer and seven test cases. The original wire format is MAVLink 1; the paper explicitly uses magic byte `FE`.

This project is based on and modernizes the fuzzing methodology described by Karel Domin, Iraklis Symeonidis, and Eduard Marin in their 2016 work on MAVLink security testing. The original work targeted MAVLink 1. This repository contains an independent adaptation of the methodology for MAVLink 2 using modern ArduPilot/ArduCopter SITL, Python, and automated monitoring — written by Muhammad Hamza, who is not an author of the 2016 paper. It follows the paper's seven-case testing idea but **modernizes the packet layer to MAVLink 2** for the current ArduCopter SITL environment. The repository therefore should be described as a **MAVLink 2 adaptation / reproduction study**, not as the exact historical implementation.

The paper itself reported a floating-point exception during its experiments and discussed using GDB/core dumps for further investigation. The current repository has not yet added that level of crash forensics; it currently uses a lightweight process/port monitor.
