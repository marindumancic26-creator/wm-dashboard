"""Offizielle WM-2026-K.o.-Bracket-Struktur (48 Teams, 32er-K.o.).

Quelle: FIFA-Spielplan / Wikipedia „2026 FIFA World Cup knockout stage".
Slots: ("W", "A")=Gruppensieger A, ("RU","B")=Gruppenzweiter B,
       ("3", [Gruppen])=bester Dritter aus einer der gelisteten Gruppen.
Die 8 qualifizierten Dritten werden den 8 Dritten-Slots zugeordnet (Bipartite-
Matching, das die Gruppen-Eligibility respektiert — FIFAs 495er-Tabelle picks eine
deterministische gültige Zuordnung; unsere respektiert dieselben Constraints).
"""
from __future__ import annotations

# (match_id, slot1, slot2)
R32 = [
    (73, ("RU", "A"), ("RU", "B")),
    (74, ("W", "E"),  ("3", ["A", "B", "C", "D", "F"])),
    (75, ("W", "F"),  ("RU", "C")),
    (76, ("W", "C"),  ("RU", "F")),
    (77, ("W", "I"),  ("3", ["C", "D", "F", "G", "H"])),
    (78, ("RU", "E"), ("RU", "I")),
    (79, ("W", "A"),  ("3", ["C", "E", "F", "H", "I"])),
    (80, ("W", "L"),  ("3", ["E", "H", "I", "J", "K"])),
    (81, ("W", "D"),  ("3", ["B", "E", "F", "I", "J"])),
    (82, ("W", "G"),  ("3", ["A", "E", "H", "I", "J"])),
    (83, ("RU", "K"), ("RU", "L")),
    (84, ("W", "H"),  ("RU", "J")),
    (85, ("W", "B"),  ("3", ["E", "F", "G", "I", "J"])),
    (86, ("W", "J"),  ("RU", "H")),
    (87, ("W", "K"),  ("3", ["D", "E", "I", "J", "L"])),
    (88, ("RU", "D"), ("RU", "G")),
]

# K.o.-Baum: Match -> (Feeder-Match-1, Feeder-Match-2)
R16 = {89: (74, 77), 90: (73, 75), 91: (76, 78), 92: (79, 80),
       93: (83, 84), 94: (81, 82), 95: (86, 88), 96: (85, 87)}
QF = {97: (89, 90), 98: (93, 94), 99: (91, 92), 100: (95, 96)}
SF = {101: (97, 98), 102: (99, 100)}
FINAL = {104: (101, 102)}

ROUND_ORDER = ["R32", "R16", "QF", "SF", "FINAL", "CHAMPION"]

# Dritten-Slots: Match-ID -> eligible Gruppen
THIRD_SLOTS = {m: s2[1] for (m, s1, s2) in R32 if s2[0] == "3"}


def _kuhn_match(slots: dict, available_groups: set) -> dict:
    """Bipartite-Matching: Dritten-Slot (Match) <- Gruppe (deren 3. qualifiziert ist),
    Gruppe muss in der Eligible-Liste des Slots sein. Rückgabe {match_id: group}."""
    slot_ids = list(slots)
    match_to_group: dict[int, str] = {}
    group_to_slot: dict[str, int] = {}

    def try_assign(mid, seen):
        for g in slots[mid]:
            if g in available_groups and g not in seen:
                seen.add(g)
                if g not in group_to_slot or try_assign(group_to_slot[g], seen):
                    match_to_group[mid] = g
                    group_to_slot[g] = mid
                    return True
        return False

    for mid in slot_ids:
        try_assign(mid, set())
    return match_to_group
