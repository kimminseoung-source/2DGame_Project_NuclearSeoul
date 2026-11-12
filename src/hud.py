"""Exploration-mode screen objects: the top strip, the bottom bar and pop-up windows."""

import pico2d

import ui
from inventory import draw_inventory
from tile_map import HEIGHT, WIDTH


class ExplorationHud:
    """Top strip: current message and health."""

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
        ui.text(124, 70, "WASD 이동   Shift 은신   E 상호작용   Space 대시(누르고 있으면 뛰기)", ui.MUTED, 14)
        ui.text(124, 44, "좌클릭 마체테(연타 3번) · ! 뜨면 Space(직전이면 반격) · 들키기 전 공격은 기습", ui.MUTED, 14)
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
    """F1 settings window: walking speed and whether the hit wheel spins."""

    WIDTH, HEIGHT = 392, 176

    def __init__(self, state):
        self.state = state

    def update(self):
        pass

    def rows(self):
        spin = "건너뛰기 (결과만)" if self.state.skip_spin else "보기"
        return [("이동 속도", f"< {self.state.speed_percent}% >"),
                ("명중 돌림판", f"< {spin} >")]

    def draw(self):
        if not self.state.settings_open:
            return
        left, bottom = WIDTH // 2 - self.WIDTH // 2, HEIGHT // 2 - self.HEIGHT // 2
        right, top = left + self.WIDTH, bottom + self.HEIGHT
        pico2d.draw_rectangle(left, bottom, right, top, 15, 23, 31, filled=True)
        pico2d.draw_rectangle(left, bottom, right, top, 135, 170, 157)
        ui.text(left + 22, top - 24, "설정", (181, 197, 209))
        for index, (name, value) in enumerate(self.rows()):
            y = top - 62 - index * 32
            selected = index == self.state.settings_row
            if selected:
                pico2d.draw_rectangle(left + 12, y - 13, right - 12, y + 13, 40, 52, 62, filled=True)
            color = (252, 218, 143) if selected else (181, 197, 209)
            ui.text(left + 22, y, name, color)
            ui.text(left + 150, y, value, color)
        ui.text(left + 22, bottom + 42, "위아래 키 선택 · 좌우 키 변경 · R 초기화", (181, 197, 209), 14)
        ui.text(left + 22, bottom + 18, "F1 / Esc 계속하기", (181, 197, 209), 14)
