import math
import tkinter
from random import randint

import numpy as np

PIXEL_SIZE: int = 40  # Half width of square pixels (shouldn't be lower than 8)
NUM_OF_PIXELS: int = 12  # Number of pixels creating the square canvas (shouldn't be lower than 12)
DELAY: int = 100  # Delay between refresh of canvas in miliseconds, the lower the delay, the more difficult the game is

CANVAS_SIZE = PIXEL_SIZE * 2 * NUM_OF_PIXELS
GRID = list(map(int, np.linspace(PIXEL_SIZE, CANVAS_SIZE - PIXEL_SIZE, NUM_OF_PIXELS)))

CENTER_INDEX = int(math.floor(NUM_OF_PIXELS / 2))
CANVAS_CENTER = [GRID[CENTER_INDEX], GRID[CENTER_INDEX]]
BELOW_CENTER = [GRID[CENTER_INDEX], GRID[CENTER_INDEX + 1]]  # One line below the center

INITIAL_BODY_ARRAY = [np.array([CENTER_INDEX, CENTER_INDEX])]  # Initial posistion of snake
INITIAL_DIRECTION = np.array([1, 0])

global direction, body_array, body_length, death_value
direction: np.ndarray = INITIAL_DIRECTION
body_array: list[np.ndarray] = INITIAL_BODY_ARRAY  # Places snake in itial posistion
body_length: int = 1
death_value: int = 1  # 1 for "Splashscreen mode", 0 for "game" mode
token_coords: list[int]  # Bound inside begin() before the game loop starts

tk = tkinter.Tk()
tk.title("Snake")

canvas = tkinter.Canvas(tk, width=CANVAS_SIZE, height=CANVAS_SIZE)
canvas.pack()

canvas.create_text(CANVAS_CENTER, text="Snake!")  # SplashScreen
canvas.create_text(BELOW_CENTER, text="Press Enter To Begin")


def turn(new_direction: np.ndarray) -> None:
    """Ignore attempts to reverse direction."""
    global direction
    if not np.array_equal(new_direction, (-1) * direction):
        direction = new_direction


def update_body() -> None:
    """Advance the head along direction and trim the body to body_length."""
    global body_array
    old_pos = body_array[-1]
    new_pos = (old_pos + direction) % NUM_OF_PIXELS
    body_array = body_array + [new_pos]
    while len(body_array) > body_length:
        body_array = [
            x % NUM_OF_PIXELS for x in body_array[1:]
        ]  # Using mod NUM_OF_PIXELS so the snake loops around the canvas;
        # the % operation works because elements of body_array are numpy arrays


def update_body_length(parity: int) -> None:
    """Update the body length by parity, never below 1."""
    global body_length
    if parity == -1:
        if body_length > 1:
            body_length = body_length + parity
    else:
        body_length = body_length + parity


def check_dead() -> None:
    """End the game if the head overlaps the body."""
    global death_value
    if body_length > 1:
        head = body_array[-1].tolist()
        if head in [x.tolist() for x in body_array[0 : body_length - 1]]:
            canvas.delete("all")
            canvas.create_text(CANVAS_CENTER, text="Score: %s " % (body_length - 1))
            canvas.create_text(BELOW_CENTER, text="Press Enter To Play Again")
            death_value = 1


def generate_token_coord() -> list[int]:
    """Random on-grid coords not occupied by the body."""
    token_provisional_coords = [randint(0, NUM_OF_PIXELS - 1) for x in [0, 1]]
    if token_provisional_coords not in [
        x.tolist() for x in body_array[0 : body_length - 1]
    ]:  # To check that we haven't generated a token inside the body of the snake
        return token_provisional_coords
    else:
        return generate_token_coord()


def eat_token() -> None:
    """Grow the body by one and respawn the token."""
    global token_coords
    update_body_length(1)
    token_coords = generate_token_coord()


def check_token() -> None:
    """Eat the token if the head is on it."""
    head = list(body_array[-1])
    if np.array_equal(head, token_coords):
        eat_token()


def square_vertices(position: np.ndarray, size: int) -> list[int]:
    """Corner coords of the square centred at position with half-width size."""
    a = [(position + np.array([-size, -size])).tolist(), (position + np.array([size, size])).tolist()]
    return [item + 3 for sublist in a for item in sublist]  # +3 to account for tkinter window top left padding


def draw_box(position: np.ndarray | list[int], pixel_size: int, colour: str) -> None:
    """Draw a bordered square cell centred on grid position."""
    inner_pixel_size = int(math.ceil(pixel_size / 2))
    [token_x, token_y] = position
    token_center = np.array([GRID[token_x], GRID[token_y]])
    token_outer_box = square_vertices(token_center, pixel_size)
    token_inner_box = square_vertices(token_center, inner_pixel_size)
    canvas.create_rectangle(token_outer_box, fill="blue", width=0)
    canvas.create_rectangle(token_inner_box, fill=colour, width=0)


def draw_body() -> None:
    """Draw the snake; head orange, body yellow."""
    for i, pos in enumerate(body_array):
        if i != len(body_array) - 1:  # The first block in the snake is orange, with the rest being yellow
            draw_box(pos, PIXEL_SIZE, "yellow")
        else:
            draw_box(pos, PIXEL_SIZE, "orange")


def draw_background() -> None:
    """Draw the checkerboard background."""
    for i in range(0, NUM_OF_PIXELS):
        for j in range(0, NUM_OF_PIXELS):
            if (i + j) % 2 == 0:
                box = square_vertices(np.array([int(GRID[i]), int(GRID[j])]), PIXEL_SIZE)
                canvas.create_rectangle(box, fill="grey", outline="grey", width=0)


def draw_token() -> None:
    """Draw the token cell."""
    draw_box(token_coords, PIXEL_SIZE, "red")


def loop() -> None:
    """Run one game tick and reschedule while alive."""
    canvas.delete("all")
    check_token()
    update_body()
    draw_background()
    draw_token()
    draw_body()
    check_dead()
    if death_value == 0:  # Iterate loop only when not dead
        canvas.after(DELAY, loop)


def begin(event: tkinter.Event) -> None:
    """Reset game state and start the loop."""
    global token_coords, death_value, body_array, body_length, direction
    if death_value == 1:  # When dead, reset variables to initial state, regenerate token
        body_array = INITIAL_BODY_ARRAY
        body_length = 1
        direction = INITIAL_DIRECTION
        token_coords = generate_token_coord()
        death_value = 0
        token_coords = generate_token_coord()
        loop()


tk.bind("<Right>", lambda event: turn(np.array([1, 0])))
tk.bind("<Up>", lambda event: turn(np.array([0, -1])))
tk.bind("<Left>", lambda event: turn(np.array([-1, 0])))
tk.bind("<Down>", lambda event: turn(np.array([0, 1])))
tk.bind("<Return>", begin)

tkinter.mainloop()
