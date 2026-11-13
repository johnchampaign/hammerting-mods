# Test only: counts loot items in default_production_complete_cbck that pass or fail the item check.
        .intel_syntax noprefix
        .text
start:
# hook: replaces `call inventory_system_has_item_comp` at 0x1802d95a1.
hook:
        .byte   0xe8
        .long   HAS_ITEM - BASE - (1f - start)
1:      test    al, al
        jz      2f
        .byte   0xff, 0x05                      # inc dword ptr [rip + passed]
        .long   passed - 3f
3:      jmp     4f
2:      .byte   0xff, 0x05                      # inc dword ptr [rip + failed]
        .long   failed - 4f
4:      .byte   0xe9
        .long   RESUME - BASE - (5f - start)
5:
        .p2align 3
passed: .long   0
failed: .long   0
end:
