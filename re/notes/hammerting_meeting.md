# Hammerting meeting softlock (BUGS.md A11), game.x86_64.dll 1.2.39

Addresses are VAs (image base 0x180000000). `tools/disasm.py` takes N = VA - 0x180001000.
Modules dumped for this note: 79 command_hammerting, 31 talk_system, 133 talk_system.ecs,
173 action_talk, 174 action_work, 245 node_talk, 16 navgraph_query_system, 15 fixed_transform.
Bytes are from the pristine DLL (`game.x86_64.dll.hmod-orig`); no site below is touched by the
installed mods. Time is gamefp 16.16 seconds (`gamestate+0xd0` = now; 0x10000 = 1 s).
There is no "meeting system": a Hammerting is the talk (small-talk) system's one **global
conversation**, held at the Great Hall. Data: `database/hammertings/hammertings_cdb.bin`
(10 records: HAMMERTING_COLONIAL_CHARTER, CLAN_LAW, ...; `hammerting_record` = tag, key-value
costs, dependencies, tier), modifiers in `database/modifier/modifier/hammerting_modifiers_cdb.bin`.
The rules that matter are code; there is nothing to fix in data.

## Lifecycle
1. **Call.** Great Hall panel (`entity/ui/building_greathall/building_greathall.entity`): pick a
   law in the tier tree (`SELECTED_HAMMERTING`), press the LABEL__HOLD_HAMMERTING button =
   `EXECUTE_COMMAND('hold_hammerting', GAME_CTX, <record hash>)`. No hotkey.
   - is_valid 0x1802f30d0 -> `hammerting_available` 0x1802dc740: record exists, personal unlock
     status == 3, **no global conversation place set** (0x1802dc7bf), no modifier of class
     HAMMERTING_HAMMERTING_TIMED on the game entity (cooldown, 0x1802dc7ce).
   - execute 0x1802f3160: `talk_system_set_global_conversation_place(hall)` (0x1802f31ce; it is
     just `talk_data+0x68 = hall`, 0x1801aee60); KV_LATEST_HAMMERTING = record hash on the game
     entity (0x1802f3201); modifier HAMMERTING_HOUSE_IN_SESSION (class HAMMERTING_HAMMERTING_GHMOD)
     on the hall (0x1802f330c; UI "Great Hall in Session": attendees get more hunger, greed and
     weariness); event TDTD_EVENT_HOLD_HAMMERTING (achievement / MISSION_GEN_HOLD_HAMMERTING).
2. **Summons** (talk_system_update 0x1801b5b40, every update). Talk component 0x50 bytes in
   `talk_data+0` (count +8): entity +0, state +4, nearby list +8 (count +0x48), conversation id
   +0x4a, assigned place +0x4c. States: 0 none, 1 wants to talk, 2 joined/walking, 3 seated
   (talking), 4 conversation over.
   - Reset loop 0x1801b6150: every component in state 0/1 is reset to 0, then, if the dwarf's
     current utility action exists and (rank < 5 or it is ACTION_TALK) (0x1801b61af):
     **with a meeting set, state = 1 at once** (0x1801b61c2 `66 83 78 68 00 75 5a`). Without a
     meeting the small-talk gates apply: gp last edge WALK, last node types TILE,
     `job_broker_system_is_worker_available_for_smalltalk`, not CURRENTLY_IN_OVERWORLD. The
     meeting skips all of them.
   - Places 0x1801b62a8: with a meeting the only place is the hall (else the pubs). A place is
     a candidate only while its conversation has room: participants < max (0x1801b642d), max =
     number of gamepath nodes tagged "interact" on the hall (CONVERSATION_NODE_TAG 0x18059d7f0).
   - Assignment 0x1801b6970: each state-1 dwarf is set to 0 (0x1801b6adb), then gets the place
     if his navgraph query "movement" (MOVEMENT_HASH 0x18059d628) has reached the hall's **first**
     interact node (result +0xc != 0, 0x1801b6c37); the hall is taken at any path cost
     (0x1801b6c47). Final pass 0x1801b6d00: a place with >= 2 (assigned + participants) puts its
     dwarves back to state 1. So unreachable dwarves are dropped each tick and, when the hall is
     full, the rest get state 0 and keep working.
   - Every dwarf with talk state != 0 cannot work: action_work's consideration_motivation
     (0x1803bf7d0) returns 0 while a meeting is set and the dwarf's talk state != 0.
