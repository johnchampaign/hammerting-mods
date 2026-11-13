# Code cave for harvest_wild_crops, in the .hmod section (see tools/cave.py for the convention).

        .intel_syntax noprefix
        .text
start:

# check: replaces `cmp byte ptr [rcx+0x30],0; je skip` at 0x1801ea3cd in
# plant_system_update_workplace_positions, the loop that hands every harvestable plant of a crop
# type to the harvest sensor as a job. rcx = plant_data, r14 = plant_system. The game skipped
# plants without auto_tend (+0x30): every wild plant, so each ripe one waited for a Harvest order.
# Now a wild plant also gets a job, if its tile is explored (map bit 22, as eating checks), so
# farmers don't walk into unexplored cave for it. Harvesting still removes a wild plant
# (plant_system_harvest reads auto_tend for that), as the manual order did.
check:
        cmp     byte ptr [rcx+0x30], 0
        jne     keep                            # sown crop: as before
        push    rax
        push    rdx
        push    r10
        push    r11
        mov     r10, [r14+0x10]                 # gamestate
        mov     r10, [r10+0x40]                 # map: cells +8, width in 16-tile blocks +0x30
        mov     eax, [rcx+0x10]                 # tile x
        mov     r11d, [rcx+0x14]                # tile y (stored as y - 1, the soil under it)
        mov     edx, r11d
        shr     edx, 4
        imul    edx, [r10+0x30]
        push    rax
        shr     eax, 4
        add     edx, eax                        # block index
        pop     rax
        shl     edx, 4
        and     r11d, 15
        add     edx, r11d
        shl     edx, 4
        and     eax, 15
        add     edx, eax                        # cell index
        mov     rax, [r10+8]
        mov     eax, [rax+rdx*4]
        bt      eax, 22                         # explored
        pop     r11
        pop     r10
        pop     rdx
        pop     rax
        jc      keep
        .byte   0xe9                            # skip this plant
        .long   SKIP - BASE - (1f - start)
1:
keep:
        .byte   0xe9                            # check its workplace and add the job
        .long   KEEP - BASE - (2f - start)
2:
end:
