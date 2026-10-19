# Headless soak (simulation only)

> **Not a Unity profile.** .NET 8 headless simulation on the CI/dev container; Unity FPS, rendering, GC spikes on device and draw calls were not measured (no Unity editor/player here).

- Command: `dotnet run --project Tools/SimHarness/Balance -c Release -- --soak 40` · Endless, seed 777, strategy balanced, Crystal made unkillable (stress mode: reaches late waves)
- Reached wave 41 (Prepare); wall clock 1.8s; machine 4 threads, .NET 8.0.31
- Allocated during soak: 51.8 MB (GC counts include the forced per-wave collections used to measure retained memory: gen0 80, gen2 80)
- Budget reference: one tick = 33.3 ms of game time; the simulation should stay far below ~2 ms/tick to leave room for Unity rendering on mobile.

| Wave | Ticks | ms/tick (avg) | ms/tick (max) | Peak enemies | Peak zones+projectiles | Retained MB after (post-GC) |
|---|---|---|---|---|---|---|
| 1 | 588 | 0.068 | 8.47 | 3 | 3 | 1.5 |
| 2 | 848 | 0.010 | 0.50 | 9 | 2 | 1.5 |
| 3 | 644 | 0.014 | 0.64 | 15 | 2 | 1.5 |
| 4 | 661 | 0.009 | 0.41 | 7 | 2 | 1.5 |
| 5 | 2552 | 0.019 | 3.23 | 13 | 6 | 1.5 |
| 6 | 2402 | 0.012 | 0.44 | 19 | 6 | 1.5 |
| 7 | 815 | 0.020 | 0.27 | 12 | 9 | 1.5 |
| 8 | 2552 | 0.013 | 0.50 | 18 | 6 | 1.4 |
| 9 | 884 | 0.024 | 4.12 | 17 | 10 | 1.4 |
| 10 | 2478 | 0.012 | 4.07 | 7 | 4 | 1.4 |
| 11 | 844 | 0.018 | 0.62 | 16 | 8 | 1.4 |
| 12 | 2146 | 0.020 | 4.13 | 22 | 12 | 1.4 |
| 13 | 847 | 0.023 | 0.67 | 15 | 10 | 1.4 |
| 14 | 1156 | 0.031 | 0.71 | 28 | 13 | 1.4 |
| 15 | 1227 | 0.026 | 4.04 | 15 | 8 | 1.4 |
| 16 | 1019 | 0.027 | 0.14 | 26 | 9 | 1.4 |
| 17 | 1479 | 0.028 | 4.21 | 22 | 14 | 1.4 |
| 18 | 1399 | 0.035 | 4.16 | 39 | 13 | 1.4 |
| 19 | 3152 | 0.025 | 0.49 | 47 | 11 | 1.4 |
| 20 | 4131 | 0.013 | 1.27 | 12 | 10 | 1.5 |
| 21 | 1039 | 0.019 | 0.21 | 21 | 10 | 1.5 |
| 22 | 1397 | 0.030 | 1.30 | 26 | 11 | 1.5 |
| 23 | 949 | 0.037 | 0.17 | 22 | 12 | 1.5 |
| 24 | 1297 | 0.074 | 4.23 | 32 | 15 | 1.5 |
| 25 | 1911 | 0.041 | 4.18 | 19 | 11 | 1.5 |
| 26 | 1142 | 0.035 | 0.40 | 29 | 11 | 1.5 |
| 27 | 1583 | 0.040 | 1.73 | 23 | 12 | 1.5 |
| 28 | 3002 | 0.037 | 4.18 | 40 | 14 | 1.5 |
| 29 | 3152 | 0.020 | 0.49 | 51 | 11 | 1.5 |
| 30 | 7142 | 0.009 | 0.43 | 17 | 10 | 1.5 |
| 31 | 1010 | 0.012 | 0.15 | 18 | 15 | 1.5 |
| 32 | 2552 | 0.014 | 0.55 | 31 | 14 | 1.5 |
| 33 | 1071 | 0.015 | 0.13 | 22 | 16 | 1.5 |
| 34 | 1825 | 0.020 | 0.29 | 37 | 13 | 1.5 |
| 35 | 2989 | 0.010 | 0.10 | 22 | 11 | 1.5 |
| 36 | 1126 | 0.018 | 0.23 | 30 | 15 | 1.5 |
| 37 | 1675 | 0.021 | 0.22 | 25 | 16 | 1.5 |
| 38 | 1922 | 0.020 | 0.87 | 45 | 16 | 1.5 |
| 39 | 1575 | 0.027 | 2.09 | 51 | 16 | 1.5 |
| 40 | 7201 | 0.007 | 0.44 | 17 | 12 | 1.5 |
