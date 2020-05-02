import math
import os

import pygame
import neat
pygame.font.init()

WIN_WIDTH = 800
WIN_HEIGHT = 800
STAT_FONT = pygame.font.SysFont("Arial", 25)
WINDOW = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))

time = 0
gen = 0

CAR_IMAGE = pygame.transform.scale(pygame.image.load(os.path.join("img", "car.png")), (32, 64))
PATH_IMAGE = pygame.transform.scale(pygame.image.load(os.path.join("img", "path.png")), (800, 800))
FINISH_IMAGE = pygame.transform.scale(pygame.image.load(os.path.join("img", "finish.png")), (32, 32))
VIEWFIELD = pygame.transform.scale(pygame.image.load(os.path.join("img", "sightline.png")), (2, 100))


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


def draw_window(window, cars, path, target):
    window.fill([255,255,40])
    path.draw(window)
    target.draw(window)

    score_label = STAT_FONT.render("Generation: " + str(gen), 1, (255, 255, 255))
    window.blit(score_label, (10, 10))

    time_label = STAT_FONT.render("Time Remaining: " + str(300 -time), 1, (255, 255, 255))
    window.blit(time_label, (10, 750))


    # Car always on top
    for car in cars:
        car.draw(window)

    pygame.display.update()
    pygame.display.set_caption("A Neat Car Game")


def eval_genomes(genomes, config):
    global gen, WINDOW, time
    gen += 1

    # Creating the list of genomes, neural nets, and car objects
    nets = []
    cars = []
    ge = []

    for genome_id, genome in genomes:
        genome.fitness = 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        cars.append(Car(550, 700))
        ge.append(genome)

    # Create the map items
    target = Target(200, 25)
    path = Path()

    clock = pygame.time.Clock()
    time = 0

    run = True
    while run and len(cars) > 0:
        clock.tick(30)
        time += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
                break

        # Link AI to controls
        for x, car in enumerate(cars):
            # Points for existing

            distance = math.sqrt((car.x - target.x)**2 + (car.y-target.y)**2)

            # Data that the AI gets
            tuple_input = [car.x, car.y, distance, path.collide(car), car.tilt, target.x, target.y]

            outputs = nets[cars.index(car)].activate(tuple_input)

            throttle = outputs[0]
            turn = outputs[1]

            if throttle > 0.5:
                car.accel()
                if turn > 0.5:
                    car.turnLeft()
                elif turn < -0.5:
                    car.turnRight()
            elif throttle < -0.5:
                car.decel()
                if turn > 0.5:
                    car.turnLeft()
                elif turn < -0.5:
                    car.turnRight()

            if path.collide(car):
                # Points lost for leaving the track
                car.max_speed = 2
            else:
                car.max_speed = 12

            if target.collide(car):
                ge[x].fitness += 50
                ge[x].fitness += 300 - time
                index = cars.index(car)
                nets.pop(index)
                ge.pop(index)
                cars.pop(index)

            car.move()

        # Remove cars that exit the boundaries, punish them heavily
        for car in cars:
            if car.x > 800 or car.x < 0 or car.y > 800 or car.y < 0:
                index = cars.index(car)
                nets.pop(index)
                ge.pop(index)
                cars.pop(index)

        # Remove stragglers and punish them heavily
        if time > 300:
            for car in cars:
                index = cars.index(car)
                nets.pop(index)
                ge.pop(index)
                cars.pop(index)

        draw_window(WINDOW, cars, path, target)

        # # Get keypresses, used for human input
        # keys = pygame.key.get_pressed()
        # if keys[pygame.K_UP]:
        #     human_car.accel()
        #     if keys[pygame.K_RIGHT]:
        #         human_car.turnRight()
        #     if keys[pygame.K_LEFT]:
        #         human_car.turnLeft()
        # if keys[pygame.K_DOWN]:
        #     human_car.decel()
        #     if keys[pygame.K_RIGHT]:
        #         human_car.turnRight()
        #     if keys[pygame.K_LEFT]:
        #         human_car.turnLeft()
        #
        # # Slow the car down if it is off the path
        # if path.collide(human_car):
        #     human_car.setMaxSpeed(2)
        # else:
        #     human_car.setMaxSpeed(10)
        #
        # human_car.move()


def run(config_file):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat. DefaultSpeciesSet, neat.DefaultStagnation, config_file)

    pop = neat.Population(config)

    pop.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    pop.add_reporter(stats)

    winner = pop.run(eval_genomes, 500)
    print("Determined best genome to be {!s}".format(winner))


if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    run(config_path)
