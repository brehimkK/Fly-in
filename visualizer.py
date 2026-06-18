#!/usr/bin/env python3
"""
Professional Pygame Visualizer for Fly-In Drone Simulation
==========================================================

Renders the drone routing simulation from simulator.py timeline output.
"""

import math
import re
from typing import Dict, List, Optional, Tuple

import pygame
from models import SimulationMap, Zone


class PygameVisualizer:
    """
    Renders the drone routing simulation from the generated timeline.

    Data flow:
    - Takes sim_map (SimulationMap object)
    - Takes timeline (Dict[int, List[str]]) from SimulationEngine.build_timeline()
    - Parses drone movements: "D1-zone1" or "D1-zone1-zone2"
    - Renders background, connections, zones, and drones
    - Allows interactive playback
    """

    def __init__(self, sim_map: SimulationMap, timeline: Dict[int, List[str]]) -> None:
        pygame.init()

        self.sim_map = sim_map
        self.timeline = timeline

        # Window setup
        self.WINDOW_WIDTH = 1800
        self.WINDOW_HEIGHT = 1100
        self.UI_HEIGHT = 44

        self.screen = pygame.display.set_mode(
            (self.WINDOW_WIDTH, self.WINDOW_HEIGHT),
        )
        pygame.display.set_caption("Fly-in Drone Simulation Visualizer")

        self.clock = pygame.time.Clock()
        self.font_small = pygame.font.SysFont(None, 14)
        self.font_normal = pygame.font.SysFont(None, 18)
        self.font_large = pygame.font.SysFont(None, 24)

        # Visual settings
        self.zone_size = 34
        self.drone_size = 32

        # IMPORTANT:
        # These values are used inside _calculate_scaling().
        # Big spacing makes rows cleaner, but the scaling still keeps the full map visible.
        self.map_zoom = 0.90
        self.spacing_x = 1.00
        self.spacing_y = 1.45
        self.map_margin = 80

        # Connection settings.
        # "line" is cleaner for dense maps.
        # Change to "image" if you want to use the connection.png sprite.
        self.connection_mode = "line"
        self.connection_height = 10

        # Display settings
        self.show_zone_labels = True
        self.label_max_chars = 7

        self.real_turn_keys = sorted(self.timeline.keys())
        self.turn_keys = ["START"] + self.real_turn_keys

        self.current_turn_index = 0
        self.max_turn_index = len(self.turn_keys) - 1
        self.is_playing = True

        # Timing
        self.delay_ms = 1000
        self.turn_elapsed_ms = 0.0

        # Colors
        self.colors: Dict[str, Tuple[int, int, int]] = {
            "red": (220, 50, 50),
            "green": (50, 200, 50),
            "blue": (50, 100, 220),
            "yellow": (220, 220, 50),
            "orange": (255, 140, 0),
            "purple": (180, 100, 200),
            "cyan": (100, 200, 220),
            "pink": (255, 100, 180),
            "gold": (255, 215, 0),
            "lime": (100, 255, 100),
            "gray": (100, 100, 100),
            "default": (150, 150, 150),
        }

        self.drone_colors = [
            (255, 100, 100), (100, 255, 100), (100, 100, 255),
            (255, 255, 100), (255, 100, 255), (100, 255, 255),
            (255, 150, 50), (150, 255, 50), (255, 50, 150),
            (50, 150, 255), (150, 50, 255), (255, 200, 100),
        ]

        # Assets
        self.background_image: Optional[pygame.Surface] = None
        self.zone_image = self._load_alpha_image(
            "assets/zone.png",
            (self.zone_size, self.zone_size),
        )
        self.drone_image = self._load_alpha_image(
            "assets/drone.png",
            (self.drone_size, self.drone_size),
        )
        self.connection_image = self._load_alpha_image(
            "assets/connection.png",
            None,
        )
        self._load_background("assets/map.png")

        # Calculate screen scaling after visual spacing values exist
        self._calculate_scaling()

    def _load_alpha_image(
        self,
        image_path: str,
        size: Optional[Tuple[int, int]],
    ) -> pygame.Surface:
        """Load a PNG image with transparency and optionally scale it."""
        image = pygame.image.load(image_path).convert_alpha()

        if size is not None:
            image = pygame.transform.smoothscale(image, size)

        return image

    def _load_background(self, image_path: str) -> None:
        """Load and resize the background image."""
        try:
            image = pygame.image.load(image_path).convert()
            self.background_image = pygame.transform.smoothscale(
                image,
                (self.WINDOW_WIDTH, self.WINDOW_HEIGHT),
            )
        except pygame.error:
            self.background_image = None

    def _calculate_scaling(self) -> None:
        """Calculate scale so the full spaced map fits inside the screen."""
        if not self.sim_map.zones:
            self.scale = 1.0
            self.map_center_x = 0.0
            self.map_center_y = 0.0
            self.screen_center_x = self.WINDOW_WIDTH / 2
            self.screen_center_y = self.WINDOW_HEIGHT / 2
            return

        zones = list(self.sim_map.zones.values())
        xs = [z.x for z in zones]
        ys = [z.y for z in zones]

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        range_x = max(max_x - min_x, 1)
        range_y = max(max_y - min_y, 1)

        self.map_center_x = min_x + range_x / 2
        self.map_center_y = min_y + range_y / 2

        available_width = self.WINDOW_WIDTH - 2 * self.map_margin
        available_height = self.WINDOW_HEIGHT - self.UI_HEIGHT - 2 * self.map_margin

        # Because spacing is applied later, include it here too.
        scale_x = available_width / (range_x * self.spacing_x)
        scale_y = available_height / (range_y * self.spacing_y)

        self.scale = min(scale_x, scale_y, 80) * self.map_zoom

        self.screen_center_x = self.WINDOW_WIDTH / 2
        self.screen_center_y = self.UI_HEIGHT + (
            (self.WINDOW_HEIGHT - self.UI_HEIGHT) / 2
        )

    def _world_to_screen(self, world_x: float, world_y: float) -> Tuple[int, int]:
        """Convert world coordinates to screen coordinates."""
        screen_x = self.screen_center_x + (
            (world_x - self.map_center_x) * self.scale * self.spacing_x
        )
        screen_y = self.screen_center_y + (
            (world_y - self.map_center_y) * self.scale * self.spacing_y
        )

        return (int(screen_x), int(screen_y))

    def _remove_ansi_codes(self, text: str) -> str:
        """Remove ANSI color codes from text."""
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        return ansi_escape.sub("", text)

    def _parse_movement(self, movement_str: str) -> Tuple[str, str]:
        """
        Parse one movement string.

        Examples:
            "D1-zone1" -> ("D1", "zone1")
            "D1-zone1-zone2" -> ("D1", "zone1-zone2")
        """
        clean = self._remove_ansi_codes(movement_str)

        if "-" not in clean:
            return "", ""

        parts = clean.split("-", 1)
        drone_id = parts[0]
        location = parts[1] if len(parts) > 1 else ""

        return drone_id, location

    def _get_drone_screen_position(
        self,
        location: str,
    ) -> Optional[Tuple[int, int]]:
        """
        Get screen position for a location.

        Supports:
        - zone name
        - connection location like "zone1-zone2"
        """
        if location in self.sim_map.zones:
            zone = self.sim_map.zones[location]
            return self._world_to_screen(zone.x, zone.y)

        parts = location.split("-")
        if len(parts) >= 2:
            zone1_name = parts[0]
            zone2_name = "-".join(parts[1:])

            if (
                zone1_name in self.sim_map.zones
                and zone2_name in self.sim_map.zones
            ):
                z1 = self.sim_map.zones[zone1_name]
                z2 = self.sim_map.zones[zone2_name]

                mid_x = (z1.x + z2.x) / 2
                mid_y = (z1.y + z2.y) / 2

                return self._world_to_screen(mid_x, mid_y)

        return None

    def _get_zone_color(self, zone: Zone) -> Tuple[int, int, int]:
        """Get RGB color for a zone based on its type."""
        if hasattr(zone, "color") and zone.color:
            return self.colors.get(zone.color, self.colors["default"])

        if zone.is_start:
            return self.colors["green"]
        if zone.is_end:
            return self.colors["red"]
        if zone.zone_type == "restricted":
            return self.colors["orange"]
        if zone.zone_type == "priority":
            return self.colors["yellow"]
        if zone.zone_type == "blocked":
            return self.colors["gray"]

        return self.colors["blue"]

    def _get_drone_color(self, drone_id: str) -> Tuple[int, int, int]:
        """Get unique color for a drone."""
        try:
            drone_num = int(drone_id[1:])
            return self.drone_colors[(drone_num - 1) % len(self.drone_colors)]
        except (ValueError, IndexError):
            return (255, 255, 255)

    def _get_positions_for_turn(
        self,
        turn_index: int,
    ) -> Dict[str, Tuple[int, int]]:
        """Return drone positions, starting all drones at the start zone."""
        positions: Dict[str, Tuple[int, int]] = {}

        if turn_index < 0 or turn_index >= len(self.turn_keys):
            return positions

        # 1. First, put every drone on the start zone.
        if self.sim_map.start_zone:
            start_pos = self._world_to_screen(
                self.sim_map.start_zone.x,
                self.sim_map.start_zone.y,
            )

            for i in range(1, self.sim_map.nb_drones + 1):
                positions[f"D{i}"] = start_pos

        # 2. If we are on the virtual START turn, stop here.
        if turn_index == 0:
            return positions

        # 3. Apply all movements from turn 1 up to the current turn.
        # This keeps drones visible even if they do not move in every turn.
        for index in range(1, turn_index + 1):
            turn = self.turn_keys[index]
            movements = self.timeline.get(turn, [])

            for movement in movements:
                drone_id, location = self._parse_movement(movement)

                if not drone_id or not location:
                    continue

                screen_pos = self._get_drone_screen_position(location)

                if screen_pos:
                    positions[drone_id] = screen_pos

        return positions

    def _draw_background(self) -> None:
        """Draw the background image."""
        if self.background_image:
            self.screen.blit(self.background_image, (0, 0))
        else:
            self.screen.fill((30, 30, 30))

    def _draw_connections(self) -> None:
        """
        Draw clean professional connections.

        For dense maps, simple trimmed lines look better than large road images.
        """
        for conn in self.sim_map.connections:
            p1 = self._world_to_screen(conn.zone1.x, conn.zone1.y)
            p2 = self._world_to_screen(conn.zone2.x, conn.zone2.y)

            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            distance = math.hypot(dx, dy)

            if distance <= 0:
                continue

            unit_x = dx / distance
            unit_y = dy / distance

            # Trim the line so it touches the edge of the zones, not their centers.
            trim = self.zone_size * 0.45

            start = (
                int(p1[0] + unit_x * trim),
                int(p1[1] + unit_y * trim),
            )
            end = (
                int(p2[0] - unit_x * trim),
                int(p2[1] - unit_y * trim),
            )

            if self.connection_mode == "image" and self.connection_image:
                self._draw_connection_image(start, end)
            else:
                self._draw_connection_line(start, end)

    def _draw_connection_image(
        self,
        start: Tuple[int, int],
        end: Tuple[int, int],
    ) -> None:
        """Draw a connection using the connection image asset."""
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        distance = max(8, int(math.hypot(dx, dy)))

        mid_x = (start[0] + end[0]) // 2
        mid_y = (start[1] + end[1]) // 2

        angle = math.degrees(math.atan2(-dy, dx))

        image = pygame.transform.smoothscale(
            self.connection_image,
            (distance, self.connection_height),
        )
        image = pygame.transform.rotate(image, angle)

        rect = image.get_rect(center=(mid_x, mid_y))
        self.screen.blit(image, rect)

    def _draw_connection_line(
        self,
        start: Tuple[int, int],
        end: Tuple[int, int],
    ) -> None:
        """Draw a clean layered line connection."""
        # Shadow
        shadow_start = (start[0] + 2, start[1] + 2)
        shadow_end = (end[0] + 2, end[1] + 2)
        pygame.draw.line(self.screen, (30, 25, 20), shadow_start, shadow_end, 5)

        # Outer border
        pygame.draw.line(self.screen, (70, 70, 75), start, end, 5)

        # Inner road color
        pygame.draw.line(self.screen, (155, 150, 145), start, end, 2)

    def _draw_zones(self) -> None:
        """Draw all zones using zone image with type badge."""
        for zone_name, zone in self.sim_map.zones.items():
            pos = self._world_to_screen(zone.x, zone.y)

            rect = self.zone_image.get_rect(center=pos)
            self.screen.blit(self.zone_image, rect)

            badge_color = self._get_zone_color(zone)
            badge_pos = (
                pos[0] + self.zone_size // 4,
                pos[1] - self.zone_size // 4,
            )

            pygame.draw.circle(self.screen, (15, 15, 15), badge_pos, 6)
            pygame.draw.circle(self.screen, badge_color, badge_pos, 4)

            if self.show_zone_labels:
                self._draw_zone_label(zone_name, pos)

    def _draw_zone_label(self, zone_name: str, pos: Tuple[int, int]) -> None:
        """Draw a short readable label under a zone."""
        display_name = zone_name[:self.label_max_chars]

        text = self.font_small.render(display_name, True, (245, 245, 245))
        text_rect = text.get_rect(
            center=(pos[0], pos[1] + self.zone_size // 2 + 9),
        )

        bg_rect = text_rect.inflate(6, 3)
        pygame.draw.rect(self.screen, (0, 0, 0), bg_rect, border_radius=3)
        self.screen.blit(text, text_rect)

    def _smoothstep(self, value: float) -> float:
        """Make movement smoother than linear movement."""
        value = max(0.0, min(1.0, value))
        return value * value * (3.0 - 2.0 * value)

    def _draw_drones_at_turn(self) -> None:
        """Draw drones smoothly between current turn and next turn."""
        if not self.turn_keys:
            return

        current_positions = self._get_positions_for_turn(self.current_turn_index)
        next_positions = self._get_positions_for_turn(
            min(self.current_turn_index + 1, self.max_turn_index),
        )

        drone_ids = sorted(set(current_positions) | set(next_positions))

        progress = self.turn_elapsed_ms / self.delay_ms
        progress = self._smoothstep(progress)

        drone_draw_positions: Dict[str, Tuple[int, int]] = {}

        for drone_id in drone_ids:
            current_pos = current_positions.get(drone_id)
            next_pos = next_positions.get(drone_id)

            if current_pos is None and next_pos is None:
                continue

            if current_pos is None:
                current_pos = next_pos
            if next_pos is None:
                next_pos = current_pos

            x = current_pos[0] + (next_pos[0] - current_pos[0]) * progress
            y = current_pos[1] + (next_pos[1] - current_pos[1]) * progress

            drone_draw_positions[drone_id] = (int(x), int(y))

        drone_draw_positions = self._offset_overlapping_drones(
            drone_draw_positions,
        )

        for drone_id, screen_pos in drone_draw_positions.items():
            self._draw_one_drone(drone_id, screen_pos)

    def _offset_overlapping_drones(
        self,
        positions: Dict[str, Tuple[int, int]],
    ) -> Dict[str, Tuple[int, int]]:
        """
        Spread drones slightly if multiple drones are on the same position.

        This makes groups readable instead of drawing all drones on top of each other.
        """
        groups: Dict[Tuple[int, int], List[str]] = {}

        for drone_id, pos in positions.items():
            key = (round(pos[0] / 6) * 6, round(pos[1] / 6) * 6)
            groups.setdefault(key, []).append(drone_id)

        result = dict(positions)

        for key, drone_ids in groups.items():
            if len(drone_ids) == 1:
                continue

            radius = 13

            for index, drone_id in enumerate(sorted(drone_ids)):
                angle = (math.tau * index) / len(drone_ids)
                base_x, base_y = positions[drone_id]

                result[drone_id] = (
                    int(base_x + math.cos(angle) * radius),
                    int(base_y + math.sin(angle) * radius),
                )

        return result

    def _draw_one_drone(self, drone_id: str, screen_pos: Tuple[int, int]) -> None:
        """Draw one drone with glow, image, and readable ID."""
        color = self._get_drone_color(drone_id)

        # Glow/shadow behind drone so the gray drone is visible on gray zones.
        pygame.draw.circle(self.screen, (0, 0, 0), screen_pos, 16)
        pygame.draw.circle(self.screen, color, screen_pos, 13)
        pygame.draw.circle(self.screen, (255, 255, 255), screen_pos, 13, 2)

        rect = self.drone_image.get_rect(center=screen_pos)
        self.screen.blit(self.drone_image, rect)

        text = self.font_normal.render(drone_id, True, (255, 255, 255))
        text_rect = text.get_rect(
            center=(screen_pos[0], screen_pos[1] + self.drone_size // 2 + 12),
        )

        pygame.draw.rect(
            self.screen,
            (0, 0, 0),
            text_rect.inflate(6, 3),
            border_radius=3,
        )
        self.screen.blit(text, text_rect)

    def _draw_ui(self) -> None:
        """Draw UI elements."""
        pygame.draw.rect(
            self.screen,
            (18, 18, 18),
            (0, 0, self.WINDOW_WIDTH, self.UI_HEIGHT),
        )

        if self.current_turn_index < len(self.turn_keys):
            current_turn = self.turn_keys[self.current_turn_index]
            status = (
                f"Turn: {current_turn} | "
                f"Index: {self.current_turn_index}/{self.max_turn_index}"
            )
        else:
            status = "Simulation Complete"

        status_text = self.font_normal.render(status, True, (255, 255, 100))
        self.screen.blit(status_text, (10, 12))

        play_status = "PAUSED" if not self.is_playing else "PLAYING"
        controls = (
            f"[{play_status}] SPACE: Play/Pause | "
            f"←/→: Step | L: Labels | Q: Quit"
        )

        control_text = self.font_small.render(controls, True, (165, 165, 165))
        self.screen.blit(control_text, (self.WINDOW_WIDTH - 430, 14))

    def _draw_frame(self) -> None:
        """Draw the complete scene."""
        self._draw_background()
        self._draw_connections()
        self._draw_zones()
        self._draw_drones_at_turn()
        self._draw_ui()
        pygame.display.flip()

    def _handle_events(self) -> bool:
        """
        Handle user input.

        Returns:
            False if user wants to quit, True otherwise.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type != pygame.KEYDOWN:
                continue

            if event.key == pygame.K_q:
                return False

            if event.key == pygame.K_SPACE:
                self.is_playing = not self.is_playing

            elif event.key == pygame.K_RIGHT:
                if self.current_turn_index < self.max_turn_index:
                    self.current_turn_index += 1
                    self.turn_elapsed_ms = 0.0
                    self.is_playing = False

            elif event.key == pygame.K_LEFT:
                if self.current_turn_index > 0:
                    self.current_turn_index -= 1
                    self.turn_elapsed_ms = 0.0
                    self.is_playing = False

            elif event.key == pygame.K_HOME:
                self.current_turn_index = 0
                self.turn_elapsed_ms = 0.0

            elif event.key == pygame.K_END:
                self.current_turn_index = self.max_turn_index
                self.turn_elapsed_ms = 0.0

            elif event.key == pygame.K_l:
                self.show_zone_labels = not self.show_zone_labels

        return True

    def _advance_simulation(self, dt_ms: int) -> None:
        """Advance timeline using real elapsed milliseconds."""
        if not self.is_playing:
            return

        self.turn_elapsed_ms += dt_ms

        while self.turn_elapsed_ms >= self.delay_ms:
            self.turn_elapsed_ms -= self.delay_ms

            if self.current_turn_index < self.max_turn_index:
                self.current_turn_index += 1
            else:
                self.is_playing = False
                self.turn_elapsed_ms = 0.0
                break

    def play(self) -> None:
        """Main visualization loop."""
        print("\n" + "=" * 60)
        print("DRONE SIMULATION VISUALIZATION")
        print("=" * 60)
        print(f"Total turns: {len(self.turn_keys)}")
        print(f"Total drones: {self.sim_map.nb_drones}")
        print(f"Total zones: {len(self.sim_map.zones)}")
        print("\nControls:")
        print("  SPACE: Play/Pause")
        print("  LEFT/RIGHT ARROW: Step through turns")
        print("  HOME: Go to start")
        print("  END: Go to end")
        print("  L: Show/Hide labels")
        print("  Q: Quit")
        print("=" * 60 + "\n")

        running = True

        while running:
            dt_ms = self.clock.tick(60)
            running = self._handle_events()
            self._advance_simulation(dt_ms)
            self._draw_frame()

        pygame.quit()


if __name__ == "__main__":
    print("This module is meant to be imported and used with SimulationEngine.")
    print("See simulator.py for usage examples.")
