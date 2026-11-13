"""Relation Crash Guard: relation_component_system_change_relation no longer crashes on
missing data.

The function (entity.x86_64.dll) changes the opinion of one entity of another: it looks up
their relation of a given type, reads the owner's opinion key-value, adds to it, steps the
relation state and writes the opinion back. It checks nothing, so it reads through NULL
when the pair has no relation of that type (0x18007eac0) or the opinion key-value is
missing (0x18007eba9). Joining an alliance (the Dwarven Licorice / Elves quest) changes the
opinion of every related faction pair without checking the pairs exist, and the opinion
tick runs over every faction pair after each load, which fits "crashes on completion" (BUGS
A4) and "crashes again after every reload" (A3). See re/notes/relation_crash.md.

Both patches are in place:
- No relation of that type: return without changing anything.
- No usable opinion value: start from 0; the write at the end recreates the key-value.
"""
DESCRIPTION = "Opinion changes between entities without a relation no longer crash (entity DLL patch)"

# 0x18007ea87: test rax,rax; je L_null (short) ... L_null: xor ebx,ebx; xor edi,edi
NULL_RELATION_OLD = bytes.fromhex(
    '4885c0' '7417' '488bd8' '66413bf4' '7204' '488d5828' '488d7828' '480f47f8' 'eb04' '33db' '33ff')
NULL_RELATION_NEW = bytes.fromhex(
    '4885c0' '0f84f5030000'      # je 0x18007ee85, the function's epilogue
    '488bd8' '66413bf4' '7204' '488d5828' '488d7828' '480f47f8'
    '6690')

# 0x18007eb74: pick the opinion value from the key-value result at [rsp+0x40]
# ({u16 type, u16 count, u32, value or pointer @+8}); anything but an i64 left rcx = NULL.
OPINION_OLD = bytes.fromhex(
    '66837c244004' '752b' '837c244400' '7524' '0fb7442442' '6685c0' '741a' '6683f801'
    '488d4c2448' '480f454c2448' 'eb0b'
    '4c894577' '4c8be9' 'ebcd'            # 0x18007eb9e, a loop exit that jumps back here: kept
    '33c9')
OPINION_NEW = bytes.fromhex(
    '488d4c2448'                          # rcx = &value (zeroed before the lookup)
    '66837c244004' '7528'                 # type != i64        -> use &value
    '837c244400' '7521'
    '66837c244201' '7619'                 # count <= 1          -> use &value
    '488b4c2448' 'eb12'                   # count > 1: value holds a pointer to the values
    '0f1f8000000000'
    '4c894577' '4c8be9' 'ebcd'
    '6690')


def apply(ctx):
    ctx.patch_dll(0x18007ea87, NULL_RELATION_OLD, NULL_RELATION_NEW,
                  'change_relation: return when the pair has no relation', dll='entity')
    ctx.patch_dll(0x18007eb74, OPINION_OLD, OPINION_NEW,
                  'change_relation: missing opinion key-value counts as 0', dll='entity')
