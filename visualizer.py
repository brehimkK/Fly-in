#!/usr/bin/env python3
import math
import re
from typing import Dict, List, Optional, Tuple

import pygame
from models import SimulationMap


class PygameVisualizer:
    def __init__(
            self, sim_map: SimulationMap, timeline: Dict[int, List[str]]
            ) -> None:
        pygame.init()

        self.sim_map = sim_map
        self.timeline = timeline

        self.width = 1600
        self.height = 850
        self.ui_height = 40
        self.margin = 70
        self.spacing_x = 1.45
        self.spacing_y = 3

        self.zoom = 1.0
        self.min_zoom = 0.4
        self.max_zoom = 3.0

        self.camera_x = 0
        self.camera_y = 0
        self.dragging = False
        self.last_mouse_pos = (0, 0)

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Fly-in Visualizer")

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 22)
        self.small_font = pygame.font.SysFont(None, 18)

        self.zone_size = 26
        self.drone_size = 28
        self.connection_height = 5

        self.background = self._load_image(
            "assets/map.png", (self.width, self.height))
        self.zone_image = self._load_image(
            "assets/zone.png", (self.zone_size, self.zone_size))
        self.drone_image = self._load_image(
            "assets/drone.png", (self.drone_size, self.drone_size))
        self.connection_image = self._load_image(
            "assets/connection.png", None)

        self.turns = [-1] + sorted(self.timeline.keys())
        self.current_turn = 0
        self.max_turn = len(self.turns) - 1

        self.is_playing = True
        self.delay_ms = 900
        self.elapsed_ms = 0

        self.scale = 1.0
        self.center_x = 0.0
        self.center_y = 0.0

        self._calculate_scale()

    def _load_image(
        self,
        path: str,
        size: Optional[Tuple[int, int]],
    ) -> Optional[pygame.Surface]:
        try:
            image = pygame.image.load(path).convert_alpha()

            if size:
                image = pygame.transform.smoothscale(image, size)

            return image
        except pygame.error:
            return None

    def _calculate_scale(self) -> None:
        zones = list(self.sim_map.zones.values())

        if not zones:
            return

        xs = [zone.x for zone in zones]
        ys = [zone.y for zone in zones]

        min_x = min(xs)
        max_x = max(xs)
        min_y = min(ys)
        max_y = max(ys)

        map_width = max(max_x - min_x, 1)
        map_height = max(max_y - min_y, 1)

        available_width = self.width - self.margin * 2
        available_height = self.height - self.ui_height - self.margin * 2

        self.scale = min(
            available_width / (map_width * self.spacing_x),
            available_height / (map_height * self.spacing_y),
            75,
        )

        self.center_x = min_x + map_width / 2
        self.center_y = min_y + map_height / 2

    def _world_to_screen(self, x: float, y: float) -> Tuple[int, int]:
        screen_x = self.width / 2
        screen_x += (
            x - self.center_x) * self.scale * self.spacing_x * self.zoom
        screen_x += self.camera_x

        screen_y = self.ui_height + (self.height - self.ui_height) / 2
        screen_y += (
            y - self.center_y) * self.scale * self.spacing_y * self.zoom
        screen_y += self.camera_y

        return int(screen_x), int(screen_y)

    def _remove_ansi(self, text: str) -> str:
        pattern = r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])"
        return re.sub(pattern, "", text)

    def _parse_move(self, movement: str) -> Tuple[str, str]:
        movement = self._remove_ansi(movement)

        if "-" not in movement:
            return "", ""

        drone, location = movement.split("-", 1)
        return drone, location

    def _short_name(self, name: str) -> str:
        if len(name) <= 13:
            return name

        parts = name.split("_")

        if len(parts) >= 2:
            return "_".join(parts[:2])[:13]

        return name[:13]

    def _location_position(self, location: str) -> Optional[Tuple[int, int]]:
        if location in self.sim_map.zones:
            zone = self.sim_map.zones[location]
            return self._world_to_screen(zone.x, zone.y)

        if "-" not in location:
            return None

        zone1_name, zone2_name = location.split("-", 1)

        if zone1_name not in self.sim_map.zones:
            return None

        if zone2_name not in self.sim_map.zones:
            return None

        zone1 = self.sim_map.zones[zone1_name]
        zone2 = self.sim_map.zones[zone2_name]

        x = (zone1.x + zone2.x) / 2
        y = (zone1.y + zone2.y) / 2

        return self._world_to_screen(x, y)

    def _smoothstep(self, value: float) -> float:
        value = max(0.0, min(1.0, value))
        return value * value * (3.0 - 2.0 * value)

    def _positions_at_turn(
            self, turn_index: int) -> Dict[str, Tuple[int, int]]:
        positions: Dict[str, Tuple[int, int]] = {}

        if self.sim_map.start_zone:
            start = self.sim_map.start_zone
            start_pos = self._world_to_screen(start.x, start.y)

            for i in range(1, self.sim_map.nb_drones + 1):
                positions[f"D{i}"] = start_pos

        if turn_index == 0:
            return positions

        for index in range(1, turn_index + 1):
            turn = self.turns[index]
            movements = self.timeline.get(turn, [])

            for movement in movements:
                drone, location = self._parse_move(movement)
                position = self._location_position(location)

                if drone and position:
                    positions[drone] = position

        return positions

    def _draw_background(self) -> None:
        if self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill((35, 38, 45))

    def _draw_connection_image(
        self,
        start: Tuple[int, int],
        end: Tuple[int, int],
    ) -> None:
        if not self.connection_image:
            pygame.draw.line(self.screen, (170, 170, 170), start, end, 5)
            return

        dx = end[0] - start[0]
        dy = end[1] - start[1]

        distance = max(10, int(math.hypot(dx, dy)))
        angle = -math.degrees(math.atan2(dy, dx))

        image = pygame.transform.smoothscale(
            self.connection_image,
            (distance, self.connection_height),
        )

        image = pygame.transform.rotate(image, angle)

        mid_x = (start[0] + end[0]) // 2
        mid_y = (start[1] + end[1]) // 2

        rect = image.get_rect(center=(mid_x, mid_y))
        self.screen.blit(image, rect)

    def _draw_connections(self) -> None:
        for connection in self.sim_map.connections:
            start = self._world_to_screen(
                connection.zone1.x,
                connection.zone1.y,
            )

            end = self._world_to_screen(
                connection.zone2.x,
                connection.zone2.y,
            )

            self._draw_connection_image(start, end)

    def _draw_zones(self) -> None:
        for name, zone in self.sim_map.zones.items():
            position = self._world_to_screen(zone.x, zone.y)

            if self.zone_image:
                rect = self.zone_image.get_rect(center=position)
                self.screen.blit(self.zone_image, rect)
            else:
                pygame.draw.circle(self.screen, (80, 140, 230), position, 18)

            text = self.small_font.render(name, True, (255, 255, 255))
            rect = text.get_rect(center=(position[0], position[1] + 23))

            pygame.draw.rect(
                self.screen,
                (0, 0, 0),
                rect.inflate(4, 2),
                border_radius=3,
            )

            self.screen.blit(text, rect)

    def _get_drone_color(self, drone_id: str) -> Tuple[int, int, int]:
        colors = [
            (255, 80, 80),    # red
            (80, 255, 80),    # green
            (80, 150, 255),   # blue
            (255, 255, 80),   # yellow
            (255, 80, 255),   # purple
            (80, 255, 255),   # cyan
            (255, 180, 80),   # orange
            (180, 80, 255),   # violet
        ]

        try:
            drone_number = int(drone_id[1:])
            return colors[(drone_number - 1) % len(colors)]
        except ValueError:
            return (255, 255, 255)

    def _tint_drone(
        self,
        image: pygame.Surface,
        color: Tuple[int, int, int],
    ) -> pygame.Surface:
        tinted = image.copy()
        tinted.fill(color, special_flags=pygame.BLEND_MULT)
        return tinted

    def _draw_drones(self) -> None:
        current_positions = self._positions_at_turn(self.current_turn)

        next_turn = min(self.current_turn + 1, self.max_turn)
        next_positions = self._positions_at_turn(next_turn)

        progress = self.elapsed_ms / self.delay_ms
        progress = self._smoothstep(progress)

        drone_ids = set(current_positions.keys()) | set(next_positions.keys())

        for drone in sorted(drone_ids):
            current_pos = current_positions.get(drone)
            next_pos = next_positions.get(drone)

            if current_pos is None and next_pos is None:
                continue

            if current_pos is None:
                current_pos = next_pos

            if next_pos is None:
                next_pos = current_pos

            if current_pos is None or next_pos is None:
                continue

            x = current_pos[0] + (next_pos[0] - current_pos[0]) * progress
            y = current_pos[1] + (next_pos[1] - current_pos[1]) * progress

            position = (int(x), int(y))

            color = self._get_drone_color(drone)
            pygame.draw.circle(self.screen, color, position, 18)

            if self.drone_image:
                tinted_drone = self._tint_drone(self.drone_image, color)
                rect = tinted_drone.get_rect(center=position)
                self.screen.blit(tinted_drone, rect)
            else:
                pygame.draw.circle(self.screen, color, position, 10)

            text = self.small_font.render(drone, True, (255, 255, 255))
            rect = text.get_rect(center=(position[0], position[1] - 23))
            self.screen.blit(text, rect)

    def _draw_ui(self) -> None:
        pygame.draw.rect(
            self.screen,
            (20, 20, 20),
            (0, 0, self.width, self.ui_height),
        )

        turn = self.turns[self.current_turn]

        if turn == -1:
            turn_text = "START"
        else:
            turn_text = str(turn)

        status = (
            f"Turn: {turn_text} | "
            f"Zoom: {self.zoom:.1f}x | "
            "Drag mouse move | "
            "Scroll zoom | "
            "R reset | "
            "Q quit"
        )

        text = self.font.render(status, True, (255, 255, 255))
        self.screen.blit(text, (12, 11))

    def _draw(self) -> None:
        self._draw_background()
        self._draw_connections()
        self._draw_zones()
        self._draw_drones()
        self._draw_ui()
        pygame.display.flip()

    def _handle_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    self.zoom *= 1.1
                elif event.y < 0:
                    self.zoom /= 1.1

                self.zoom = max(self.min_zoom, min(self.zoom, self.max_zoom))

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.dragging = True
                    self.last_mouse_pos = event.pos

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.dragging = False

            if event.type == pygame.MOUSEMOTION:
                if self.dragging:
                    mouse_x, mouse_y = event.pos
                    last_x, last_y = self.last_mouse_pos

                    dx = mouse_x - last_x
                    dy = mouse_y - last_y

                    self.camera_x += dx
                    self.camera_y += dy

                    self.last_mouse_pos = event.pos

            if event.type != pygame.KEYDOWN:
                continue

            if event.key == pygame.K_q:
                return False

            if event.key == pygame.K_r:
                self.zoom = 1.0
                self.camera_x = 0
                self.camera_y = 0

            if event.key == pygame.K_SPACE:
                self.is_playing = not self.is_playing

            if event.key == pygame.K_RIGHT:
                self.current_turn = min(self.current_turn + 1, self.max_turn)
                self.elapsed_ms = 0
                self.is_playing = False

            if event.key == pygame.K_LEFT:
                self.current_turn = max(self.current_turn - 1, 0)
                self.elapsed_ms = 0
                self.is_playing = False

        return True

    def _update(self, dt_ms: int) -> None:
        if not self.is_playing:
            return

        self.elapsed_ms += dt_ms

        if self.elapsed_ms < self.delay_ms:
            return

        self.elapsed_ms = 0

        if self.current_turn < self.max_turn:
            self.current_turn += 1
        else:
            self.is_playing = False

    def play(self) -> None:
        running = True

        while running:
            dt_ms = self.clock.tick(60)
            running = self._handle_events()
            self._update(dt_ms)
            self._draw()

        pygame.quit()


if __name__ == "__main__":
    print("Use this visualizer from simulator.py")