3. **ACTION_TALK** (utility_action_talk_register 0x1803be170): rank 5 (`c7 45 40 05 00 00 00`
   at 0x1803be21e), one consideration (0x1803be960): state 0 -> 0, state 2-4 -> 1.0, state 1 with
   a meeting -> 1.0. Rank 5 beats work, orders, eating, sleeping and wages (all rank 4); only
   combat 6, high desire 7 (health <= 40 % with an instant-heal item), player direct move 8,
   fall 9 and script 10 beat it. Begin (0x1803be850): BT_TALK +
   `talk_system_start_or_join_conversation` (0x1801adbc0). End (0x1803be8f0): leave conversation.
4. **Join** (0x1801adbc0): with a place, join the conversation at it if participants < max;
   else create one (0x1801ae051): +2 place, +0x108 max (interact node count), +0x118 next-bubble
   time = 0, +0x120 bubbles said = 0, +0x128 bubble max = 2 + 3 x (rand % 6), and for the global
   place `2 x that + 10` (0x1801ae396), i.e. 14..44. `calc_positions` (0x1801b3870) gives each
   participant a free interact node and checks it against **his own query** (0x1801b40cd); an
   unreachable seat is cleared (BT_TALK then fails and he leaves). Positions of all participants
   are re-checked only when someone joins.
5. **Walk** (bt_talk_update 0x1804d1ac0, state 2 branch 0x1804d1e08): no talk position -> FAILURE
   (0x1804d1e4f). Otherwise: not moving and gp == seat -> `talk_system_start_talking` (0x1804d1eb0)
   and RUNNING; else `movement_system_move_to(seat)` (0x1804d212a) and RUNNING (0x1804d2137).
   **No timeout, no progress check, the move_to result is ignored.**
6. **Start** (talk_system_start_talking 0x1801ae3f0): state 3 (0x1801ae43b); the inlined
   `conversation::has_started` loop (0x1801ae51e..0x1801ae58d) checks that **every participant is
   in state 3**; only then `+0x118 = now + 1 s` (0x1801ae58f..0x1801ae5a1). This is the only
   place a conversation is started (all uses of +0x118: 0x1801ae08c zero at creation,
   0x1801ae5a1 start, 0x1801b42e4 next bubble, 0x1801b5f2b test).
7. **Session** (update loop 0x1801b5c40): `+0x120 < +0x128` and `+0x118 != 0 && <= now`
   (0x1801b5f2b `49 8b 85 18 01 00 00 48 85 c0 74 1d 48 3b c6 7f 18`) ->
   talk_system_update_conversation 0x1801b4200: bubbles++, next bubble in 1.0..3.0 s
   (0x1801b42b6), speaker picked among state-3 participants (none -> no bubble, safe). So a
   session lasts about 14..44 bubbles x 2 s = 30..90 s once everyone is seated.
8. **End**: bubbles >= max -> talk_system_resolve_conversation 0x1801b28c0: removes the GHMOD
   modifiers from the hall (0x1801b29fe), clears the global place (0x1801b2a23), reads
   KV_LATEST_HAMMERTING, `unlock_system_acquire_personal_unlock` (0x1801b2b4f: the law takes
   effect), adds HAMMERTING_SESSION_CONCLUDED (class HAMMERTING_HAMMERTING_TIMED: morale timer and
   the cooldown) to the game entity (0x1801b2c26), then relation changes between state-3
   participants (the "mass Nemesis after a meeting" PRE bug lives here). Back in the update every
   participant gets state 4 (0x1801b5f06) -> BT_TALK SUCCESS -> leaves.
9. **Cancel**: there is no command (command_hammerting.cpp has only hold) and no UI button.
   Only destroying the hall cancels it: talk_system_remove_destroyed_entities drops the
   conversations at the destroyed place and clears the global place (0x1801b0e0d, 0x1801b0ed6);
   no law, no cooldown.

## Why a stuck dwarf freezes the colony
- Wait condition: the meeting starts only when the **last participant to arrive** finds all
  participants seated (step 6). Nothing re-evaluates it later and there is no timeout.
- A participant who joined while his seat was reachable and then cannot finish the walk stays in
  state 2 forever: BT_TALK keeps returning RUNNING and re-issuing move_to (step 5). His seat is
  re-checked only if another dwarf joins, and nobody else is free to join (all are participants
  or the hall is full).
