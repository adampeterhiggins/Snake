import math
import tkinter
from random import randint

import numpy as np

PIXEL_SIZE: int = 40  # Half width of square pixels (shouldn't be lower than 8)
NUM_OF_PIXELS: int = 12  # Number of pixels creating the square canvas (shouldn't be lower than 12)
DELAY: int = 100  # Delay between refresh of canvas in miliseconds, the lower the delay, the more difficult the game is

CANVAS_SIZE = PIXEL_SIZE * 2 * NUM_OF_PIXELS
GRID = list(map(int, np.linspace(start=PIXEL_SIZE, stop=CANVAS_SIZE - PIXEL_SIZE, num=NUM_OF_PIXELS)))

CENTER_INDEX = int(math.floor(NUM_OF_PIXELS / 2))
CANVAS_CENTER = [GRID[CENTER_INDEX], GRID[CENTER_INDEX]]
BELOW_CENTER = [GRID[CENTER_INDEX], GRID[CENTER_INDEX + 1]]  # One line below the center

INITIAL_BODY_ARRAY = [np.array(object=[CENTER_INDEX, CENTER_INDEX])]  # Initial posistion of snake
INITIAL_DIRECTION = np.array(object=[1, 0])

global direction, body_array, body_length, death_value
direction: np.ndarray = INITIAL_DIRECTION
body_array: list[np.ndarray] = INITIAL_BODY_ARRAY  # Places snake in itial posistion
body_length: int = 1
death_value: int = 1  # 1 for "Splashscreen mode", 0 for "game" mode
token_coordinates: list[int]  # Bound inside begin_game() before the game loop starts
canvas: tkinter.Canvas  # Bound inside main()


def turn(new_direction: np.ndarray) -> None:
    """Ignore attempts to reverse direction."""
    global direction
    if not np.array_equal(a1=new_direction, a2=(-1) * direction):
        direction = new_direction


def update_body() -> None:
    """Advance the head along direction and trim the body to body_length."""
    global body_array
    old_position = body_array[-1]
    new_position = (old_position + direction) % NUM_OF_PIXELS
    body_array = body_array + [new_position]
    while len(body_array) > body_length:
        body_array = [
            segment % NUM_OF_PIXELS for segment in body_array[1:]
        ]  # Using mod NUM_OF_PIXELS so the snake loops around the canvas;
        # the % operation works because elements of body_array are numpy arrays


def update_body_length(length_delta: int) -> None:
    """Update the body length by length_delta, never below 1."""
    global body_length
    if length_delta == -1:
        if body_length > 1:
            body_length = body_length + length_delta
    else:
        body_length = body_length + length_delta


def check_dead() -> None:
    """End the game if the head overlaps the body."""
    global death_value
    if body_length > 1:
        head = body_array[-1].tolist()
        if head in [segment.tolist() for segment in body_array[0 : body_length - 1]]:
            canvas.delete("all")
            canvas.create_text(CANVAS_CENTER, text="Score: %s " % (body_length - 1))
            canvas.create_text(BELOW_CENTER, text="Press Enter To Play Again")
            death_value = 1


def generate_token_coordinate() -> list[int]:
    """Random on-grid coordinates not occupied by the body."""
    candidate_coordinates = [randint(a=0, b=NUM_OF_PIXELS - 1) for _ in [0, 1]]
    if candidate_coordinates not in [
        segment.tolist() for segment in body_array
    ]:  # To check that we haven't generated a token inside the body of the snake
        return candidate_coordinates
    else:
        return generate_token_coordinate()


def eat_token() -> None:
    """Grow the body by one and respawn the token."""
    global token_coordinates
    update_body_length(length_delta=1)
    token_coordinates = generate_token_coordinate()


def check_token() -> None:
    """Eat the token if the head is on it."""
    head = list(body_array[-1])
    if np.array_equal(a1=head, a2=token_coordinates):
        eat_token()


