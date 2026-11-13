# Job broker: how dwarves pick jobs, game.x86_64.dll 1.2.39

Module 21, `job_broker_system::calc_assignments` (N 1266464, 7277 bytes). VAs. Static reading, nothing
patched or replayed. [V] = read in the disassembly by me. [S] = read by a subagent, not rechecked.
[I] = inferred.

## Score (worker x job matrix, 0x180137390..0x180137875)
- Filters give score 0: type not allowed, no free workplace slot, unreachable, skill <= 0, eta < 0 [S].
- `B = (age + 100) / (eta + 100)`, age = job +0x90 (0x18013748d..0x1801374c5) [V]. Age grows every update [S].
- Favorite profession: B x 5 (0x1801374e7..0x18013750c) [V].
- `W = 1 + min(job.worked / 60, 1)`, job +0x98 (0x180137510) [S]. Worked accumulates at unassign
  (0x18012a9cd) [V].
- Worker's current job: t = min(elapsed / 300, 1), M = 5 + mult - 4t, F = 1500 + flat - 1500t
  (0x180137593) [S]. JOB_HAUL flat = 10000 (0x1801e872a) [S].
- Else, if the job's workplace (+0x44) is the worker's last workplace (+0x30): t = min(+0x38 / 60, 1),
  M = 1 + 4t, F = 500t (0x180137728..0x1801377b2) [V]. On unassign the workplace is recorded, and time there
  accumulates unless the workplace changed (0x18012a9a9..0x18012a9d4) [V].
- `S = min(B * W * M + F, 1e7) + 1000 * prio`, prio 0/1/2 (0x180137850..0x180137875) [V for the prio term].
- Greedy: take the global max of S x type factor, zero that worker's row (and the job's column when full),
  repeat. Runs about once a second and when a worker goes idle (0x180138c54) [S].

## Type factor: the Job Broker's desired workers (0x180137b5f) [S]
r = picks of this type so far in this run / desired. r <= 0: x3. r < 1: x(3 - 2r). r >= 1: / (1 + 0.3 (cur -
desired)). Desired 0 excludes the type. It multiplies priority too. All 17 types default to 1 (save: u16 array
at job_broker_system/data.bin +1384) [V]. Commands `change_desired_num_workers` +1/-1 are in the Job Broker UI [V].
So once one dwarf is hauling, a free dwarf sees an unstaffed craft type at about 3000 and more hauling at <= 1000 [I].

## Why a haul job starves [I]
Age only appears in B, typically single digits, against flat bonuses of 500 and more. A haul trip ends the job
(`haul_job_is_done` returns 1, 0x1801dda00 [S]), so one 60 s trip gives full stickiness to that destination's
haul workplace. While the dwarf's last workplace has a job, it returns to it (+500, x5). Haul and craft use
separate workplace ids [S]. Haul eta = min over eligible items of (dist(worker, item) + dist(worker, dest) / 2)
/ speed + 10 (0x1801de140) [S]; JOB_HAUL has requires_move = 0 (0x1801e868c) [S]. High priority (2000) beats a
sticky normal job (1000 + 500), which fits the user's raised foundry.
Seen in game (copy of savegame11, t 6403-6671, 10 autosaves): every dwarf on a haul job was hauling to the
cave farm or infirmary; none to the foundry or the 5 construction sites, all with haul jobs open.
Not determined: whether the construction jobs had eta -1 (no eligible item), which scores 0 at any priority [S].

## Patch candidates (soft + age reset is `mods/fair_jobs`)
Original bytes checked against `.hmod-orig` [V].
- Soft: zero the 500 at 0x1801377b5 (`F4 01 00 00`), keeping the x5. Age reset below as well. Bound about
  400-1000 s [I].
- Hard: 0x180137731 `0F 85 82 00 00 00` -> `90 E9 82 00 00 00` removes workplace stickiness. M = 1, F = 0 are
  loaded before it (0x18013758a..0x180137590) [V]. Bound about 100-300 s [I], at the cost of more walking.
- Age reset: 0x18012a9cd `48 01 87 98 00 00 00` -> `48 89 B7 90 00 00 00` (age = rsi, 0 since 0x18012a9ad [V]),
  so age = time since a dwarf last left the job, and W stops growing. Age is then lost on any unassign.

## Test of mods/fair_jobs (copy of savegame11, no input, about 690 game seconds, t 5986-6672)
| | Before (whole_batch_inputs simplified) | With fair_jobs |
|---|---|---|
| Items crafted in the first 13 real minutes | 71 | 107 |
| Copper ingots | 4 | 8 |
| Parts claimed at construction sites | 0 of the 5 sites | cook house 5 of 8, dwelling 4, one bridge finished |
| Dwarf snapshots on haul jobs to the foundry or a site | 0 | 5 of 19 x 6 |
The cook house was not finished: 4 slabs arrived by t 6136, 1 ingot by t 6404, and the smithy took most ingots.
Hauling to the infirmary stayed the most common haul job (25 snapshots). No exceptions or unlocks. Not tested: long
play, crafting output in a settled colony, walking time.

## Priority can starve Normal work (savegame13, t 7530)
Foundry, cook house and infirmary hauling were High (byte +12 of the haul_system destination record), smithy Normal:
no smith item in 21 minutes of play, 9 copper ingots idle, smithy haul job open. Same save with only those four
records changed (smithy High, the others Normal), no input: ladle head about 40 s after play started and a finished Cook's
Ladle after about 155 s (real time; normal speed). That is one run. It did not get equipped: no dwarf's belt changed.


## Builders and the fading current-job bonus (Nov 2026, `mods/builders_finish`)
Verified [V]: current-job branch 0x18013759c..0x180137723: t = min((now - worker+0x28) / 300 s, 1) (magic
0x6d3a06d3a06d3a07, sar 0x17), M = 5 + type+0x110 - 4t, F = 1500 + type+0x10c - 1500t (0x180137719: +0x5dc0000).
Job types: JOB_HAUL flat 10000 (0x1801e872a); every JOB_CRAFT_PROF_<profession> 0/0 (sensor_craft_init 0x1803c39ee
`mov qword [rbp+0x7c], 0`, rbx = profession record). The registered types sit in one array, 0x190 apart, tag at +0.
Recipe +0x980 (16.16) is the work amount: 1.0 for crafts (progress max 100, about 3 per second at normal speed, so
about 33 s), 5.0 for buildings, 2.0 for stairs and bridges. Progress in memory: production_queue_entry +0x540/+0x544
(entries found by recipe* at +0x10 and queued at +0x538). The mod sets JOB_CRAFT_PROF_BUILDER flat to 900.
