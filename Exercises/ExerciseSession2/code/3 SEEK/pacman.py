from random import uniform
import pygame
from constants import PACMAN, RED, STOP, UP, DOWN, LEFT, RIGHT, YELLOW
from vector import Vector2


class Pacman(object):
    def __init__(self, screen):
        self.name = PACMAN
        self.position = pygame.math.Vector2(200, 400)
        self.directions = {
            STOP: pygame.math.Vector2(),
            UP: pygame.math.Vector2(0, -1),
            DOWN: pygame.math.Vector2(0, 1),
            LEFT: pygame.math.Vector2(-1, 0),
            RIGHT: pygame.math.Vector2(1, 0),
        }
        self.speed = 10
        self.radius = 10
        self.color = YELLOW

        self.velocity = pygame.math.Vector2(self.speed, 0).rotate(uniform(0, 360))
        self.acceleration = Vector2()
        self.screen = screen

    def update(self, dt):
        self.acceleration = self.seek(pygame.mouse.get_pos())
        self.velocity += self.acceleration
        if self.velocity.length() > self.speed:
            self.velocity.scale_to_length(self.speed)
        self.position += self.velocity

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
        # normalize == make length 1
        # unit vectors are usually used for representing direction
        # and we can scale it to whatever the velocity is

    def seek(self, target: tuple[int, int]):
        self.desired_velocity = (target - self.position).normalize() * self.speed
        steer = self.desired_velocity - self.velocity
        STEERING_FORCE = 0.5
        if steer.length() > STEERING_FORCE:
            steer.scale_to_length(STEERING_FORCE)
        return steer

    def draw_vectors(self):
        scale = 25
        # vel vector
        pygame.draw.line(
            self.screen,
            YELLOW,
            self.position,
            (self.position + self.velocity * scale),
            5,
        )
        # desired
        pygame.draw.line(
            self.screen,
            RED,
            self.position,
            (self.position + self.desired_velocity * scale),
            5,
        )
