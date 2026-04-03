import argparse
import math
import os
from collections import deque
from dataclasses import dataclass

import pygame


WIDTH = 1600
HEIGHT = 980
MIN_WIDTH = 1000
MIN_HEIGHT = 640
FPS = 60
HISTORY_SECONDS = 12.0

LEFT_PANEL = pygame.Rect(38, 96, 900, 846)
RIGHT_PANEL = pygame.Rect(960, 96, 602, 846)

BG = (152, 214, 237)
PANEL = (246, 252, 255)
PANEL_LINE = (215, 232, 240)
TITLE = (10, 60, 82)
TEXT = (30, 72, 92)
SUBTLE = (71, 110, 127)
WHITE = (255, 255, 255)
BLACK = (18, 24, 31)
RED = (239, 63, 70)
RED_DARK = (201, 47, 55)
BLUE = (26, 83, 179)
BLUE_LIGHT = (77, 184, 255)
CYAN = (34, 190, 220)
GREEN = (48, 156, 64)
PURPLE = (141, 95, 212)
PINK = (227, 106, 200)
YELLOW = (242, 191, 22)
GRAY = (190, 194, 199)
DARK_GRAY = (123, 129, 135)
BROWN = (138, 92, 60)


def clamp(value, low, high):
    return max(low, min(high, value))


def approach(current, target, rate, dt):
    return current + (target - current) * clamp(rate * dt, 0.0, 1.0)


def draw_text(surface, font, text, color, pos, align="topleft"):
    image = font.render(text, True, color)
    rect = image.get_rect()
    setattr(rect, align, pos)
    surface.blit(image, rect)
    return rect


def draw_pipe(surface, color, points, width):
    if len(points) < 2:
        return
    pygame.draw.lines(surface, color, False, points, width)
    for px, py in points:
        pygame.draw.circle(surface, color, (int(px), int(py)), width // 2)


def draw_valve(surface, center, color):
    pygame.draw.circle(surface, WHITE, center, 9)
    pygame.draw.circle(surface, color, center, 9, 2)
    pygame.draw.line(surface, color, (center[0] - 5, center[1]), (center[0] + 5, center[1]), 2)


def draw_gauge(surface, center, radius, value, label, unit, accent, fonts):
    pygame.draw.circle(surface, WHITE, center, radius)
    pygame.draw.circle(surface, DARK_GRAY, center, radius, 3)
    for angle in (-120, -60, 0, 60, 120):
        rad = math.radians(angle)
        p1 = (center[0] + math.cos(rad) * (radius - 8), center[1] + math.sin(rad) * (radius - 8))
        p2 = (center[0] + math.cos(rad) * (radius - 2), center[1] + math.sin(rad) * (radius - 2))
        pygame.draw.line(surface, DARK_GRAY, p1, p2, 2)

    normalized = clamp((value - 10.0) / 35.0, 0.0, 1.0)
    angle = math.radians(-120 + 240 * normalized)
    needle = (center[0] + math.cos(angle) * (radius - 11), center[1] + math.sin(angle) * (radius - 11))
    pygame.draw.line(surface, accent, center, needle, 4)
    pygame.draw.circle(surface, accent, center, 5)
    draw_text(surface, fonts["small"], label, TEXT, (center[0], center[1] - radius - 22), "center")
    draw_text(surface, fonts["small"], f"{value:0.1f} {unit}", TEXT, (center[0], center[1] + radius + 8), "center")


@dataclass(frozen=True)
class PlotConfig:
    title: str
    unit: str
    key: str
    color: tuple[int, int, int]
    vmin: float
    vmax: float


class HeaterSimulation:
    def __init__(self):
        self.time = 0.0
        self.tap_open = False
        self.tap_opening = 1.0
        self.inlet_temp = 15.0
        self.outlet_temp = 15.0
        self.setpoint = 40.0
        self.flow = 0.0
        self.gas_valve = 0.0
        self.igniter = 0.0
        self.fan = 0.0
        self.igniter_timer = 0.0
        self.history = {
            "time": deque(),
            "tap": deque(),
            "tap_opening": deque(),
            "flow": deque(),
            "inlet": deque(),
            "setpoint": deque(),
            "igniter": deque(),
            "gas": deque(),
            "fan": deque(),
            "outlet": deque(),
        }
        self.record()

    def toggle_tap(self):
        self.set_tap_open(not self.tap_open)

    def set_tap_open(self, is_open):
        is_open = bool(is_open)
        was_closed = not self.tap_open and is_open
        self.tap_open = is_open
        if was_closed and self.tap_opening > 0.02:
            self.igniter_timer = 0.8

    def set_tap_opening(self, opening):
        previous = self.tap_opening
        self.tap_opening = clamp(opening, 0.0, 1.0)
        if self.tap_open and previous <= 0.02 and self.tap_opening > 0.02:
            self.igniter_timer = 0.8

    def set_setpoint(self, value):
        self.setpoint = clamp(value, 30.0, 55.0)

    def set_inlet_temp(self, value):
        self.inlet_temp = clamp(value, 10.0, 25.0)
        self.outlet_temp = max(self.outlet_temp, self.inlet_temp)

    def update(self, dt):
        self.time += dt

        effective_opening = self.tap_opening if self.tap_open else 0.0
        flow_target = 8.0 * effective_opening
        flow_rate = 1.4 + effective_opening * 1.4 if effective_opening > 0.0 else 4.2
        self.flow = approach(self.flow, flow_target, flow_rate, dt)

        if self.tap_open and self.flow > 0.45 and self.igniter_timer <= 0.0 and self.gas_valve < 2.0:
            self.igniter_timer = 0.55

        if self.igniter_timer > 0.0:
            self.igniter_timer = max(0.0, self.igniter_timer - dt)
        self.igniter = 1.0 if self.igniter_timer > 0.0 else 0.0

        burner_enable = self.tap_open and effective_opening > 0.02 and self.flow > 0.35
        fan_target = 1.0 if burner_enable or self.gas_valve > 2.0 else 0.0
        self.fan = approach(self.fan, fan_target, 6.0, dt)

        gas_target = 0.0
        if burner_enable:
            temp_error = max(0.0, self.setpoint - self.outlet_temp)
            gas_target = 16.0 + temp_error * 2.15 + self.flow * 3.2
            if self.igniter > 0.0:
                gas_target += 8.0
            gas_target = clamp(gas_target, 0.0, 70.0)

        response_rate = 1.8 if gas_target > self.gas_valve else 3.2
        self.gas_valve = approach(self.gas_valve, gas_target, response_rate, dt)

        flow_factor = min(self.flow / 6.5, 1.0)
        gas_factor = min(self.gas_valve / 60.0, 1.0)
        heating_factor = flow_factor * gas_factor
        outlet_target = self.inlet_temp
        if burner_enable or self.gas_valve > 1.0:
            outlet_target = self.inlet_temp + (self.setpoint - self.inlet_temp) * heating_factor

        temp_rate = 1.3 + heating_factor * 1.7 if outlet_target >= self.outlet_temp else 2.6
        self.outlet_temp = approach(self.outlet_temp, outlet_target, temp_rate, dt)
        self.outlet_temp = max(self.inlet_temp, self.outlet_temp)
        self.record()

    def record(self):
        self.history["time"].append(self.time)
        self.history["tap"].append(1.0 if self.tap_open else 0.0)
        self.history["tap_opening"].append(self.tap_opening * 100.0 if self.tap_open else 0.0)
        self.history["flow"].append(self.flow)
        self.history["inlet"].append(self.inlet_temp)
        self.history["setpoint"].append(self.setpoint)
        self.history["igniter"].append(self.igniter)
        self.history["gas"].append(self.gas_valve)
        self.history["fan"].append(self.fan)
        self.history["outlet"].append(self.outlet_temp)

        while self.history["time"] and self.time - self.history["time"][0] > HISTORY_SECONDS:
            for series in self.history.values():
                series.popleft()


class ToggleButton:
    def __init__(self, rect, label, initial, on_change, fonts):
        self.rect = rect
        self.label = label
        self.value = bool(initial)
        self.on_change = on_change
        self.fonts = fonts

    def set_value(self, value, emit=False):
        self.value = bool(value)
        if emit and self.on_change is not None:
            self.on_change(self.value)

    def draw(self, surface):
        draw_text(surface, self.fonts["small"], self.label, TITLE, (self.rect.x, self.rect.y))
        button_rect = pygame.Rect(self.rect.x, self.rect.y + 22, self.rect.width, self.rect.height - 22)
        active_color = GREEN if self.value else RED_DARK
        fill = (228, 246, 233) if self.value else (251, 235, 236)
        pygame.draw.rect(surface, fill, button_rect, border_radius=14)
        pygame.draw.rect(surface, active_color, button_rect, 2, border_radius=14)
        text = "ON" if self.value else "OFF"
        draw_text(surface, self.fonts["small"], text, active_color, button_rect.center, "center")

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            button_rect = pygame.Rect(self.rect.x, self.rect.y + 22, self.rect.width, self.rect.height - 22)
            if button_rect.collidepoint(event.pos):
                self.set_value(not self.value, emit=True)
                return True
        return False


class SliderControl:
    def __init__(self, rect, label, min_value, max_value, initial_value, on_change, value_formatter, fonts):
        self.rect = rect
        self.label = label
        self.min_value = min_value
        self.max_value = max_value
        self.value = initial_value
        self.on_change = on_change
        self.value_formatter = value_formatter
        self.fonts = fonts
        self.dragging = False

    def set_value(self, value, emit=False):
        self.value = clamp(value, self.min_value, self.max_value)
        if emit and self.on_change is not None:
            self.on_change(self.value)

    def draw(self, surface):
        draw_text(surface, self.fonts["small"], self.label, TITLE, (self.rect.x, self.rect.y))
        draw_text(surface, self.fonts["small"], self.value_formatter(self.value), TITLE, (self.rect.right, self.rect.y), "topright")

        track = self._track_rect()
        pygame.draw.line(surface, PANEL_LINE, track.midleft, track.midright, 8)
        fill_x = self._value_to_x(self.value)
        pygame.draw.line(surface, BLUE, track.midleft, (fill_x, track.centery), 8)
        pygame.draw.circle(surface, WHITE, (fill_x, track.centery), 12)
        pygame.draw.circle(surface, BLUE, (fill_x, track.centery), 12, 3)

        draw_text(surface, self.fonts["tiny"], f"{self.min_value:g}", SUBTLE, (track.x, track.bottom + 8))
        draw_text(surface, self.fonts["tiny"], f"{self.max_value:g}", SUBTLE, (track.right, track.bottom + 8), "topright")

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            self.dragging = True
            self._update_from_mouse(event.pos[0])
            return True

        if event.type == pygame.MOUSEMOTION and self.dragging:
            self._update_from_mouse(event.pos[0])
            return True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging:
            self.dragging = False
            self._update_from_mouse(event.pos[0])
            return True

        return False

    def _track_rect(self):
        return pygame.Rect(self.rect.x + 10, self.rect.y + 34, self.rect.width - 20, 12)

    def _value_to_x(self, value):
        track = self._track_rect()
        ratio = 0.0 if self.max_value == self.min_value else (value - self.min_value) / (self.max_value - self.min_value)
        return round(track.x + clamp(ratio, 0.0, 1.0) * track.width)

    def _update_from_mouse(self, mouse_x):
        track = self._track_rect()
        ratio = clamp((mouse_x - track.x) / track.width, 0.0, 1.0)
        value = self.min_value + ratio * (self.max_value - self.min_value)
        self.set_value(value, emit=True)


class HeaderView:
    def __init__(self, fonts):
        self.fonts = fonts
        self.state_rect = pygame.Rect(1055, 24, 210, 44)
        self.tap_rect = pygame.Rect(1280, 18, 255, 50)

    def draw(self, surface, sim, paused, speed_multiplier):
        draw_text(surface, self.fonts["title"], "Gas water heater system - pygame simulation", TITLE, (48, 24))
        draw_text(surface, self.fonts["small"], "Press Space to toggle the tap, press P to pause, or use the sliders under the plant.", TEXT, (50, 64))

        tap_text = "TAP OPEN" if sim.tap_open else "TAP CLOSED"
        tap_color = GREEN if sim.tap_open else RED_DARK
        pygame.draw.rect(surface, WHITE, self.tap_rect, border_radius=18)
        pygame.draw.rect(surface, tap_color, self.tap_rect, 3, border_radius=18)
        draw_text(surface, self.fonts["label"], tap_text, tap_color, self.tap_rect.center, "center")

        state_color = RED_DARK if paused else BLUE
        pygame.draw.rect(surface, WHITE, self.state_rect, border_radius=16)
        pygame.draw.rect(surface, state_color, self.state_rect, 2, border_radius=16)
        status = "Paused" if paused else "Running"
        draw_text(surface, self.fonts["small"], f"{status}  |  {speed_multiplier:0.2g}x speed", state_color, self.state_rect.center, "center")


class ControlPanelView:
    def __init__(self, rect, fonts, on_pause, on_tap, on_speed, on_opening, on_setpoint, on_inlet):
        self.rect = rect
        self.fonts = fonts
        x = rect.x + 18
        y = rect.y + 18
        w = rect.width - 36
        half = (w - 16) // 2

        self.pause_button = ToggleButton(pygame.Rect(x, y, 160, 60), "Pause simulation", False, on_pause, fonts)
        self.tap_button = ToggleButton(pygame.Rect(x + 180, y, 160, 60), "Tap command", False, on_tap, fonts)
        self.speed_slider = SliderControl(pygame.Rect(x + 360, y, w - 360, 60), "Simulation speed", 0.25, 4.0, 1.0, on_speed, lambda v: f"{v:0.2f}x", fonts)
        self.opening_slider = SliderControl(pygame.Rect(x, y + 76, w, 60), "Tap opening", 0.0, 1.0, 1.0, on_opening, lambda v: f"{v * 100:0.0f} %", fonts)
        self.setpoint_slider = SliderControl(pygame.Rect(x, y + 152, half, 60), "Target temperature", 30.0, 55.0, 40.0, on_setpoint, lambda v: f"{v:0.1f} C", fonts)
        self.inlet_slider = SliderControl(pygame.Rect(x + half + 16, y + 152, half, 60), "Inlet temperature", 10.0, 25.0, 15.0, on_inlet, lambda v: f"{v:0.1f} C", fonts)

    def draw(self, surface):
        pygame.draw.rect(surface, WHITE, self.rect, border_radius=20)
        pygame.draw.rect(surface, PANEL_LINE, self.rect, 2, border_radius=20)
        draw_text(surface, self.fonts["label"], "Interactive controls", TITLE, (self.rect.x + 16, self.rect.y + 10))
        self.pause_button.draw(surface)
        self.tap_button.draw(surface)
        self.speed_slider.draw(surface)
        self.opening_slider.draw(surface)
        self.setpoint_slider.draw(surface)
        self.inlet_slider.draw(surface)
        draw_text(surface, self.fonts["tiny"], "Tap opening directly changes flow and the water stream drawn in the plant.", SUBTLE, (self.rect.x + 18, self.rect.bottom - 18))

    def handle_event(self, event):
        for control in (
            self.pause_button,
            self.tap_button,
            self.speed_slider,
            self.opening_slider,
            self.setpoint_slider,
            self.inlet_slider,
        ):
            if control.handle_event(event):
                return True
        return False

    def sync(self, sim, paused, speed_multiplier):
        self.pause_button.set_value(paused)
        self.tap_button.set_value(sim.tap_open)
        self.speed_slider.set_value(speed_multiplier)
        self.opening_slider.set_value(sim.tap_opening)
        self.setpoint_slider.set_value(sim.setpoint)
        self.inlet_slider.set_value(sim.inlet_temp)


class SystemView:
    def __init__(self, rect, fonts, control_panel, on_tap_toggle):
        self.rect = rect
        self.fonts = fonts
        self.control_panel = control_panel
        self.on_tap_toggle = on_tap_toggle
        self.tap_box = pygame.Rect(760, 428, 126, 130)
        self.diagram_rect = pygame.Rect(rect.x + 14, rect.y + 48, rect.width - 28, 500)

    def draw(self, surface, sim, paused, speed_multiplier):
        pygame.draw.rect(surface, PANEL, self.rect, border_radius=28)
        pygame.draw.rect(surface, PANEL_LINE, self.rect, 2, border_radius=28)
        draw_text(surface, self.fonts["label"], "Plant / schematic", TITLE, (self.rect.x + 20, self.rect.y + 14))
        pygame.draw.rect(surface, (250, 254, 255), self.diagram_rect, border_radius=22)
        pygame.draw.rect(surface, PANEL_LINE, self.diagram_rect, 1, border_radius=22)

        self._draw_gas_line(surface)
        self._draw_heater(surface, sim)
        self._draw_tank(surface, sim)
        self._draw_pipe_network(surface)
        self._draw_expansion_tank(surface, sim)
        self._draw_lcd(surface, sim)
        self._draw_faucet(surface, sim)
        self._draw_labels(surface)
        self.control_panel.draw(surface)

    def handle_event(self, event):
        if self.control_panel.handle_event(event):
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.tap_box.collidepoint(event.pos):
            self.on_tap_toggle()
            return True
        return False

    def _draw_gas_line(self, surface):
        pygame.draw.line(surface, YELLOW, (92, 182), (92, 470), 8)
        pygame.draw.line(surface, YELLOW, (92, 470), (182, 470), 8)
        pygame.draw.line(surface, YELLOW, (182, 470), (182, 432), 8)
        draw_valve(surface, (92, 320), YELLOW)
        draw_text(surface, self.fonts["small"], "Gas line", TEXT, (62, 150))

    def _draw_heater(self, surface, sim):
        body = pygame.Rect(132, 210, 170, 245)
        pygame.draw.rect(surface, (244, 245, 247), body, border_radius=8)
        pygame.draw.rect(surface, GRAY, body, 2, border_radius=8)
        pygame.draw.rect(surface, (228, 230, 234), (158, 402, 118, 36), border_radius=4)
        pygame.draw.rect(surface, (167, 169, 174), (214, 408, 44, 18), border_radius=3)
        pygame.draw.rect(surface, RED, (250, 396, 26, 8), border_radius=2)
        pygame.draw.rect(surface, GRAY, (200, 146, 44, 64), border_radius=18)
        pygame.draw.circle(surface, DARK_GRAY, (222, 178), 25, 4)
        draw_gauge(surface, (185, 420), 18, sim.outlet_temp, "Outlet", "C", RED, self.fonts)
        draw_text(surface, self.fonts["small"], "Gas heater", TEXT, (216, 466), "center")

    def _draw_tank(self, surface, sim):
        tank = pygame.Rect(390, 250, 250, 300)
        pygame.draw.rect(surface, (241, 243, 245), tank, border_radius=10)
        pygame.draw.rect(surface, GRAY, tank, 2, border_radius=10)
        pygame.draw.circle(surface, WHITE, (515, 320), 22)
        pygame.draw.circle(surface, DARK_GRAY, (515, 320), 22, 2)
        draw_text(surface, self.fonts["small"], "T", RED, (515, 319), "center")
        draw_text(surface, self.fonts["small"], f"{sim.outlet_temp:0.1f} C", TITLE, (515, 348), "center")
        pygame.draw.circle(surface, (171, 174, 179), (515, 478), 38)
        draw_text(surface, self.fonts["small"], "Thermal body", TEXT, (515, 530), "center")

    def _draw_pipe_network(self, surface):
        draw_pipe(surface, RED, [(302, 412), (390, 412), (390, 405), (690, 405)], 12)
        draw_pipe(surface, BLUE, [(238, 412), (238, 515), (390, 515)], 12)
        draw_pipe(surface, RED, [(640, 345), (752, 345)], 9)
        draw_pipe(surface, BLUE, [(640, 495), (748, 495)], 9)
        draw_pipe(surface, RED, [(640, 412), (860, 412)], 9)
        draw_pipe(surface, BLUE, [(640, 515), (860, 515)], 9)
        draw_valve(surface, (690, 412), RED)
        draw_valve(surface, (752, 345), RED)
        draw_valve(surface, (752, 495), BLUE)
        draw_valve(surface, (690, 515), BLUE)

    def _draw_expansion_tank(self, surface, sim):
        expansion = pygame.Rect(705, 302, 82, 118)
        pygame.draw.rect(surface, BLUE, expansion, border_radius=40)
        pygame.draw.rect(surface, (12, 61, 136), (705, 359, 82, 14))
        draw_text(surface, self.fonts["small"], "Expansion tank", TEXT, (746, 275), "center")
        pygame.draw.line(surface, BLUE, (746, 420), (746, 515), 10)
        pygame.draw.line(surface, BLUE, (746, 420), (746, 345), 10)
        pygame.draw.line(surface, BLUE, (746, 420), (836, 420), 8)
        draw_gauge(surface, (836, 420), 24, sim.outlet_temp, "Temp", "C", GREEN, self.fonts)

    def _draw_lcd(self, surface, sim):
        display = pygame.Rect(670, 140, 188, 92)
        screen = pygame.Rect(686, 154, 156, 42)
        pygame.draw.rect(surface, (238, 239, 240), display, border_radius=8)
        pygame.draw.rect(surface, DARK_GRAY, display, 2, border_radius=8)
        pygame.draw.rect(surface, WHITE, screen, border_radius=4)
        pygame.draw.rect(surface, DARK_GRAY, screen, 2, border_radius=4)
        draw_text(surface, self.fonts["display"], f"{sim.outlet_temp:04.1f} C", DARK_GRAY, (764, 175), "center")
        draw_text(surface, self.fonts["tiny"], f"SP {sim.setpoint:0.0f} C", SUBTLE, (764, 200), "center")
        pygame.draw.polygon(surface, BLACK, [(696, 222), (708, 202), (720, 222)])
        pygame.draw.rect(surface, BLACK, (759, 204, 14, 14))
        pygame.draw.polygon(surface, BLACK, [(824, 202), (836, 222), (848, 202)])
        pygame.draw.lines(surface, BLACK, False, [(302, 412), (350, 412), (350, 250), (764, 250), (764, 232)], 4)

    def _draw_faucet(self, surface, sim):
        opening = sim.tap_opening if sim.tap_open else 0.0
        handle_color = GREEN if opening > 0.02 else DARK_GRAY
        pygame.draw.line(surface, RED, (836, 412), (886, 412), 9)
        pygame.draw.line(surface, BLUE, (836, 515), (886, 515), 9)
        pygame.draw.rect(surface, RED, (828, 402, 72, 18), border_radius=4)
        pygame.draw.rect(surface, BLUE, (828, 506, 72, 18), border_radius=4)
        pygame.draw.rect(surface, handle_color, self.tap_box, 3, border_radius=24)
        draw_text(surface, self.fonts["small"], "Tap", TEXT, (823, 405), "center")
        draw_text(surface, self.fonts["tiny"], "click / space", SUBTLE, (823, 423), "center")

        start = (817, 485)
        angle = math.radians(-10 - opening * 55)
        end = (start[0] + math.cos(angle) * 45, start[1] + math.sin(angle) * 45)
        pygame.draw.line(surface, handle_color, start, end, 8)
        pygame.draw.line(surface, handle_color, start, (846, 485), 10)

        for idx in range(5):
            x = 842 + idx * 12
            pygame.draw.line(surface, WHITE, (x, 420), (x, 486), 5)
            pygame.draw.line(surface, WHITE, (x, 526), (x, 560), 5)

        if sim.flow > 0.05:
            drops = max(2, min(8, int(2 + sim.tap_opening * 6)))
            spacing = 44 / max(drops - 1, 1)
            for idx in range(drops):
                x = 838 + idx * spacing
                phase = (sim.time * (2.4 + sim.tap_opening * 1.8) + idx * 0.18) % 1.0
                y = 566 + phase * (18 + sim.tap_opening * 24)
                pygame.draw.polygon(surface, BLUE_LIGHT, [(x, y), (x - 5, y + 12), (x, y + 24), (x + 5, y + 12)])

    def _draw_labels(self, surface):
        for text, pos in (
            ("Outlet temperature sensor", (600, 318)),
            ("Flow sensor", (594, 454)),
            ("Inlet temperature sensor", (570, 540)),
            ("LCD / setpoint", (670, 240)),
        ):
            draw_text(surface, self.fonts["small"], text, SUBTLE, pos)


class SignalPlotsView:
    def __init__(self, rect, fonts):
        self.rect = rect
        self.fonts = fonts
        self.plot_configs = [
            PlotConfig("Tap open", "0 / 1", "tap", BLUE, 0.0, 1.0),
            PlotConfig("Tap opening", "%", "tap_opening", CYAN, 0.0, 100.0),
            PlotConfig("Flow", "L/min", "flow", BLUE_LIGHT, 0.0, 8.0),
            PlotConfig("Inlet temp", "C", "inlet", BROWN, 10.0, 25.0),
            PlotConfig("Target temp", "C", "setpoint", RED, 30.0, 55.0),
            PlotConfig("Igniter", "pulse", "igniter", PURPLE, 0.0, 1.0),
            PlotConfig("Gas valve", "%", "gas", GREEN, 0.0, 70.0),
            PlotConfig("Outlet temp", "C", "outlet", PINK, 10.0, 55.0),
        ]

    def draw(self, surface, sim, hover_pos=None):
        pygame.draw.rect(surface, PANEL, self.rect, border_radius=28)
        pygame.draw.rect(surface, PANEL_LINE, self.rect, 2, border_radius=28)
        draw_text(surface, self.fonts["label"], "Signal lines", TITLE, (self.rect.x + 20, self.rect.y + 14))

        plot_width = self.rect.width - 36
        start_x = self.rect.x + 18
        start_y = self.rect.y + 52
        gap_y = 8
        available = self.rect.height - 70
        plot_height = (available - gap_y * (len(self.plot_configs) - 1)) // len(self.plot_configs)
        times = list(sim.history["time"])
        hover_x = hover_pos[0] if hover_pos and self.rect.collidepoint(hover_pos) else None

        for idx, config in enumerate(self.plot_configs):
            plot_rect = pygame.Rect(start_x, start_y + idx * (plot_height + gap_y), plot_width, plot_height)
            self._draw_plot(surface, plot_rect, config, list(sim.history[config.key]), times, sim.time, hover_x)

    def _draw_plot(self, surface, rect, config, values, times, now, hover_x=None):
        pygame.draw.rect(surface, WHITE, rect, border_radius=14)
        pygame.draw.rect(surface, PANEL_LINE, rect, 1, border_radius=14)
        draw_text(surface, self.fonts["small"], config.title, TITLE, (rect.x + 12, rect.y + 8))
        draw_text(surface, self.fonts["tiny"], config.unit, SUBTLE, (rect.x + 12, rect.bottom - 18))

        left = rect.x + 88
        right = rect.right - 18
        top = rect.y + 20
        bottom = rect.bottom - 24

        for step in range(5):
            y = int(top + (bottom - top) * step / 4)
            pygame.draw.line(surface, PANEL_LINE, (left, y), (right, y), 1)

        for step in range(0, int(HISTORY_SECONDS) + 1, 3):
            x = int(right - (step / HISTORY_SECONDS) * (right - left))
            pygame.draw.line(surface, PANEL_LINE, (x, top), (x, bottom), 1)
            draw_text(surface, self.fonts["tiny"], f"-{step}s", SUBTLE, (x, bottom + 2), "midtop")

        pygame.draw.line(surface, SUBTLE, (left, top), (left, bottom), 2)
        pygame.draw.line(surface, SUBTLE, (left, bottom), (right, bottom), 2)

        if hover_x is not None:
            guide_x = int(clamp(hover_x, left, right))
            self._draw_dashed_vertical(surface, guide_x, top, bottom)

        if len(times) >= 2:
            points = []
            for time_value, value in zip(times, values):
                age = now - time_value
                if age > HISTORY_SECONDS:
                    continue
                x = right - (age / HISTORY_SECONDS) * (right - left)
                ratio = 0.0 if config.vmax == config.vmin else (value - config.vmin) / (config.vmax - config.vmin)
                y = bottom - clamp(ratio, 0.0, 1.0) * (bottom - top)
                points.append((x, y))
            if len(points) >= 2:
                pygame.draw.lines(surface, config.color, False, points, 3)

        draw_text(surface, self.fonts["tiny"], f"{config.vmax:g}", SUBTLE, (left - 10, top), "topright")
        draw_text(surface, self.fonts["tiny"], f"{config.vmin:g}", SUBTLE, (left - 10, bottom - 10), "topright")
        if values:
            draw_text(surface, self.fonts["tiny"], f"{values[-1]:0.1f}", config.color, (right - 4, top + 2), "topright")

    def _draw_dashed_vertical(self, surface, x, top, bottom):
        dash = 7
        gap = 5
        y = top
        while y < bottom:
            pygame.draw.line(surface, SUBTLE, (x, y), (x, min(y + dash, bottom)), 2)
            y += dash + gap


class HeaterApp:
    def __init__(self, args):
        self.args = args
        self.paused = False
        self.speed_multiplier = 1.0

        if args.headless:
            os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

        pygame.init()
        self.window_size = (WIDTH, HEIGHT)
        self.screen = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
        self.canvas = pygame.Surface((WIDTH, HEIGHT))
        pygame.display.set_caption("Gas Water Heater - pygame")
        self.clock = pygame.time.Clock()
        self.fonts = self._build_fonts()

        self.sim = HeaterSimulation()
        controls_rect = pygame.Rect(LEFT_PANEL.x + 18, LEFT_PANEL.y + 560, LEFT_PANEL.width - 36, 246)
        self.control_panel = ControlPanelView(
            controls_rect,
            self.fonts,
            self.set_paused,
            self.set_tap_state,
            self.set_speed_multiplier,
            self.set_tap_opening,
            self.set_setpoint,
            self.set_inlet_temp,
        )
        self.header_view = HeaderView(self.fonts)
        self.system_view = SystemView(LEFT_PANEL, self.fonts, self.control_panel, self.toggle_tap)
        self.plots_view = SignalPlotsView(RIGHT_PANEL, self.fonts)
        self.sync_controls()

    def _build_fonts(self):
        return {
            "title": pygame.font.SysFont("segoeui", 32, bold=True),
            "label": pygame.font.SysFont("segoeui", 24, bold=True),
            "small": pygame.font.SysFont("segoeui", 18),
            "tiny": pygame.font.SysFont("segoeui", 14),
            "display": pygame.font.SysFont("consolas", 28, bold=True),
        }

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if not self._handle_event(event):
                    running = False
            if not self.paused:
                self.sim.update(dt * self.speed_multiplier)
            self._draw_frame()
            if self.args.seconds > 0.0 and self.sim.time >= self.args.seconds:
                running = False
        pygame.quit()

    def _handle_event(self, event):
        if event.type == pygame.QUIT:
            return False

        if event.type == pygame.VIDEORESIZE:
            self._set_window_size(event.size)
            return True

        translated_event = self._translate_pointer_event(event)
        if self.system_view.handle_event(translated_event):
            self.sync_controls()
            return True
        if translated_event.type == pygame.KEYDOWN:
            if translated_event.key == pygame.K_SPACE:
                self.toggle_tap()
            elif translated_event.key == pygame.K_p:
                self.set_paused(not self.paused)
        return True

    def _draw_frame(self):
        self.canvas.fill(BG)
        hover_pos = self._scale_pos(pygame.mouse.get_pos())
        self.header_view.draw(self.canvas, self.sim, self.paused, self.speed_multiplier)
        self.system_view.draw(self.canvas, self.sim, self.paused, self.speed_multiplier)
        self.plots_view.draw(self.canvas, self.sim, hover_pos)

        if self.window_size == (WIDTH, HEIGHT):
            self.screen.blit(self.canvas, (0, 0))
        else:
            scaled = pygame.transform.smoothscale(self.canvas, self.window_size)
            self.screen.blit(scaled, (0, 0))
        pygame.display.flip()

    def sync_controls(self):
        self.control_panel.sync(self.sim, self.paused, self.speed_multiplier)

    def toggle_tap(self):
        self.sim.toggle_tap()
        self.sync_controls()

    def set_tap_state(self, is_open):
        self.sim.set_tap_open(is_open)
        self.sync_controls()

    def set_speed_multiplier(self, speed):
        self.speed_multiplier = float(speed)
        self.sync_controls()

    def set_tap_opening(self, opening):
        self.sim.set_tap_opening(opening)
        self.sync_controls()

    def set_setpoint(self, value):
        self.sim.set_setpoint(value)
        self.sync_controls()

    def set_inlet_temp(self, value):
        self.sim.set_inlet_temp(value)
        self.sync_controls()

    def set_paused(self, paused):
        self.paused = bool(paused)
        self.sync_controls()

    def _set_window_size(self, size):
        width = max(MIN_WIDTH, int(size[0]))
        height = max(MIN_HEIGHT, int(size[1]))
        self.window_size = (width, height)
        self.screen = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)

    def _translate_pointer_event(self, event):
        if not hasattr(event, "pos"):
            return event

        event_dict = event.dict.copy()
        event_dict["pos"] = self._scale_pos(event.pos)

        if "rel" in event_dict:
            rel_x = event_dict["rel"][0] * WIDTH / self.window_size[0]
            rel_y = event_dict["rel"][1] * HEIGHT / self.window_size[1]
            event_dict["rel"] = (rel_x, rel_y)

        return pygame.event.Event(event.type, event_dict)

    def _scale_pos(self, pos):
        scaled_x = pos[0] * WIDTH / self.window_size[0]
        scaled_y = pos[1] * HEIGHT / self.window_size[1]
        return (scaled_x, scaled_y)


def parse_args():
    parser = argparse.ArgumentParser(description="Gas water heater simulator in pygame.")
    parser.add_argument("--headless", action="store_true", help="Run with the dummy SDL video driver.")
    parser.add_argument("--seconds", type=float, default=0.0, help="Automatically exit after N seconds.")
    return parser.parse_args()


def main():
    HeaterApp(parse_args()).run()


if __name__ == "__main__":
    main()
