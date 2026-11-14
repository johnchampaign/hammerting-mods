# Code cave for harvest_priority, in the .hmod section (see tools/cave.py for the convention).

        .intel_syntax noprefix
        .text
start:

# prio: replaces `mov r8d,[rdi+0x1c]; mov r9,r15` at 0x1801ea91f in
# plant_system_update_workplace_positions, which hands a crop type's harvest job its priority
# (type entry +0x1c, from plant_system::update_harvesting) and ripe positions (r15). That
# priority starts at Low and is only raised by a Cave Farm entry for the crop, to the Cave Farm's
# hauling priority, so a dwarf with any Normal job never picked a harvest. Now it is at least
# HARVEST_PRIO.
prio:
        mov     r8d, [rdi+0x1c]
        cmp     r8d, HARVEST_PRIO
        jae     1f
        mov     r8d, HARVEST_PRIO
1:
        mov     r9, r15
        .byte   0xe9                            # pass them to update_harvest_jobs
        .long   BACK - BASE - (2f - start)
2:
end:
