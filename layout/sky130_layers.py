"""Sky130A GDS layer / datatype map (open_pdks / magic sky130A)."""

# (layer, datatype)
LAYERS = {
    "nwell": (64, 20),
    "diff": (65, 20),
    "tap": (65, 44),
    "poly": (66, 20),
    "licon1": (66, 44),
    "li1": (67, 20),
    "mcon": (67, 44),
    "met1": (68, 20),
    "via": (68, 44),
    "met2": (69, 20),
    "via2": (69, 44),
    "met3": (70, 20),
    "via3": (70, 44),
    "met4": (71, 20),
    "met4.pin": (71, 16),
    "met4.label": (71, 5),
    "via4": (71, 44),
    "met5": (72, 20),
    "pad": (76, 20),
    "npc": (95, 20),  # nitride poly cut (hi-R poly)
    "capm": (89, 44),  # MIM
    "prb": (235, 4),  # prBoundary
    "areaid_sc": (81, 4),
    "text": (83, 44),
    "hvntm": (125, 20),
}

# Min width um (approx sky130A, for the DRC report)
MIN_WIDTH = {
    "poly": 0.15,
    "diff": 0.15,
    "li1": 0.17,
    "met1": 0.14,
    "met2": 0.14,
    "met3": 0.30,
    "met4": 0.30,
    "met5": 1.60,
    "nwell": 0.84,
}
