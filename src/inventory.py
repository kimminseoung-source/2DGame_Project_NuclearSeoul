"""Backpack slots and the inventory overlay."""

import pico2d

from item_ui import draw_filter_icon


SPARE_FILTER = "Spare filter"
SLOT_COUNT = 8
COLUMNS = 4


class Inventory:
    def __init__(self):
        self.slots = [None] * SLOT_COUNT
        self.selected = 0
        self.message = ""

    def count(self, item):
        return sum(quantity for name, quantity in filter(None, self.slots) if name == item)

    def add(self, item):
        empty = None
        for index, slot in enumerate(self.slots):
            if slot is None:
                if empty is None:
                    empty = index
            elif slot[0] == item:
                self.slots[index] = item, slot[1] + 1
                return True
        if empty is None:
            return False
        self.slots[empty] = item, 1
        return True

    def select(self, offset):
        self.selected = (self.selected + offset) % SLOT_COUNT
        self.message = ""

    def use_selected(self):
        if self.slots[self.selected] is None:
            self.message = "This slot is empty."
        else:
            self.message = "Filter replacement is not available yet."


def draw_inventory(inventory, font, width, height):
    x, y = width // 2 - 245, height // 2 - 151
    pale = (203, 219, 228)
    gold = (250, 219, 146)
    pico2d.draw_rectangle(x, y, x + 490, y + 302, 15, 23, 31, filled=True)
    pico2d.draw_rectangle(x, y, x + 490, y + 302, 100, 132, 132)
    font.draw(x + 20, y + 277, "BACKPACK", pale)
    font.draw(x + 292, y + 277, "Weapon: Baseball bat", pale)
    for index, slot in enumerate(inventory.slots):
        row, col = divmod(index, COLUMNS)
        left = x + 20 + col * 114
        bottom = y + 180 - row * 72
        border = gold if index == inventory.selected else (76, 98, 108)
        pico2d.draw_rectangle(left, bottom, left + 108, bottom + 64, 33, 46, 56, filled=True)
        pico2d.draw_rectangle(left, bottom, left + 108, bottom + 64, *border)
        if slot:
            item, count = slot
            draw_filter_icon(left + 23, bottom + 41)
            font.draw(left + 64, bottom + 38, f"x{count}", gold)
            font.draw(left + 6, bottom + 12, "Filter" if item == SPARE_FILTER else item, pale)
        else:
            font.draw(left + 28, bottom + 26, "Empty", (130, 151, 163))
    if inventory.slots[inventory.selected]:
        font.draw(x + 20, y + 81, "Spare filter for your gas mask.", pale)
    else:
        font.draw(x + 20, y + 81, "No item in this slot.", pale)
    font.draw(x + 20, y + 54, inventory.message, gold)
    font.draw(x + 20, y + 22, "Arrows Select   Enter Use   Tab / Esc Close", pale)
