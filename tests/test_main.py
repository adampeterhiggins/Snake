from unittest.mock import MagicMock

import numpy as np
import pytest

from main import NUM_OF_PIXELS, SnakeGame


@pytest.fixture(name="game")
def game_fixture() -> SnakeGame:
    """A fresh game with a mocked canvas."""
    return SnakeGame(canvas=MagicMock())


def test_turn_blocks_reversal(game: SnakeGame) -> None:
    """Reversing direction is ignored."""
    game.direction = np.array(object=[1, 0])
    game.turn(new_direction=np.array(object=[-1, 0]))
    assert game.direction.tolist() == [1, 0]


def test_turn_allows_perpendicular(game: SnakeGame) -> None:
    """Perpendicular turns are accepted."""
    game.direction = np.array(object=[1, 0])
    game.turn(new_direction=np.array(object=[0, -1]))
    assert game.direction.tolist() == [0, -1]


def test_update_body_moves_head(game: SnakeGame) -> None:
    """Head advances one cell along direction."""
    game.body_array = [np.array(object=[5, 5])]
    game.body_length = 1
    game.direction = np.array(object=[1, 0])
    game.update_body()
    assert game.body_array[-1].tolist() == [6, 5]


def test_update_body_trims_to_body_length(game: SnakeGame) -> None:
    """Body is trimmed back to body_length."""
    game.body_array = [np.array(object=[4, 5]), np.array(object=[5, 5])]
    game.body_length = 2
    game.direction = np.array(object=[1, 0])
    game.update_body()
    assert len(game.body_array) == 2
    assert game.body_array[-1].tolist() == [6, 5]


def test_snake_wraps_off_right_edge(game: SnakeGame) -> None:
    """Head wraps from the right edge to column 0."""
    game.body_array = [np.array(object=[NUM_OF_PIXELS - 1, 5])]
    game.body_length = 1
    game.direction = np.array(object=[1, 0])
    game.update_body()
    assert game.body_array[-1].tolist() == [0, 5]


def test_snake_wraps_off_left_edge(game: SnakeGame) -> None:
    """Head wraps from the left edge to the last column."""
    game.body_array = [np.array(object=[0, 5])]
    game.body_length = 1
    game.direction = np.array(object=[-1, 0])
    game.update_body()
    assert game.body_array[-1].tolist() == [NUM_OF_PIXELS - 1, 5]


def test_update_body_length_never_drops_below_one(game: SnakeGame) -> None:
    """body_length never goes below 1."""
    game.body_length = 1
    game.update_body_length(length_delta=-1)
    assert game.body_length == 1


def test_generate_token_coordinate_within_grid_and_off_body(game: SnakeGame) -> None:
    """Tokens spawn on-grid and never on the body."""
    game.body_array = [np.array(object=[3, 3]), np.array(object=[4, 3])]
    game.body_length = 2
    for _ in range(20):
        coordinate = game.generate_token_coordinate()
        assert all(0 <= component < NUM_OF_PIXELS for component in coordinate)
        assert coordinate not in [segment.tolist() for segment in game.body_array]


def test_check_token_eats_token_and_grows(game: SnakeGame) -> None:
    """Head on a token grows the snake and respawns the token."""
    game.body_array = [np.array(object=[5, 5])]
    game.body_length = 1
    game.token_coordinates = [5, 5]
    game.check_token()
    assert game.body_length == 2
    assert game.token_coordinates != [5, 5]


def test_check_token_miss_leaves_state(game: SnakeGame) -> None:
    """Head off the token leaves state unchanged."""
    game.body_array = [np.array(object=[5, 5])]
    game.body_length = 1
    game.token_coordinates = [0, 0]
    game.check_token()
    assert game.body_length == 1
    assert game.token_coordinates == [0, 0]


def test_check_dead_when_head_hits_body(game: SnakeGame) -> None:
    """Head overlapping the body ends the game."""
    game.body_array = [np.array(object=[1, 1]), np.array(object=[2, 1]), np.array(object=[1, 1])]
    game.body_length = 3
    game.death_value = 0
    game.check_dead()
    assert game.death_value == 1


def test_check_dead_alive_with_short_body(game: SnakeGame) -> None:
    """A length-1 snake is never dead."""
    game.body_array = [np.array(object=[5, 5])]
    game.body_length = 1
    game.death_value = 0
    game.check_dead()
    assert game.death_value == 0


def test_square_vertices_returns_four_corners(game: SnakeGame) -> None:
    """Returns four corner coordinates."""
    vertices = game.square_vertices(position=np.array(object=[100, 100]), half_width=10)
    assert len(vertices) == 4


def test_eating_token_at_edge_keeps_head_on_grid(game: SnakeGame) -> None:
    """Eating a token on the edge still wraps the head on-grid."""
    # Regression test: eating grows body_length, so update_body used to skip
    # its trim branch — which was also where the % NUM_OF_PIXELS wrap lived —
    # leaving the head off-grid. The wrap must apply regardless of trimming.
    game.body_array = [np.array(object=[NUM_OF_PIXELS - 1, 5])]
    game.body_length = 1
    game.direction = np.array(object=[1, 0])
    game.token_coordinates = [NUM_OF_PIXELS - 1, 5]
    game.check_token()
    game.update_body()
    head_x, _ = game.body_array[-1].tolist()
    assert 0 <= head_x < NUM_OF_PIXELS


def test_eating_token_at_edge_does_not_crash_draw(game: SnakeGame) -> None:
    """Eating a token on the edge does not crash draw_body."""
    # Reproduces the observed IndexError: GRID[cell_x] with cell_x == 12.
    game.body_array = [np.array(object=[NUM_OF_PIXELS - 1, 5])]
    game.body_length = 1
    game.direction = np.array(object=[1, 0])
    game.token_coordinates = [NUM_OF_PIXELS - 1, 5]
    game.check_token()
    game.update_body()
    game.draw_body()
