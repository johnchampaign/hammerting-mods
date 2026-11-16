# Translations

Hammerting has ten languages. English texts are spread over several tables
(`localization/core.loc`, `cave.loc`, ...), and each other language has one table with every key
(`imported_de_de.loc` and so on). A key missing from the player's language shows as the key itself,
with no fallback to English.

So when `tools/hmod.py` installs, it copies every text the mods add or change in the English tables
into the other nine tables, translated by the file for that language here, and in English where the
file has no entry. The Mods window and the news section are built in the language the game has at
install time (from the game's `settings.txt`, or Steam's language for the game when the game is set
to Default; `HMOD_LANGUAGE=de-DE` overrides it).

Each file is a JSON object from the English text, exactly as the mod writes it, to the translation:

    de-DE.json  es-ES.json  fr-FR.json  it-IT.json  ja-JP.json
    pl-PL.json  pt-BR.json  ru-RU.json  zh-CN.json

A translation must keep, in the same order, every `%Oproperty_comp` (the game fills each with a live
value), every colour tag (`|YELLOW|` ... `|!|`), every icon code (`:building_large_vault:`) and every
`{placeholder}`, and the same line breaks. The installer falls back to English for a translation
with the wrong number of `%Oproperty_comp`.

The current translations were made with an AI model, using the game's own translations for its
terms. Corrections from native speakers are welcome.

## Adding texts

After changing a mod's text or adding a mod, run

    python tools/hmod.py strings recommended stairs_timeout eat_reserved_food lava_burn

It writes `build/strings.json`: every text some language lacks, with the game's own translations of
the text it replaced, if any. The install output also says how many texts are shown in English for
lack of a translation.
