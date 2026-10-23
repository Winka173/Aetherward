# Simulation performance probe

Six level-5 heroes with mixed elements, desktop .NET 8 (JIT), single thread. Not a device measurement.

| Wave | Ticks | Peak enemies | Avg µs/tick | Max µs/tick | Max reactions/s |
|---|---|---|---|---|---|
| 11 | 913 | 22 | 105.9 | 2384 | 5 |
| 14 | 1370 | 38 | 103.6 | 4634 | 19 |
| 18 | 1389 | 41 | 105.4 | 20426 | 26 |
| 19 | 1536 | 60 | 196.4 | 11163 | 23 |
| 20 | 2906 | 26 | 107.8 | 16234 | 18 |

## Saturated Haven simulation

160 durable enemies at the gates, six level-5 heroes, 900 ticks per biome. Includes reactions and combat journals; excludes Unity rendering, audio and VFX. Times may include OS scheduling pauses.

| Biome | Peak enemies | Avg µs/tick | p95 µs/tick | Max µs/tick |
|---|---|---|---|---|
| verdant_sanctuary | 160 | 887.4 | 2729.5 | 12201.3 |
| molten_crater | 160 | 700.3 | 3207.0 | 11398.6 |
| frostfall_bastion | 160 | 212.7 | 673.6 | 4345.3 |
| shattered_aether | 160 | 268.5 | 854.6 | 17428.9 |
| stormspire_citadel | 160 | 186.8 | 545.9 | 2251.2 |
| sunken_archive | 160 | 191.0 | 650.0 | 5884.3 |
