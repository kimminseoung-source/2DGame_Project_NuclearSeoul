"""Exploration-mode screen objects: the top strip, the bottom bar and pop-up windows."""

import pico2d

import ui
from inventory import SPARE_FILTER, draw_inventory
from item_ui import draw_filter_slot
from tile_map import HEIGHT, WIDTH


class ExplorationHud:
    """Top strip: current message, health and spare filters."""

    def __init__(self, state):
        self.state = state

    def update(self):
        pass

    def draw(self):
        state = self.state
        pico2d.draw_rectangle(0, HEIGHT, WIDTH - 1, HEIGHT + 63, 15, 23, 31, filled=True)
        color = (133, 231, 184) if state.finished else (245, 222, 169)
        ui.text(16, HEIGHT + 32, state.message, color)
        ui.text(500, HEIGHT + 18, f"체력 {state.health}/{state.max_health}", (238, 169, 149))
        draw_filter_slot(WIDTH - 162, HEIGHT + 8, state.inventory.count(SPARE_FILTER), ui.font(16))


class ExplorationBar:
    """Bottom strip outside combat: round portrait, health and controls."""

    def __init__(self, state, player):
        self.state = state
        self.player = player

    def update(self):
        pass

    def draw(self):
        ui.panel(0, 0, WIDTH - 1, ui.BOTTOM_HEIGHT - 1, ui.BORDER, ui.PANEL, 255)
        pico2d.draw_line(0, ui.BOTTOM_HEIGHT - 2, WIDTH, ui.BOTTOM_HEIGHT - 2, 120, 98, 60)
        x, y, radius = 58, 52, 44
        pico2d.draw_circle(x, y, radius, 24, 32, 40, filled=True)
        image, sx, sy, sw, sh = self.player.portrait_clip()
        scale = radius * 1.35 / max(sw, sh)
        image.clip_draw(sx, sy, sw, sh, x, y + 6, sw * scale, sh * scale)
        ui.ring(x, y, radius, ui.PARTY, 3)
        ui.ring(x, y, radius + 3, (120, 98, 60), 1)
        label = f"{self.state.health}/{self.state.max_health}"
        width = ui.text_width(label, 14) + 12
        ui.panel(x - width / 2, y - radius - 2, x + width / 2, y - radius + 16, ui.PARTY)
        ui.text_center(x, y - radius + 7, label, ui.TEXT, 14)
        ui.text(124, 70, "WASD 이동   Shift 은신   E 상호작용   Space 대시", ui.MUTED, 14)
        ui.text(124, 44, "좌클릭 공격 · 들키기 전에 가까이서 좌클릭하면 기습", ui.MUTED, 14)
        ui.text(124, 18, "Tab 배낭   F1 설정   Esc 종료", ui.DIM, 14)


class InventoryOverlay:
    """Backpack window, shown while Tab is toggled on."""

    def __init__(self, state):
        self.state = state

    def update(self):
        pass

    def draw(self):
        if self.state.inventory_open and not self.state.settings_open:
            draw_inventory(self.state.inventory, ui.font(16), WIDTH, HEIGHT)


class SettingsOverlay:
    """F1 settings window for the walking speed."""

    def __init__(self, state):
        self.state = state

    def update(self):
        pass

    def draw(self):
        if not self.state.settings_open:
            return
        left, bottom = WIDTH // 2 - 176, HEIGHT // 2 - 66
        pico2d.draw_rectangle(left, bottom, left + 352, bottom + 132, 15, 23, 31, filled=True)
        pico2d.draw_rectangle(left, bottom, left + 352, bottom + 132, 135, 170, 157)
        ui.text(left + 22, bottom + 103, "설정", (181, 197, 209))
        ui.text(left + 22, bottom + 70, f"이동 속도   < {self.state.speed_percent}% >", (252, 218, 143))
        ui.text(left + 22, bottom + 42, "좌우 방향키 조절   R 초기화", (181, 197, 209))
        ui.text(left + 22, bottom + 18, "F1 / Esc 계속하기", (181, 197, 209))
