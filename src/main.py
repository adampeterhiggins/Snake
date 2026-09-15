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


class SnakeGame:
    """Snake game state and per-tick logic, drawn onto a tkinter canvas."""

    def __init__(self, canvas: tkinter.Canvas) -> None:
        self.canvas = canvas
        self.direction: np.ndarray = INITIAL_DIRECTION
        self.body_array: list[np.ndarray] = INITIAL_BODY_ARRAY
        self.body_length: int = 1
        self.death_value: int = 1  # 1 for "Splashscreen mode", 0 for "game" mode
        self.token_coordinates: list[int] = []  # Respawned inside begin_game()

    def turn(self, new_direction: np.ndarray) -> None:
        """Ignore attempts to reverse direction."""
        if not np.array_equal(a1=new_direction, a2=(-1) * self.direction):
            self.direction = new_direction

    def update_body(self) -> None:
        """Advance the head along direction and trim the body to body_length."""
        old_position = self.body_array[-1]
        new_position = (old_position + self.direction) % NUM_OF_PIXELS
        self.body_array = self.body_array + [new_position]
        while len(self.body_array) > self.body_length:
            self.body_array = [
                segment % NUM_OF_PIXELS for segment in self.body_array[1:]
            ]  # Using mod NUM_OF_PIXELS so the snake loops around the canvas;
            # the % operation works because elements of body_array are numpy arrays

    def update_body_length(self, length_delta: int) -> None:
        """Update the body length by length_delta, never below 1."""
        if length_delta == -1:
            if self.body_length > 1:
                self.body_length = self.body_length + length_delta
        else:
            self.body_length = self.body_length + length_delta

    def check_dead(self) -> None:
        """End the game if the head overlaps the body."""
        if self.body_length > 1:
            head = self.body_array[-1].tolist()
            if head in [segment.tolist() for segment in self.body_array[0 : self.body_length - 1]]:
                self.canvas.delete("all")
                self.canvas.create_text(CANVAS_CENTER, text="Score: %s " % (self.body_length - 1))
                self.canvas.create_text(BELOW_CENTER, text="Press Enter To Play Again")
                self.death_value = 1

    def generate_token_coordinate(self) -> list[int]:
        """Random on-grid coordinates not occupied by the body."""
        candidate_coordinates = [randint(a=0, b=NUM_OF_PIXELS - 1) for _ in [0, 1]]
        if candidate_coordinates not in [
            segment.tolist() for segment in self.body_array
        ]:  # To check that we haven't generated a token inside the body of the snake
            return candidate_coordinates
        else:
            return self.generate_token_coordinate()

    def eat_token(self) -> None:
        """Grow the body by one and respawn the token."""
        self.update_body_length(length_delta=1)
        self.token_coordinates = self.generate_token_coordinate()

    def check_token(self) -> None:
        """Eat the token if the head is on it."""
        head = list(self.body_array[-1])
        if np.array_equal(a1=head, a2=self.token_coordinates):
            self.eat_token()

    @staticmethod
    def square_vertices(position: np.ndarray, half_width: int) -> list[int]:
        """Corner coords of the square centred at position with the given half width."""
        corners = [
            (position + np.array(object=[-half_width, -half_width])).tolist(),
            (position + np.array(object=[half_width, half_width])).tolist(),
        ]
        return [
            coordinate + 3 for corner in corners for coordinate in corner
        ]  # +3 to account for tkinter window top left padding

    def draw_box(self, position: np.ndarray | list[int], pixel_size: int, colour: str) -> None:
        """Draw a bordered square cell centred on grid position."""
        inner_size = int(math.ceil(pixel_size / 2))
        cell_x, cell_y = position
        cell_center = np.array(object=[GRID[cell_x], GRID[cell_y]])
        outer_box = self.square_vertices(position=cell_center, half_width=pixel_size)
        inner_box = self.square_vertices(position=cell_center, half_width=inner_size)
        self.canvas.create_rectangle(outer_box, fill="blue", width=0)
        self.canvas.create_rectangle(inner_box, fill=colour, width=0)

    def draw_body(self) -> None:
        """Draw the snake; head orange, body yellow."""
        for segment_index, segment_position in enumerate(self.body_array):
            # The first block in the snake is orange, with the rest being yellow
            if segment_index != len(self.body_array) - 1:
                self.draw_box(position=segment_position, pixel_size=PIXEL_SIZE, colour="yellow")
            else:
                self.draw_box(position=segment_position, pixel_size=PIXEL_SIZE, colour="orange")

    def draw_background(self) -> None:
        """Draw the checkerboard background."""
        for column in range(NUM_OF_PIXELS):
            for row in range(NUM_OF_PIXELS):
                if (column + row) % 2 == 0:
                    tile = self.square_vertices(
                        position=np.array(object=[int(GRID[column]), int(GRID[row])]), half_width=PIXEL_SIZE
                    )
                    self.canvas.create_rectangle(tile, fill="grey", outline="grey", width=0)

    def draw_token(self) -> None:
        """Draw the token cell."""
        self.draw_box(position=self.token_coordinates, pixel_size=PIXEL_SIZE, colour="red")

    def game_loop(self) -> None:
        """Run one game tick and reschedule while alive."""
        self.canvas.delete("all")
        self.check_token()
        self.update_body()
        self.draw_background()
        self.draw_token()
        self.draw_body()
        self.check_dead()
        if self.death_value == 0:  # Iterate loop only when not dead
            self.canvas.after(DELAY, func=self.game_loop)

    def begin_game(self, event: tkinter.Event) -> None:
        """Reset game state and start the loop."""
        if self.death_value == 1:  # When dead, reset variables to initial state, regenerate token
            self.body_array = INITIAL_BODY_ARRAY
            self.body_length = 1
            self.direction = INITIAL_DIRECTION
            self.token_coordinates = self.generate_token_coordinate()
            self.death_value = 0
            self.token_coordinates = self.generate_token_coordinate()
            self.game_loop()


def main() -> None:
    """Create the window, bind keys, and start the event loop."""
    root = tkinter.Tk()
    root.title(string="Snake")
    canvas = tkinter.Canvas(master=root, width=CANVAS_SIZE, height=CANVAS_SIZE)
    canvas.pack()
    canvas.create_text(CANVAS_CENTER, text="Snake!")  # SplashScreen
    canvas.create_text(BELOW_CENTER, text="Press Enter To Begin")
    game = SnakeGame(canvas=canvas)
    root.bind(sequence="<Right>", func=lambda event: game.turn(new_direction=np.array(object=[1, 0])))
    root.bind(sequence="<Up>", func=lambda event: game.turn(new_direction=np.array(object=[0, -1])))
    root.bind(sequence="<Left>", func=lambda event: game.turn(new_direction=np.array(object=[-1, 0])))
    root.bind(sequence="<Down>", func=lambda event: game.turn(new_direction=np.array(object=[0, 1])))
    root.bind(sequence="<Return>", func=game.begin_game)
    tkinter.mainloop()


if __name__ == "__main__":
    main()
