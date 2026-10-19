# UX & Combat Guide (player-facing + designer-facing)

## 1. How heroes pick targets
Each basic attack scores every enemy **within reach** (range + leash) using 7 components, each normalized to 0..1:

| Component | Meaning | Base weight |
|---|---|---|
| profile | the hero's own targeting profile (Closest / Lowest HP / Strongest…), as a rank | 1.0 |
| threat | how close the enemy is to the Crystal (sappers/sieges ×1.3) | 0.6 (+0.4 Guardian) |
| kill | can die within ~2 hits, or is already wounded | 0.3 |
| reaction | the hit's element would trigger a reaction on the current aura | 0.3 |
| priority | boss = 1, elite = 0.7 | 0.2 (+0.2 Assassin/Ranger) |
| cluster | number of enemies around it (AoE value) | 0.1 |
| reach | the closer the enemy, the less chasing | 0.3 |

**Team tactic** (chosen on the prepare screen) only adds weight; it never forces a target:
- Balanced — default.
- Protect Crystal — threat +0.8.
- Focus Boss — priority +1.0.
- Elemental Chain — reaction +0.8.
- Crowd Control — cluster +0.8.

**Hysteresis 0.15:** a hero only switches when the new target scores at least 0.15 higher, so it doesn't flicker. Tied scores go to the lower uid, so the choice is deterministic. Skills keep their own targeting.
The AI inspector (Settings → Show ranges) shows each hero's components, its runner-up target and why it kept its target.

## 2. Crystal Evolution (after wave 6, once per run)
| Path | Effect | When to pick |
|---|---|---|
| Bastion | −7% damage taken, regenerates 0.15% max HP per second | The Crystal is often hit by leakers/sappers |
| Aether Pulse | every 6 s, an Arcane nova (55 × wave scale) hits enemies within 3.2 m | Many small enemies reach the Crystal |
| Thornheart | +45 thorns (Earth, × wave scale) back at every attacker | Bruiser/siege enemies stand and hit the Crystal |
The choice is permanent and exclusive. It is saved with the run. Feature flag: `FeatureFlags.CrystalEvolution`. Tuned so that no path dominates: forcing each path (150 seeds × 12 lineups × scripted/greedy) gives Bastion 16.8/13.8%, Pulse 15.1/12.4%, Thorn 14.6/12.6% (overlapping CIs). An earlier version had Bastion ahead by ~5 points.

## 3. Shop & draft
- **Lock** one item: it survives rerolls and waits in the next shop at its old price. Buying it clears the lock.
- Reroll costs go up within a screen, and gold never goes negative.
- A 3-card draft always has at least 1 card that works now and at least 1 strategic alternative (not 3 copies of the current plan).

## 4. Readability & accessibility
- Damage numbers: hits on the same target within 0.3 s merge into one number that grows; crits stay separate.
- Flash intensity 0–100% (photosensitivity), Reduced VFX, screen shake on/off, high contrast.
- Pause when unfocused (default on), battery saver (30 FPS + reduced VFX).
- **Unverified:** none of this has been checked on screen (no Unity editor here); only the pure logic is tested.

## 5. After a run
The results screen shows the turning points:
- the threat that did the most damage to the Crystal;
- the closest save (the wave with the lowest Crystal HP);
- the decisive upgrade (the relic/evolution with the most attributed damage).
"Copy build" copies a share code `AW1 seed=… mode=… asc=… biome=… heroes=… relics=…`. A seed only replays the same run on the same content version (content hash).
