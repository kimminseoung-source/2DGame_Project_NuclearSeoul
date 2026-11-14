"""Backpack slots and the inventory overlay."""

import pico2d


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
            self.message = "빈 슬롯입니다."
        else:
            self.message = "아직 사용할 수 없는 물건입니다."


def draw_inventory(inventory, font, width, height):
    x, y = width // 2 - 245, height // 2 - 151
    pale = (203, 219, 228)
    gold = (250, 219, 146)
    pico2d.draw_rectangle(x, y, x + 490, y + 302, 15, 23, 31, filled=True)
    pico2d.draw_rectangle(x, y, x + 490, y + 302, 100, 132, 132)
    font.draw(x + 20, y + 277, "배낭", pale)
    font.draw(x + 292, y + 277, "장착 무기  야구 방망이", pale)
    for index, slot in enumerate(inventory.slots):
        row, col = divmod(index, COLUMNS)
        left = x + 20 + col * 114
        bottom = y + 180 - row * 72
        border = gold if index == inventory.selected else (76, 98, 108)
        pico2d.draw_rectangle(left, bottom, left + 108, bottom + 64, 33, 46, 56, filled=True)
        pico2d.draw_rectangle(left, bottom, left + 108, bottom + 64, *border)
        if slot:
            item, count = slot
            font.draw(left + 64, bottom + 38, f"{count}개", gold)
            font.draw(left + 6, bottom + 12, item, pale)
        else:
            font.draw(left + 28, bottom + 26, "빈 슬롯", (130, 151, 163))
    if inventory.slots[inventory.selected]:
        font.draw(x + 20, y + 81, inventory.slots[inventory.selected][0], pale)
    else:
        font.draw(x + 20, y + 81, "이 슬롯에는 아이템이 없습니다.", pale)
    font.draw(x + 20, y + 54, inventory.message, gold)
    font.draw(x + 20, y + 22, "방향키 선택   Enter 사용   Tab / Esc 닫기", pale)
