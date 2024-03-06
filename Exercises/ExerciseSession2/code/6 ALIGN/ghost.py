import pygame
from constants import PACMAN, STOP, UP, DOWN, LEFT, RIGHT, RED, WHITE, YELLOW

from random import uniform


class Ghost(object):
    def __init__(self, screen):
        self.name = PACMAN
        self.position = pygame.math.Vector2(400, 100)
        self.directions = {
            STOP: pygame.math.Vector2(),
            UP: pygame.math.Vector2(0, -1),
            DOWN: pygame.math.Vector2(0, 1),
            LEFT: pygame.math.Vector2(-1, 0),
            RIGHT: pygame.math.Vector2(1, 0),
        }
        self.speed = 10
        self.radius = 10
        self.color = RED

        self.direction = pygame.math.Vector2(self.speed, 0).rotate(uniform(0, 360))
        self.screen = screen
        self.velocity = pygame.math.Vector2()

    def update(self, dt):
        self.velocity = self.seek_and_arrive(pygame.mouse.get_pos())
        self.direction += self.velocity
        if self.direction.length() > self.speed:
            self.direction.scale_to_length(self.speed)

    def getValidKey(self):
        key_pressed = pygame.key.get_pressed()
        if key_pressed[pygame.K_UP]:
            return UP
        if key_pressed[pygame.K_DOWN]:
            return DOWN
        if key_pressed[pygame.K_LEFT]:
            return LEFT
        if key_pressed[pygame.K_RIGHT]:
            return RIGHT
        return STOP

    def render(self, screen):
        pygame.draw.circle(screen, self.color, self.position, self.radius)

    def follow_mouse(self):
        mouse_pos = pygame.mouse.get_pos()
        # Avoid a division by zero in normalization
        mouse_pos = (mouse_pos[0] + 1, mouse_pos[1] + 1)
        self.velocity = (mouse_pos - self.position).normalize() * 0.2

    def draw_vectors(self):
        scale = 25
        APPROACH_RADIUS = 50
        # direction vector
        pygame.draw.line(
            self.screen,
            YELLOW,
            self.position,
            (self.position + self.direction * scale),
            5,
        )
        # desired
        pygame.draw.line(
            self.screen, RED, self.position, (self.position + self.desired * scale), 5
        )
        # approach radius
        pygame.draw.circle(
            self.screen, WHITE, pygame.mouse.get_pos(), APPROACH_RADIUS, 1
        )

    def seek_and_arrive(self, target):
        APPROACH_RADIUS = 50
        self.desired = target - self.position
        distance = (
            self.desired.length()
        )  # we get the distance before normalizing the desired
        self.desired.normalize_ip()  # ip = in place
        if distance < APPROACH_RADIUS:
            self.desired *= distance / APPROACH_RADIUS * self.speed
        else:
            self.desired *= self.speed
        steer = self.desired - self.direction
        STEERING_FORCE = 0.5
        if steer.length() > STEERING_FORCE:
            steer.scale_to_length(STEERING_FORCE)
        return steer