def square_vertices(position: np.ndarray, half_width: int) -> list[int]:
    """Corner coords of the square centred at position with the given half width."""
    corners = [
        (position + np.array(object=[-half_width, -half_width])).tolist(),
        (position + np.array(object=[half_width, half_width])).tolist(),
    ]
    return [
        coordinate + 3 for corner in corners for coordinate in corner
    ]  # +3 to account for tkinter window top left padding


def draw_box(position: np.ndarray | list[int], pixel_size: int, colour: str) -> None:
    """Draw a bordered square cell centred on grid position."""
    inner_size = int(math.ceil(pixel_size / 2))
    cell_x, cell_y = position
    cell_center = np.array(object=[GRID[cell_x], GRID[cell_y]])
    outer_box = square_vertices(position=cell_center, half_width=pixel_size)
    inner_box = square_vertices(position=cell_center, half_width=inner_size)
    canvas.create_rectangle(outer_box, fill="blue", width=0)
    canvas.create_rectangle(inner_box, fill=colour, width=0)


def draw_body() -> None:
    """Draw the snake; head orange, body yellow."""
    for segment_index, segment_position in enumerate(body_array):
        if segment_index != len(body_array) - 1:  # The first block in the snake is orange, with the rest being yellow
            draw_box(position=segment_position, pixel_size=PIXEL_SIZE, colour="yellow")
        else:
            draw_box(position=segment_position, pixel_size=PIXEL_SIZE, colour="orange")


def draw_background() -> None:
    """Draw the checkerboard background."""
    for column in range(NUM_OF_PIXELS):
        for row in range(NUM_OF_PIXELS):
            if (column + row) % 2 == 0:
                tile = square_vertices(
                    position=np.array(object=[int(GRID[column]), int(GRID[row])]), half_width=PIXEL_SIZE
                )
                canvas.create_rectangle(tile, fill="grey", outline="grey", width=0)


def draw_token() -> None:
    """Draw the token cell."""
    draw_box(position=token_coordinates, pixel_size=PIXEL_SIZE, colour="red")


def game_loop() -> None:
    """Run one game tick and reschedule while alive."""
    canvas.delete("all")
    check_token()
    update_body()
    draw_background()
    draw_token()
    draw_body()
    check_dead()
    if death_value == 0:  # Iterate loop only when not dead
        canvas.after(DELAY, func=game_loop)


def begin_game(event: tkinter.Event) -> None:
    """Reset game state and start the loop."""
    global token_coordinates, death_value, body_array, body_length, direction
    if death_value == 1:  # When dead, reset variables to initial state, regenerate token
        body_array = INITIAL_BODY_ARRAY
        body_length = 1
        direction = INITIAL_DIRECTION
        token_coordinates = generate_token_coordinate()
        death_value = 0
        token_coordinates = generate_token_coordinate()
        game_loop()


def main() -> None:
    """Create the window, bind keys, and start the event loop."""
    global canvas
    root = tkinter.Tk()
    root.title(string="Snake")
    canvas = tkinter.Canvas(master=root, width=CANVAS_SIZE, height=CANVAS_SIZE)
    canvas.pack()
    canvas.create_text(CANVAS_CENTER, text="Snake!")  # SplashScreen
    canvas.create_text(BELOW_CENTER, text="Press Enter To Begin")
    root.bind(sequence="<Right>", func=lambda event: turn(new_direction=np.array(object=[1, 0])))
    root.bind(sequence="<Up>", func=lambda event: turn(new_direction=np.array(object=[0, -1])))
    root.bind(sequence="<Left>", func=lambda event: turn(new_direction=np.array(object=[-1, 0])))
    root.bind(sequence="<Down>", func=lambda event: turn(new_direction=np.array(object=[0, 1])))
    root.bind(sequence="<Return>", func=begin_game)
    tkinter.mainloop()


if __name__ == "__main__":
    main()
