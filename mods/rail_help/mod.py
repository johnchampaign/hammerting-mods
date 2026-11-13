"""Rail Help: the rail tooltips and help pages say what actually carries dwarves.

The help pages tell players to build "a Cart to ride in", but a Cart never carries dwarves: only
the Handcar does (only the CART_PASSENGER tag counts, station_system 0x18035e3b9). With no Handcar
on a line dwarves ignore it, and in a test a rail piece further along a shaft stayed unreachable
until one was added. The Elevator Platform in the texts can't be built at all (its recipe depends
on BUILDING_NONE). So "my elevator doesn't work" reports read like a bug (BUGS A14). This only
changes text. See re/notes/carts_elevators.md.
"""

DESCRIPTION = "Rail tooltips and help say that only Handcars carry dwarves and builders need one"

TEXT = {
    'items': {
        'Handcars transport dwarves between two Railway Stations, connected by Railway.':
            'Handcars are the only vehicle dwarves can ride, on Railway and on Elevator Rail. Keep one on '
            'every line: without it dwarves ignore the line, and builders may not reach rail further along it.',
        'Carts transport goods between two points along a Railway.':
            'Carts carry goods along a line by themselves, between inventories next to the rail. Dwarves '
            "can't ride them: build a Handcar for that.",
        'Rail Stations are the beginning and end points for rail lines, where Carts can switch between '
        'traveling along horizontal Railways, and vertical Elevator Rails.':
            'Rail Stations are the beginning and end points for rail lines, and the only place where Railway '
            'and Elevator Rail connect. Dwarves get on and off here. A line needs a Handcar before they can '
            'ride it.',
        'Elevator Rail lines form paths along which Carts can move between two Elevator Stations.':
            'Elevator Rail lines form vertical paths between two Rail Stations. No platform is needed or '
            'available: dwarves ride a Handcar placed on the line.',
        'Railway lines form paths along which Carts can move between two Railway Stations.':
            'Railway lines form paths between two Rail Stations. Dwarves ride Handcars along them, and Carts '
            'carry goods.',
    },
    'core': {
        'For the Patrician colony, and with the research of new Knowledge, there are eventually also '
        'Railways available. Construct Rails, a Station, and a Mine Cart, and the Dwarves will automatically '
        'use the Railway to travel.':
            'For the Patrician colony, and with the research of new Knowledge, there are eventually also '
            'Railways available. Construct Rails, a Station, and a Handcar, and the Dwarves will automatically '
            'use the Railway to travel.',
        "A second Station to serve as a destination, and a Cart to ride in, completes the picture, and makes "
        "for a functional Rail system. Carts can also be found under the 'Infrastructure' tab of the Action Menu.":
            "A second Station to serve as a destination, and a Handcar to ride in, completes the picture, and "
            "makes for a functional Rail system. Handcars are found under the 'Infrastructure' tab of the Action "
            "Menu, next to Carts, which carry only goods.",
        "As your Colony discovers new Knowledge, specifically the Knowledge of 'Machinery', new means of "
        "transportation become available to it in the form of Mine Carts. Cart systems are constructed using "
        "the component parts Station, Rail, and Cart. Begin the construction of a new system by placing a Rail "
        "Station from the 'Infrastructure' tab of the Action Menu.":
            "As your Colony discovers new Knowledge, specifically the Knowledge of 'Machinery', new means of "
            "transportation become available to it in the form of Mine Carts. Rail systems are constructed using "
            "the component parts Station, Rail, and Handcar. Begin the construction of a new system by placing a "
            "Rail Station from the 'Infrastructure' tab of the Action Menu.",
    },
}


def apply(ctx):
    for name, texts in TEXT.items():
        table = ctx.loc(name)
        found = set()
        for entry in table.entries.values():
            if entry.text in texts and not entry.blobs:
                found.add(entry.text)
                entry.text = texts[entry.text]
        assert found == set(texts), set(texts) - found
