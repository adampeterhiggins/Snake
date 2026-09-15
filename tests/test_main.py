import importlib
import sys
import tkinter
from typing import Protocol, cast
from unittest.mock import MagicMock

import numpy as np
import pytest


class GameModule(Protocol):
    """Structural type for the freshly imported main game module."""

    NumOfPixels: int
    Direction: np.ndarray
    BodyArray: list[np.ndarray]
    BodyLength: int
    TokenCoords: list[int]
    DeathValue: int
    canvas: MagicMock

    def turn(self, direction: np.ndarray) -> None: ...
    def UpdateBody(self) -> None: ...
    def UpdateBodyLength(self, parity: int) -> None: ...
    def CheckDead(self) -> None: ...
    def GenerateTokenCoord(self) -> list[int]: ...
    def CheckToken(self) -> None: ...
    def DrawBody(self) -> None: ...
    def SquareVertices(self, position: np.ndarray, size: int) -> list[float]: ...


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
    game.Direction = np.array([1, 0])
    game.turn(np.array([-1, 0]))
    assert game.Direction.tolist() == [1, 0]


def test_turn_allows_perpendicular(game: GameModule) -> None:
    """Perpendicular turns are accepted."""
    game.Direction = np.array([1, 0])
    game.turn(np.array([0, -1]))
    assert game.Direction.tolist() == [0, -1]


def test_update_body_moves_head(game: GameModule) -> None:
    """Head advances one cell along Direction."""
    game.BodyArray = [np.array([5, 5])]
    game.BodyLength = 1
    game.Direction = np.array([1, 0])
    game.UpdateBody()
    assert game.BodyArray[-1].tolist() == [6, 5]


def test_update_body_trims_to_body_length(game: GameModule) -> None:
    """Body is trimmed back to BodyLength."""
    game.BodyArray = [np.array([4, 5]), np.array([5, 5])]
    game.BodyLength = 2
    game.Direction = np.array([1, 0])
    game.UpdateBody()
    assert len(game.BodyArray) == 2
    assert game.BodyArray[-1].tolist() == [6, 5]


def test_snake_wraps_off_right_edge(game: GameModule) -> None:
    """Head wraps from the right edge to column 0."""
    game.BodyArray = [np.array([game.NumOfPixels - 1, 5])]
    game.BodyLength = 1
    game.Direction = np.array([1, 0])
    game.UpdateBody()
    assert game.BodyArray[-1].tolist() == [0, 5]


def test_snake_wraps_off_left_edge(game: GameModule) -> None:
    """Head wraps from the left edge to the last column."""
    game.BodyArray = [np.array([0, 5])]
    game.BodyLength = 1
    game.Direction = np.array([-1, 0])
    game.UpdateBody()
    assert game.BodyArray[-1].tolist() == [game.NumOfPixels - 1, 5]


def test_update_body_length_never_drops_below_one(game: GameModule) -> None:
    """BodyLength never goes below 1."""
    game.BodyLength = 1
    game.UpdateBodyLength(-1)
    assert game.BodyLength == 1


def test_generate_token_coord_within_grid_and_off_body(game: GameModule) -> None:
    """Tokens spawn on-grid and never on the body."""
    game.BodyArray = [np.array([3, 3]), np.array([4, 3])]
    game.BodyLength = 2
    for _ in range(20):
        coord = game.GenerateTokenCoord()
        assert all(0 <= c < game.NumOfPixels for c in coord)
        assert coord not in [x.tolist() for x in game.BodyArray]


def test_check_token_eats_token_and_grows(game: GameModule) -> None:
    """Head on a token grows the snake and respawns the token."""
    game.BodyArray = [np.array([5, 5])]
    game.BodyLength = 1
    game.TokenCoords = [5, 5]
    game.CheckToken()
    assert game.BodyLength == 2
    assert game.TokenCoords != [5, 5]


def test_check_token_miss_leaves_state(game: GameModule) -> None:
    """Head off the token leaves state unchanged."""
    game.BodyArray = [np.array([5, 5])]
    game.BodyLength = 1
    game.TokenCoords = [0, 0]
    game.CheckToken()
    assert game.BodyLength == 1
    assert game.TokenCoords == [0, 0]


def test_check_dead_when_head_hits_body(game: GameModule) -> None:
    """Head overlapping the body ends the game."""
    game.BodyArray = [np.array([1, 1]), np.array([2, 1]), np.array([1, 1])]
    game.BodyLength = 3
    game.DeathValue = 0
    game.CheckDead()
    assert game.DeathValue == 1


def test_check_dead_alive_with_short_body(game: GameModule) -> None:
    """A length-1 snake is never dead."""
    game.BodyArray = [np.array([5, 5])]
    game.BodyLength = 1
    game.DeathValue = 0
    game.CheckDead()
    assert game.DeathValue == 0


def test_square_vertices_returns_four_corners(game: GameModule) -> None:
    """Returns four corner coordinates."""
    vertices = game.SquareVertices(np.array([100, 100]), 10)
    assert len(vertices) == 4


def test_eating_token_at_edge_keeps_head_on_grid(game: GameModule) -> None:
    """Eating a token on the edge still wraps the head on-grid."""
    # Head sits on a token at the right edge, moving right. Eating grows
    # BodyLength, so UpdateBody skips its trim branch — which is also where
    # the % NumOfPixels wrap lives. The head must still land on-grid.
    game.BodyArray = [np.array([game.NumOfPixels - 1, 5])]
    game.BodyLength = 1
    game.Direction = np.array([1, 0])
    game.TokenCoords = [game.NumOfPixels - 1, 5]
    game.CheckToken()
    game.UpdateBody()
    x, _ = game.BodyArray[-1].tolist()
    assert 0 <= x < game.NumOfPixels


def test_eating_token_at_edge_does_not_crash_draw(game: GameModule) -> None:
    """Eating a token on the edge does not crash DrawBody."""
    # Reproduces the observed IndexError: grid[Token_x] with Token_x == 12.
    game.BodyArray = [np.array([game.NumOfPixels - 1, 5])]
    game.BodyLength = 1
    game.Direction = np.array([1, 0])
    game.TokenCoords = [game.NumOfPixels - 1, 5]
    game.CheckToken()
    game.UpdateBody()
    game.DrawBody()
