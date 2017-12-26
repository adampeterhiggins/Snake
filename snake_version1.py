from __future__ import division
from Tkinter import * 
from random import randint
from math import * 
import numpy as np

PixelSize = 8 #Half width of square pixels (shouldn't be lower than 8)
NumOfPixels = 12 #Number of pixels creating the square canvas (shouldn't be lower than 12)
Delay = 100 #Delay between refresh of canvas in miliseconds, the lower the delay, the more difficult the game is 

CanvasSize = PixelSize * 2 * NumOfPixels
grid = map(int,np.linspace(PixelSize, CanvasSize-PixelSize, NumOfPixels))

CenterIndex = int(floor(NumOfPixels/2))
CanvasCenter = [grid[CenterIndex],grid[CenterIndex]]
BelowCenter = [grid[CenterIndex],grid[CenterIndex + 1]] #One line below the center 

InitialBodyArray = [[CenterIndex, CenterIndex]] #Initial posistion of snake 
InitialBodyLength = 1
InitialDirection = np.array([1,0])

global Direction, BodyArray, BodyLength, DeathValue
Direction = InitialDirection
BodyArray = InitialBodyArray #Places snake in itial posistion 
BodyLength = InitialBodyLength
DeathValue = 1 #DeathValue Determines if the canvas is in "game" mode or in "Splashscreen mode", 1 for Splashscreen, 0 for game 

tk = Tk()
tk.title("Snake")

canvas = Canvas(tk, width=CanvasSize, height=CanvasSize)
canvas.pack()

canvas.create_text(CanvasCenter, text = "Snake!") #SplashScreen
canvas.create_text(BelowCenter, text="Press Enter To Begin")

def turn(dir):
    global Direction
    if np.array_equal(dir,(-1)*Direction) == False: #Don't allow snake to reverse direction
	    Direction = dir

def EdgeDetection(): #Loops the canvas
	global BodyArray
	for i, coords in enumerate(BodyArray):
		x_pos = coords[0]
		y_pos = coords[1]
		if x_pos > NumOfPixels-1:
			x_pos = 0
			BodyArray[i] = np.array([x_pos,y_pos])
		elif x_pos < 0:
			x_pos = NumOfPixels-1
			BodyArray[i] = np.array([x_pos,y_pos])
		if y_pos > NumOfPixels-1:
			y_pos = 0
			BodyArray[i] = np.array([x_pos,y_pos])
		elif y_pos < 0:
			y_pos = NumOfPixels-1
			BodyArray[i] = np.array([x_pos,y_pos])

def UpdateBody():
	global BodyArray
	oldPos = BodyArray[-1]
	newPos = oldPos + Direction
	BodyArray = BodyArray + [newPos]
	while len(BodyArray) > BodyLength:
		BodyArray = BodyArray[1:]

def UpdateBodyLength(parity): #Updates length of body by parity 
	global BodyLength
	if parity == -1:
		if BodyLength > 1:
			BodyLength = BodyLength + parity
	else:
		BodyLength = BodyLength + parity

def CheckDead(): #Checks if snake head is in same square as another square in the body of the snake 
	global DeathValue
	if BodyLength > 1:
		head = BodyArray[-1].tolist()
		if head in [x.tolist() for x in BodyArray[0:BodyLength-1]]:
			canvas.delete('all')
			canvas.create_text(CanvasCenter, text="Score: %s " % (BodyLength-1))
			canvas.create_text(BelowCenter, text = "Press Enter To Play Again")
			DeathValue = 1
			
def GenerateTokenCoord(): 
	TokenProvisionalCoords = [randint(0,NumOfPixels-1) for x in [0,1] ]
	if TokenProvisionalCoords not in [x.tolist() for x in BodyArray[0:BodyLength-1]]: #To check that we haven't generated a token inside the body of the snake 
		return TokenProvisionalCoords
	else:
		return GenerateTokenCoord()

def EatToken(): #Generates new token and increases body length by one 
	global TokenCoords
	UpdateBodyLength(1)
	TokenCoords = GenerateTokenCoord()


def CheckToken(): #Checks if the snake head is in the same coordinates as the token 
	head = list(BodyArray[-1])
	if np.array_equal(head, TokenCoords) == True:
		EatToken()

def SquareVertices(Posistion, size): #returns an array of corner posistions of square with center Posistion and half width size
	a = [(Posistion + np.array([-size,-size])).tolist(), (Posistion + np.array([size,size])).tolist()]
	return [item+3 for sublist in a for item in sublist] # +3 to account for tkinter window top left padding 

def DrawBox(Posistion, PixelSize, Colour):
	InnerPixelSize = int(ceil(PixelSize/2))
	[Token_x, Token_y] = Posistion
	TokenCenter = np.array([grid[Token_x], grid[Token_y]])
	TokenOuterBox = SquareVertices(TokenCenter, PixelSize)
	TokenInnerBox = SquareVertices(TokenCenter, InnerPixelSize)
	canvas.create_rectangle(TokenOuterBox,fill="blue",width=0)
	canvas.create_rectangle(TokenInnerBox,fill=Colour,width=0)

def DrawBody():
	for i, Pos in enumerate(BodyArray):
		if i!= len(BodyArray) - 1: #The first block in the snake is orange, with the rest being yellow 
			DrawBox(Pos, PixelSize, "yellow")
		else:
			DrawBox(Pos, PixelSize, "orange")

def DrawBackground():
	for i in range(0,NumOfPixels):
		for j in range(0,NumOfPixels):
			if (i+j) % 2 == 0:				
				Box = SquareVertices([int(grid[i]),int(grid[j])], PixelSize)
				canvas.create_rectangle(Box,fill="grey",outline="grey",width=0)

def DrawToken():
	DrawBox(TokenCoords, PixelSize, "red")


def loop():
	canvas.delete('all')
	CheckToken()
	UpdateBody()
	EdgeDetection()
	DrawBackground()
	DrawBody()
	DrawToken()
	CheckDead()
	if DeathValue == 0: #Iterate loop only when not dead
		canvas.after(Delay,loop)  

def begin(event):
	global TokenCoords, DeathValue, BodyArray, BodyLength, Direction
	if DeathValue == 1: #When dead, reset variables to initial state, regenerate token
		BodyArray = InitialBodyArray
		BodyLength = InitialBodyLength
		Direction = InitialDirection
		TokenCoords = GenerateTokenCoord()
		DeathValue = 0
		TokenCoords = GenerateTokenCoord()
		loop()

tk.bind("<Right>", lambda event : turn(np.array([1,0])))
tk.bind("<Up>", lambda event : turn(np.array([0,-1])))
tk.bind("<Left>", lambda event : turn(np.array([-1,0])))
tk.bind("<Down>", lambda event : turn(np.array([0,1])))
tk.bind("<Return>", begin)

mainloop()