- If he leaves anyway (player direct move, fall, combat), `conversation::remove_participant`
  (0x1801baa30) just removes him; the global conversation is not removed when it empties
  (0x1801ae625) and has_started is not re-run, so the seated dwarves keep waiting until some
  other dwarf joins and arrives.
- Meanwhile every participant is in ACTION_TALK (rank 5) with work motivation 0: they stand at
  the hall (state 3, talk animation) or stand still on the way (state 2). They do not dig, build,
  haul, eat or sleep (rank 4), so nobody frees the stuck dwarf, and they starve faster under the
  in-session modifier. Only rank >= 6 actions interrupt them.
- Which "stuck" dwarves get in (gates verified, triggers inferred): the meeting drops the
  small-talk gates, so any dwarf whose current action is rank < 5 and whose "movement" query
  reaches the hall's first interact node is summoned: dwarves off the walk graph (gp on a climb
  edge or gamepath), on a vehicle, or CURRENTLY_IN_OVERWORLD with a query that reaches the
  mountain. A dwarf with no graph position gets an empty query (refresh_query 0x1800f42a0 sets
  0 start positions; inferred) and is not summoned. Most likely real trigger: the route is cut
  after he joined (digging, deconstruction, pit), or he can't physically follow a path his query
  reports.
- Reload does not help: talk_system saves only the component entity list and the global place
  (format_1 init_from_system 0x1801b9dd0), so after loading everyone is summoned again from
  scratch, stuck dwarf included if he still qualifies.
- Player workarounds (inferred): destroy the Great Hall; or direct-move the stuck dwarf out
  (rank 8), then direct-move one seated dwarf away and let him walk back (his arrival runs the
  start check).

## Fixes, ranked
**F1 (cave, recommended): start the Hammerting after a deadline.** When the global conversation
is created, also set its first-bubble time to now + T, so talk_system_update starts the session
at T even if not everyone is seated. start_talking still sets now + 1 s when the last dwarf
sits down earlier. Stragglers stay state 2 until the end, then get state 4 and are freed; the law
is acquired; bubbles come only from seated dwarves; 0 seated is safe. Normal chats are untouched.
- Site 0x1801ae396, old `48 8d 04 45 0a 00 00 00 49 89 86 28 01 00 00 eb 0e`
  (lea rax,[rax*2+0xa]; mov [r14+0x128],rax; jmp 0x1801ae3b5), new
  `e9 65 e1 45 00` + 12 x `90` (jmp 0x18060c500).
- Cave at .hmod+0x500 = 0x18060c500 (44 bytes, assembled with tools/cave.py, BASE 0x18060c500,
  RESUME 0x1801ae3b5, TIMEOUT 0x780000 = 120 s; 0xb40000 = 180 s):
  ```
  lea  rax, [2*rax + 0xa]          ; 48 8d 04 45 0a 00 00 00
  mov  [r14 + 0x128], rax          ; 49 89 86 28 01 00 00   (original: bubble max)
  mov  rax, [rdi + 0x60]           ; 48 8b 47 60            (talk data -> gamestate)
  mov  rax, [rax + 0xd0]           ; 48 8b 80 d0 00 00 00   (now)
  add  rax, TIMEOUT                ; 48 05 00 00 78 00
  mov  [r14 + 0x118], rax          ; 49 89 86 18 01 00 00
  jmp  0x1801ae3b5                 ; e9 89 1e ba ff
  ```
  rdi = talk data and r14 = the new conversation at the site (0x1801ae390 compares
  [rdi+0x68]); every volatile register is dead at 0x1801ae3b5 (epilogue).
**F2 (cave, optional, complements F1): summon only dwarves that small talk would accept.** In the
reset loop, with a meeting set, require a graph position, last edge WALK, last node types TILE
and not CURRENTLY_IN_OVERWORLD (the small-talk gates minus job availability, which would exclude
every worker). Keeps overworld, vehicle, climbing and gp-less dwarves out of the meeting; they
are re-tested every tick, so they join once they stand on the floor.
- Site 0x1801b61bd, old `48 8b 44 24 40 66 83 78 68 00 75 5a`, new `e9 7e 63 45 00` + 7 x `90`
  (jmp 0x18060c540).
- Cave at 0x18060c540 (77 bytes; SMALLTALK 0x1801b61c9, SKIP 0x1801b622d, OWCHECK 0x1801b6208):
  ```
  mov  rax, [rsp + 0x40]           ; talk data
  cmp  word ptr [rax + 0x68], 0
  jz   SMALLTALK                   ; no meeting: original small-talk gates (needs rax)
  mov  rdi, r14 ; mov rsi, r14 ; shl rdi, 6 ; add rdi, [rbp + 0x3428]   ; gp component
  cmp  dword ptr [rdi], 0      ; jz SKIP     ; no graph position
  cmp  byte ptr [rdi + 0x1a], 1; jnz SKIP    ; last edge WALK
  cmp  byte ptr [rdi + 0x18], 1; jnz SKIP    ; last node TILE
  cmp  byte ptr [rdi + 0x19], 1; ja SKIP
  jmp  OWCHECK                     ; overworld bit test, then state = 1 (0x1801b6223)
  ```
  bytes `48 8b 44 24 40 66 83 78 68 00 0f 84 79 9c ba ff 4c 89 f7 4c 89 f6 48 c1 e7 06 48 03 bd
  28 34 00 00 83 3f 00 0f 84 c3 9c ba ff 80 7f 1a 01 0f 85 b9 9c ba ff 80 7f 18 01 0f 85 af 9c
  ba ff 80 7f 19 01 0f 87 a5 9c ba ff e9 7b 9c ba ff`. rsi/rdi are restored at 0x1801b622d /
  0x1801b6237 as on the original paths.
No safe no-cave variant: NOPing the `je` at 0x1801b5f35 (`74 1d`) would update every unstarted
conversation each tick, and since update_conversation does `+0x118 += 1..3 s` from 0, every
chat and every Hammerting would burn through its bubbles in a few ticks.
Not proposed: lowering ACTION_TALK to rank 4 (0x1803be21e) does nothing for participants,
because work motivation is 0 for them anyway; removing that work block makes attendees drift
off while the rest wait. A start re-check on leave would make the direct-move workaround instant
but is unnecessary with F1.

## Testing
- Save while in session: `talk_system/data.bin` = talk entity list (u16) + global place (u16,
  the hall's entity; 0 when no meeting). Participants, states and conversations are not saved.
  `key_value_system`: KV_LATEST_HAMMERTING (wc_hash 0x39992be1c34c7f82, type 0x10003, value =
  wc_hash of the record name) on the game entity. Modifiers: HAMMERTING_HOUSE_IN_SESSION
  (0x94f43e915e61c5a5, class GHMOD 0xc4e779096ede26e7) on the hall during the session;
  HAMMERTING_SESSION_CONCLUDED (0xdd83b277f753c68e, class TIMED 0xd097ef2f7e646fc4) on the game
  entity afterwards, plus the law in unlock_system.
  Talk debug lines ("Conversation %hu created between...", "started talking", "ended",
  channel GAMESTATE-TALK) are gated by a debug flag ([0x1805a77f0]+0xe) and probably not logged.
- Start one: Great Hall -> Hammerting tab -> select an affordable law -> Hold Hammerting. Needs no
  cooldown modifier and no session running.
- Repro (vanilla): call it; after a second or two every eligible dwarf has joined (state 2). Then
  cut one far dwarf's route ahead of him (deconstruct a ladder or stair section he still has to
  use, not the tile he stands on, which re-snaps and pre-empts him). Expect: the others sit
  in the hall, no speech bubbles, "Great Hall in Session" never ends, nobody works. If a later
  joiner appears, the cut-off dwarf's seat is re-checked and dropped, which can unstick it; the
  repro is cleanest when everyone joined before the cut.
- With F1: the session starts at most T after the call, runs 30..90 s, ends with "Session
  Concluded", the law applied, the cut-off dwarf released; the colony can then reach him.
  With F2: a dwarf on a ladder or in the overworld at the call stays at work until he is back on
  the floor.
- Save edit (checks the reachability gate, not the hang): move a dwarf into a sealed pocket in
  `fixed_transform_system/data.bin`. Format (fixed_transform_system_format_1 writer
  0x1800efb30; inferred from the code, not yet checked on a save): five arrays, each
  `u64 count, u64 bytes, data`, indexed by entity id: local positions vec3, local directions i8,
  world positions vec3, world directions i8, rotations vec3. vec3 = 3 x i32 16.16 (x, y, z). For a
  dwarf (family root) set local and world to (tile.x + 0.5, floor y, same z). On load the gp is
  re-snapped from it (stuck_dwarves.md). Vanilla: he is not summoned and the meeting runs without
  him.
- Back up the save folder first (CLAUDE.md); autosaves overwrite `autosave_<Colony>_*`.

## Ordinary chats: the partner left behind (Nov 2026, `mods/chat_partner_release`)
`talk_system_leave_conversation` (0x1801ae5c0): leaver state 0, `conversation::remove_participant`
(0x1801baa30, returns participants left <= 1), then `talk_system::remove_conversation` (0x1801ba950, frees
everyone left: state 0, conversation 0) unless the conversation's place equals the Hammerting place
(0x1801ae625). That place is 0 with no Hammerting, and chats between nearby dwarves have place 0 too (seen in
memory: every chat in KrazJomsglind had place 0 except one at a place 2080), so an abandoned chat is kept. If its
other dwarf was already seated, has_started never runs again: he stays in ACTION_TALK, state 3, until someone else
joins. bt_talk_update returns 3 running, 2 failure, 1 success; states 0/1 fail. The mod removes such chats when no
Hammerting is set and re-runs the all-seated check when a kept chat has not started (inline participants only, up
to 8). `mods/_test_talk_leave` (test only) fails BT_TALK for odd entity ids at their seat; the scanner used was a
scratch script reading talk data (components [+0] 0x50 each, count +8, conversations +0x40, 0x1338 each).

## Relations after a meeting (2026-11-08, BUGS B15 "Mass Nemesis relations after a meeting")
- Reproduced in the user's colony: the user held a Hammerting (`hold_hammerting`, session 2026-11-06 11:19, at 01:26:18,
  about 14 minutes before savegame29). RELATION_DWARF states per side (relation_system/data.bin, 56-byte records {u16 e1,
  u16 e2, u64 2, u64 4, u16 s1, u16 s2, u64 2, u64 16, u64 t1, u64 t2}, tags SPITEFUL COLD NEUTRAL FRIENDS LOVING):
  savegame28 0/0/62/9/1, savegame29 35/17/18/2/0. Values (key_value RELATION_DWARF_<id>, 0..1000): every one of the 72
  changed, median -240, 21 at 0. Other save intervals: median change 0 (only pairs that chatted), single pairs up to -875.
  Still 24 SPITEFUL in savegame32.
- talk_system_resolve_conversation 0x1801b28c0: for every seated participant A and every other seated B, rel =
  relation_component_system_get_relation(A, B) (+0x18 i32), range = 3 * (tone + 2 * rel), delta = PCG random in
  [0, range) or (range, 0], then relation_component_system_change_relation(A, B, delta) (call 0x1801b2ed9). The tone is
  conversation +0x110. Afterwards morale/energy change by 3 * (tone + 2 * average rel).
- talk_system_update_conversation 0x1801b4200: each talk turn adds r10 to the tone if the topic tag is in the list at
  [rsp+0x58] and subtracts it otherwise (0x1801b52d3 / 0x1801b5369); r10 is doubled on a 1-in-5 roll and tripled on a
  1-in-3 roll. Nothing clamps the tone or scales it by the number of participants, so a meeting applies one accumulated
  tone to every pair at once. [V for the code; I that long meetings drift negative because most topics miss the list]
- Not measured: the tone of a meeting against an ordinary chat, what +0x18 of the relation holds.
- Fix: `mods/meeting_tone_scale` (`.hmod` 0x80, whole_batch_inputs shrunk to 0x00-0x80; it uses 0x4c) replaces the 13-byte tone
  load at 0x1801b2d75 with a cave that divides the tone by (participants - 1) when there are more than 2 (idiv, rel kept in
  r9d; r9 and r11 are rewritten before their next use). The morale/energy step at 0x1801b2f22 still reads the raw tone.
  Test: copy of savegame32, `_test_quiet`, key 3, about 11 minutes, `HMOD_TONE_DIAG=1`: one 3-dwarf chat, 6 pairs scaled,
  tone -246 to -123; Spiteful 24 to 22, Friends 21 to 27 over the run; two-dwarf chats still moved single values by -653
  to +826 (vanilla). No meeting held (ACHIEVEMENT_HOUSE_IN_SESSION may be tied to Hammertings).
