# Draft code cave for a plant-repair mod (see re/notes/plant_growth.md, tools/cave.py for the
# conventions). Not installed by any mod. Symbols: BASE = 0x18060c400 (.hmod + 0x400),
# DB_PLANT = 0x18007b760 internal_database_get_container<plant_record>(database*),
# GET_QUEUE = 0x18014e5d0 production_system_get_queue(ecs, producer, uid),
# SET_STAGE = 0x1801f37c0 plant_system::set_stage(ps, plant_data*, u16 stage).

        .intel_syntax noprefix
        .text
start:

# repair: replaces `call SET_STAGE` at 0x1801eb193 in the plant system's
# EP_LOAD_POST_SINGLETHREADED pass, which calls set_stage(ps, p, p->stage) for every plant.
# With an unchanged stage set_stage only refreshes the harvest flag, so a plant at a tender
# stage (sow, water, lava) whose production entry is gone stays stuck. Here, if the stage's
# first tender advances the plant (on_complete == PLANT_ADVANCE_STAGE) and the plant entity
# has no queue entry, p->stage is set to 0xffff so set_stage takes its full path and starts
# the tender production again. A plant at a timed stage whose timer is unset (0xffffffff, e.g.
# after a data patch turned a tender stage into a timed one) is forced the same way, which
# draws a new timer. Otherwise the call is unchanged.
# In: rcx = plant_system, rdx = plant_data (0x38 B), r8w = stage. The caller keeps rbx, rsi,
# rdi live; they are saved here. set_stage is reached by a tail jump.
repair:
        push    rbx
        push    rsi
        push    rdi
        sub     rsp, 0x20
        mov     rsi, rcx                        # plant_system
        mov     rbx, rdx                        # plant_data
        movzx   edi, r8w                        # stage
        mov     rax, qword ptr [rsi + 0x10]     # gamestate
        mov     rcx, qword ptr [rax + 0x20]     # database
        .byte   0xe8
        .long   DB_PLANT - BASE - (1f - start)
1:      mov     rax, qword ptr [rax + 0x50]
        movzx   ecx, word ptr [rbx + 6]         # plant type index
        mov     rax, qword ptr [rax + 8*rcx]    # plant_record
        imul    rcx, rdi, 0x178
        add     rax, rcx                        # + stage * sizeof(plant_stage)
        cmp     qword ptr [rax + 0x198], 0      # _stages[s]._tender[0]._recipe._hash
        je      timed
        cmp     dword ptr [rax + 0x1a0], 1      # _tender[0]._on_complete == ADVANCE
        jne     plain
        mov     rax, qword ptr [rsi + 0x10]
        mov     rcx, qword ptr [rax + 0x28]     # mainstate
        add     rcx, 0x1e08                     # production ecs
        movzx   edx, word ptr [rbx + 2]         # plant entity
        xor     r8d, r8d                        # uid 0 = first entry
        .byte   0xe8
        .long   GET_QUEUE - BASE - (2f - start)
2:      test    rax, rax
        jne     plain
force:
        mov     word ptr [rbx + 4], 0xffff      # force the full path
        jmp     plain
timed:
        cmp     dword ptr [rax + 0x108], 0      # _stages[s]._min_time_in_stage
        je      plain
        cmp     dword ptr [rbx + 8], -1         # p->next_time unset
        je      force
plain:
        mov     rcx, rsi
        mov     rdx, rbx
        mov     r8d, edi
        add     rsp, 0x20
        pop     rdi
        pop     rsi
        pop     rbx
        .byte   0xe9
        .long   SET_STAGE - BASE - (3f - start)
3:
end:
