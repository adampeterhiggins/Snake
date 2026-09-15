import importlib
import sys
import tkinter
from typing import Protocol, cast
from unittest.mock import MagicMock

import numpy as np
import pytest


class GameModule(Protocol):
    """Structural type for the freshly imported main game module."""

    NUM_OF_PIXELS: int
    direction: np.ndarray
    body_array: list[np.ndarray]
    body_length: int
    token_coords: list[int]
    death_value: int
    canvas: MagicMock

    def turn(self, new_direction: np.ndarray) -> None: ...
    def update_body(self) -> None: ...
    def update_body_length(self, parity: int) -> None: ...
    def check_dead(self) -> None: ...
    def generate_token_coord(self) -> list[int]: ...
    def check_token(self) -> None: ...
    def draw_body(self) -> None: ...
    def square_vertices(self, position: np.ndarray, size: int) -> list[int]: ...


@pytest.fixture(name="game")
def game_fixture(monkeypatch: pytest.MonkeyPatch) -> GameModule:
    """Import src/main.py with tkinter patched out, fresh module state per test."""
    canvas = MagicMock()
    monkeypatch.setattr(tkinter, "Tk", MagicMock)
    monkeypatch.setattr(tkinter, "Canvas", lambda *args, **kwargs: canvas)
    monkeypatch.setattr(tkinter, "mainloop", lambda: None)
    sys.modules.pop("main", None)
    main = cast(GameModule, importlib.import_module("main"))
    main.canvas = canvas
    return main


def test_turn_blocks_reversal(game: GameModule) -> None:
    """Reversing direction is ignored."""
    game.direction = np.array([1, 0])
    game.turn(np.array([-1, 0]))
    assert game.direction.tolist() == [1, 0]


def test_turn_allows_perpendicular(game: GameModule) -> None:
    """Perpendicular turns are accepted."""
    game.direction = np.array([1, 0])
    game.turn(np.array([0, -1]))
    assert game.direction.tolist() == [0, -1]


def test_update_body_moves_head(game: GameModule) -> None:
    """Head advances one cell along direction."""
    game.body_array = [np.array([5, 5])]
    game.body_length = 1
    game.direction = np.array([1, 0])
    game.update_body()
    assert game.body_array[-1].tolist() == [6, 5]


def test_update_body_trims_to_body_length(game: GameModule) -> None:
    """Body is trimmed back to body_length."""
    game.body_array = [np.array([4, 5]), np.array([5, 5])]
    game.body_length = 2
    game.direction = np.array([1, 0])
    game.update_body()
    assert len(game.body_array) == 2
    assert game.body_array[-1].tolist() == [6, 5]


def test_snake_wraps_off_right_edge(game: GameModule) -> None:
    """Head wraps from the right edge to column 0."""
    game.body_array = [np.array([game.NUM_OF_PIXELS - 1, 5])]
    game.body_length = 1
    game.direction = np.array([1, 0])
    game.update_body()
    assert game.body_array[-1].tolist() == [0, 5]


def test_snake_wraps_off_left_edge(game: GameModule) -> None:
    """Head wraps from the left edge to the last column."""
    game.body_array = [np.array([0, 5])]
    game.body_length = 1
    game.direction = np.array([-1, 0])
    game.update_body()
    assert game.body_array[-1].tolist() == [game.NUM_OF_PIXELS - 1, 5]


def test_update_body_length_never_drops_below_one(game: GameModule) -> None:
    """body_length never goes below 1."""
    game.body_length = 1
    game.update_body_length(-1)
    assert game.body_length == 1


def test_generate_token_coord_within_grid_and_off_body(game: GameModule) -> None:
    """Tokens spawn on-grid and never on the body."""
    game.body_array = [np.array([3, 3]), np.array([4, 3])]
    game.body_length = 2
    for _ in range(20):
        coord = game.generate_token_coord()
        assert all(0 <= c < game.NUM_OF_PIXELS for c in coord)
        assert coord not in [x.tolist() for x in game.body_array]


def test_check_token_eats_token_and_grows(game: GameModule) -> None:
    """Head on a token grows the snake and respawns the token."""
    game.body_array = [np.array([5, 5])]
    game.body_length = 1
    game.token_coords = [5, 5]
    game.check_token()
    assert game.body_length == 2
    assert game.token_coords != [5, 5]


def test_check_token_miss_leaves_state(game: GameModule) -> None:
    """Head off the token leaves state unchanged."""
    game.body_array = [np.array([5, 5])]
    game.body_length = 1
    game.token_coords = [0, 0]
    game.check_token()
    assert game.body_length == 1
    assert game.token_coords == [0, 0]


def test_check_dead_when_head_hits_body(game: GameModule) -> None:
    """Head overlapping the body ends the game."""
    game.body_array = [np.array([1, 1]), np.array([2, 1]), np.array([1, 1])]
    game.body_length = 3
    game.death_value = 0
    game.check_dead()
    assert game.death_value == 1


def test_check_dead_alive_with_short_body(game: GameModule) -> None:
    """A length-1 snake is never dead."""
    game.body_array = [np.array([5, 5])]
    game.body_length = 1
    game.death_value = 0
    game.check_dead()
    assert game.death_value == 0


def test_square_vertices_returns_four_corners(game: GameModule) -> None:
    """Returns four corner coordinates."""
    vertices = game.square_vertices(np.array([100, 100]), 10)
    assert len(vertices) == 4


def test_eating_token_at_edge_keeps_head_on_grid(game: GameModule) -> None:
    """Eating a token on the edge still wraps the head on-grid."""
    # Regression test: eating grows body_length, so update_body used to skip
    # its trim branch — which was also where the % NUM_OF_PIXELS wrap lived —
    # leaving the head off-grid. The wrap must apply regardless of trimming.
    game.body_array = [np.array([game.NUM_OF_PIXELS - 1, 5])]
    game.body_length = 1
    game.direction = np.array([1, 0])
    game.token_coords = [game.NUM_OF_PIXELS - 1, 5]
    game.check_token()
    game.update_body()
    x, _ = game.body_array[-1].tolist()
    assert 0 <= x < game.NUM_OF_PIXELS


def test_eating_token_at_edge_does_not_crash_draw(game: GameModule) -> None:
    """Eating a token on the edge does not crash draw_body."""
    # Reproduces the observed IndexError: GRID[token_x] with token_x == 12.
    game.body_array = [np.array([game.NUM_OF_PIXELS - 1, 5])]
    game.body_length = 1
    game.direction = np.array([1, 0])
    game.token_coords = [game.NUM_OF_PIXELS - 1, 5]
    game.check_token()
    game.update_body()
    game.draw_body()
