import math
import os

import pygame
import neat

WIN_WIDTH = 800
WIN_HEIGHT = 800

CAR_IMAGE = pygame.transform.scale(pygame.image.load(os.path.join("img", "car.png")), (32, 64))
PATH_IMAGE = pygame.transform.scale(pygame.image.load(os.path.join("img", "path.png")), (800, 800))
FINISH_IMAGE = pygame.transform.scale(pygame.image.load(os.path.join("img", "finish.png")), (32, 32))


class Car:
    ACCEL = 1
    TURN_RATE = 5
    max_speed = 2

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 90
        self.velX = 0
        self.velY = 0
        self.rot = 0
        self.acceltick = 0
        self.rottick = 0
        self.image = CAR_IMAGE

    def accel(self):
        self.velX += math.cos(math.radians(self.tilt))
        self.velY -= math.sin(math.radians(self.tilt))
        self.acceltick = 0

    def decel(self):
        self.velX -= math.cos(math.radians(self.tilt))
        self.velY += math.sin(math.radians(self.tilt))
        self.acceltick = 0

    def turnLeft(self):
        self.rot = self.TURN_RATE
        self.rottick = 0

    def turnRight(self):
        self.rot = self.TURN_RATE * -1
        self.rottick = 0

    def move(self):
        # Tick count
        self.acceltick += 1
        self.rottick += 1

        # Friction
        if self.acceltick != 0:
            self.velX = (self.velX / self.acceltick)
            self.velY = (self.velY / self.acceltick)

        if self.rottick != 0:
            self.rot /= self.rottick

        # Update movement
        self.tilt += self.rot
        self.x += self.velX
        self.y += self.velY

        # Limit movement
        if self.velX > self.max_speed:
            self.velX = self.max_speed

        if self.velY > self.max_speed:
            self.velY = self.max_speed

        if self.velX < -1 * self.max_speed:
            self.velX = -1 * self.max_speed

        if self.velY < -1 * self.max_speed:
            self.velY = -1 * self.max_speed

    def setMaxSpeed(self, speed):
        self.max_speed = speed

    def draw(self, window):
        rotated_image = pygame.transform.rotate(self.image, self.tilt-90)
        rect = rotated_image.get_rect(center=self.image.get_rect(topleft=(self.x, self.y)).center)

        window.blit(rotated_image, rect.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.image)


class Path:
    def __init__(self):
        self.image = PATH_IMAGE

    def draw(self, window):
        window.blit(self.image, (0, 0))

    def collide(self, car):
        car_mask = car.get_mask()
        path_mask = pygame.mask.from_surface(self.image)

        # Car coordinate minus 0 because the path is always drawn at 0, 0
        offset = (0 - round(car.x), 0 - round(car.y))
        collision_point = car_mask.overlap(path_mask, offset)

        if collision_point:
            return True;

        return False


class Target:
    def __init__(self, x, y):
        self.image = FINISH_IMAGE
        self.x = x
        self.y = y

    def draw(self, window):
        window.blit(self.image, (self.x, self.y))

    def collide(self, car):
        car_mask = car.get_mask()
        path_mask = pygame.mask.from_surface(self.image)

        # Car coordinate minus 0 because the path is always drawn at 0, 0
        offset = (self.x - round(car.x), self.y - round(car.y))
        collision_point = car_mask.overlap(path_mask, offset)

        if collision_point:
            return True;

        return False


def draw_window(window, car, path, target):
    window.fill([255,255,40])
    path.draw(window)
    target.draw(window)
    # Car always on top
    car.draw(window)
    pygame.display.update()
    pygame.display.set_caption("A Neat Car Game")


def main():
    target = Target(200, 25)
    path = Path()
    human_car = Car(550, 700)
    clock = pygame.time.Clock()
    window = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))

    run = True
    while run:
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        # Get keypresses, used for human input
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            human_car.accel()
            if keys[pygame.K_RIGHT]:
                human_car.turnRight()
            if keys[pygame.K_LEFT]:
                human_car.turnLeft()
        if keys[pygame.K_DOWN]:
            human_car.decel()
            if keys[pygame.K_RIGHT]:
                human_car.turnRight()
            if keys[pygame.K_LEFT]:
                human_car.turnLeft()

        # Slow the car down if it is off the path
        if path.collide(human_car):
            human_car.setMaxSpeed(2)
        else:
            human_car.setMaxSpeed(10)

        human_car.move()
        draw_window(window, human_car, path, target)


main()
