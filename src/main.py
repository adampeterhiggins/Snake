import math
import tkinter
from random import randint

import numpy as np

PixelSize: int = 40  # Half width of square pixels (shouldn't be lower than 8)
NumOfPixels: int = 12  # Number of pixels creating the square canvas (shouldn't be lower than 12)
Delay: int = 100  # Delay between refresh of canvas in miliseconds, the lower the delay, the more difficult the game is

CanvasSize = PixelSize * 2 * NumOfPixels
grid = list(map(int, np.linspace(PixelSize, CanvasSize - PixelSize, NumOfPixels)))

CenterIndex = int(math.floor(NumOfPixels / 2))
CanvasCenter = [grid[CenterIndex], grid[CenterIndex]]
BelowCenter = [grid[CenterIndex], grid[CenterIndex + 1]]  # One line below the center

InitialBodyArray = [np.array([CenterIndex, CenterIndex])]  # Initial posistion of snake
InitialDirection = np.array([1, 0])

global Direction, BodyArray, BodyLength, DeathValue
Direction: np.ndarray = InitialDirection
BodyArray: list[np.ndarray] = InitialBodyArray  # Places snake in itial posistion
BodyLength: int = 1
DeathValue: int = 1  # 1 for "Splashscreen mode", 0 for "game" mode
TokenCoords: list[int]  # Bound inside begin() before the game loop starts

tk = tkinter.Tk()
tk.title("Snake")

canvas = tkinter.Canvas(tk, width=CanvasSize, height=CanvasSize)
canvas.pack()

canvas.create_text(CanvasCenter, text="Snake!")  # SplashScreen
canvas.create_text(BelowCenter, text="Press Enter To Begin")


def turn(dir: np.ndarray) -> None:
    """Ignore attempts to reverse direction."""
    global Direction
    if not np.array_equal(dir, (-1) * Direction):
        Direction = dir


def UpdateBody() -> None:
    """Advance the head along Direction and trim the body to BodyLength."""
    global BodyArray
    oldPos = BodyArray[-1]
    newPos = (oldPos + Direction) % NumOfPixels
    BodyArray = BodyArray + [newPos]
    while len(BodyArray) > BodyLength:
        BodyArray = [
            x % NumOfPixels for x in BodyArray[1:]
        ]  # Using mod NumOfPixels so the snake loops around the canvas;
        # the % operation works because elements of BodyArray are numpy arrays


def UpdateBodyLength(parity: int) -> None:
    """Update the body length by parity, never below 1."""
    global BodyLength
    if parity == -1:
        if BodyLength > 1:
            BodyLength = BodyLength + parity
    else:
        BodyLength = BodyLength + parity


def CheckDead() -> None:
    """End the game if the head overlaps the body."""
    global DeathValue
    if BodyLength > 1:
        head = BodyArray[-1].tolist()
        if head in [x.tolist() for x in BodyArray[0 : BodyLength - 1]]:
            canvas.delete("all")
            canvas.create_text(CanvasCenter, text="Score: %s " % (BodyLength - 1))
            canvas.create_text(BelowCenter, text="Press Enter To Play Again")
            DeathValue = 1


def GenerateTokenCoord() -> list[int]:
    """Random on-grid coords not occupied by the body."""
    TokenProvisionalCoords = [randint(0, NumOfPixels - 1) for x in [0, 1]]
    if TokenProvisionalCoords not in [
        x.tolist() for x in BodyArray[0 : BodyLength - 1]
    ]:  # To check that we haven't generated a token inside the body of the snake
        return TokenProvisionalCoords
    else:
        return GenerateTokenCoord()


def EatToken() -> None:
    """Grow the body by one and respawn the token."""
    global TokenCoords
    UpdateBodyLength(1)
    TokenCoords = GenerateTokenCoord()


def CheckToken() -> None:
    """Eat the token if the head is on it."""
    head = list(BodyArray[-1])
    if np.array_equal(head, TokenCoords):
        EatToken()


def SquareVertices(Posistion: np.ndarray, size: int) -> list[int]:
    """Corner coords of the square centred at Posistion with half-width size."""
    a = [(Posistion + np.array([-size, -size])).tolist(), (Posistion + np.array([size, size])).tolist()]
    return [item + 3 for sublist in a for item in sublist]  # +3 to account for tkinter window top left padding


def DrawBox(Posistion: np.ndarray | list[int], PixelSize: int, Colour: str) -> None:
    """Draw a bordered square cell centred on grid position Posistion."""
    InnerPixelSize = int(math.ceil(PixelSize / 2))
    [Token_x, Token_y] = Posistion
    TokenCenter = np.array([grid[Token_x], grid[Token_y]])
    TokenOuterBox = SquareVertices(TokenCenter, PixelSize)
    TokenInnerBox = SquareVertices(TokenCenter, InnerPixelSize)
    canvas.create_rectangle(TokenOuterBox, fill="blue", width=0)
    canvas.create_rectangle(TokenInnerBox, fill=Colour, width=0)


def DrawBody() -> None:
    """Draw the snake; head orange, body yellow."""
    for i, Pos in enumerate(BodyArray):
        if i != len(BodyArray) - 1:  # The first block in the snake is orange, with the rest being yellow
            DrawBox(Pos, PixelSize, "yellow")
        else:
            DrawBox(Pos, PixelSize, "orange")


def DrawBackground() -> None:
    """Draw the checkerboard background."""
    for i in range(0, NumOfPixels):
        for j in range(0, NumOfPixels):
            if (i + j) % 2 == 0:
                Box = SquareVertices(np.array([int(grid[i]), int(grid[j])]), PixelSize)
                canvas.create_rectangle(Box, fill="grey", outline="grey", width=0)


def DrawToken() -> None:
    """Draw the token cell."""
    DrawBox(TokenCoords, PixelSize, "red")


def loop() -> None:
    """Run one game tick and reschedule while alive."""
    canvas.delete("all")
    CheckToken()
    UpdateBody()
    DrawBackground()
    DrawToken()
    DrawBody()
    CheckDead()
    if DeathValue == 0:  # Iterate loop only when not dead
        canvas.after(Delay, loop)


def begin(event: tkinter.Event) -> None:
    """Reset game state and start the loop."""
    global TokenCoords, DeathValue, BodyArray, BodyLength, Direction
    if DeathValue == 1:  # When dead, reset variables to initial state, regenerate token
        BodyArray = InitialBodyArray
        BodyLength = 1
        Direction = InitialDirection
        TokenCoords = GenerateTokenCoord()
        DeathValue = 0
        TokenCoords = GenerateTokenCoord()
        loop()


tk.bind("<Right>", lambda event: turn(np.array([1, 0])))
tk.bind("<Up>", lambda event: turn(np.array([0, -1])))
tk.bind("<Left>", lambda event: turn(np.array([-1, 0])))
tk.bind("<Down>", lambda event: turn(np.array([0, 1])))
tk.bind("<Return>", begin)

tkinter.mainloop()
