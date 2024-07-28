import pygame 

#Takes rectangle's size, position and a point. Returns true if that
#point is inside the rectangle and false if it isnt.
def pointInRectanlge(px, py, rw, rh, rx, ry):
    if px > rx and px < rx  + rw:
        if py > ry and py < ry + rh:
            return True
    return False

#Blueprint to make sliders in the game
class Slider:
    def __init__(self, position:tuple, upperValue:int=100, percent:float = 34, text:str="",
                 outlineSize:tuple=(400, 40))->None:
        self.position = position
        self.outlineSize = outlineSize
        self.text = text
        #self.sliderWidth = sliderWidth
        self.upperValue = upperValue
        self.sliderWidth = int(outlineSize[0] * percent / 100)
        self.drone = None
        self.motor_index = None
        self.motor_sign = 1
        
    #returns the current value of the slider
    def getValue(self)->float:
        return self.sliderWidth / (self.outlineSize[0] / self.upperValue)

    #renders slider and the text showing the value of the slider
    def render(self, display:pygame.display)->None:
        #draw outline and slider rectangles
        pygame.draw.rect(display, (0, 0, 0), (self.position[0], self.position[1], 
                                              self.outlineSize[0], self.outlineSize[1]), 3)
        
        pygame.draw.rect(display, (0, 0, 0), (self.position[0], self.position[1], 
                                              self.sliderWidth, self.outlineSize[1]))

        #determite size of font
        self.font = pygame.font.Font(pygame.font.get_default_font(), 3 * int((15/100)*self.outlineSize[1]))

        #create text surface with value
        valueSurf = self.font.render(f"{self.text}: {round(self.getValue())}", True, (255, 0, 0))
        
        #centre text
        textx = self.position[0] + (self.outlineSize[0]/2) - (valueSurf.get_rect().width/2)
        texty = self.position[1] + (self.outlineSize[1]/2) - (valueSurf.get_rect().height/2)

        display.blit(valueSurf, (textx, texty))

    def set_motor_power_function(self, drone, motor_index, motor_sign):
        self.drone = drone
        self.motor_index = motor_index
        self.motor_sign = motor_sign
        if self.drone is not None and self.motor_index is not None:
            self.drone.motor_set_power_percent(self.motor_index, self.motor_sign * self.getValue() / 100)

    #allows users to change value of the slider by dragging it.
    def changeValue(self)->None:
        #If mouse is pressed and mouse is inside the slider
        mousePos = pygame.mouse.get_pos()
        if pointInRectanlge(mousePos[0], mousePos[1]
                            , self.outlineSize[0], self.outlineSize[1], self.position[0], self.position[1]):
            if pygame.mouse.get_pressed()[0]:
                #the size of the slider
                self.sliderWidth = mousePos[0] - self.position[0]

                #limit the size of the slider
                if self.sliderWidth < 1:
                    self.sliderWidth = 0
                if self.sliderWidth > self.outlineSize[0]:
                    self.sliderWidth = self.outlineSize[0]
        
                if self.drone is not None and self.motor_index is not None:
                    self.drone.motor_set_power_percent(self.motor_index, self.motor_sign * self.getValue() / 100)
