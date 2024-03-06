from random import uniform
import pygame
from ghost import Ghost
from vector import Vector2
from constants import (
    PACMAN,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    STOP,
    UP,
    DOWN,
    LEFT,
    RIGHT,
    YELLOW,
)


class Pacman(object):
    def __init__(self, screen: pygame.Surface, ghost: Ghost):
        self.name = PACMAN
        self.position = pygame.math.Vector2(200, 400)
        self.directions = {
            STOP: pygame.math.Vector2(),
            UP: pygame.math.Vector2(0, -1),
            DOWN: pygame.math.Vector2(0, 1),
            LEFT: pygame.math.Vector2(-1, 0),
            RIGHT: pygame.math.Vector2(1, 0),
        }
        self.direction = STOP
        self.speed = 10
        self.radius = 10
        self.color = YELLOW

        self.velocity = pygame.math.Vector2(self.speed, 0).rotate(uniform(0, 360))
        self.acceleration = Vector2()
        self.screen = screen
        self.ghost = ghost

    def update(self, dt):
        self.velocity = self.ghost.velocity
        self.acceleration = self.ghost.acceleration
        if self.position.x > SCREEN_WIDTH:
            self.position.x = 0
        if self.position.x < 0:
            self.position.x = SCREEN_WIDTH
        if self.position.y > SCREEN_HEIGHT:
            self.position.y = 0
        if self.position.y < 0:
            self.position.y = SCREEN_HEIGHT

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
        mouse_position = pygame.mouse.get_pos()
        mouse_position = (mouse_position[0] + 1, mouse_position[1] + 1)
        self.acceleration = (mouse_position - self.position).normalize() * 0.2
        # normalize == make length 1
        # unit vectors are usually used for representing direction
        # and we can scale it to whatever the acceleration is

    def seek(self, target: tuple[int, int]):
        self.desired_velocity = (target - self.position).normalize() * self.speed
        steer = self.desired_velocity - self.velocity
        STEERING_FORCE = 0.5
        if steer.length() > STEERING_FORCE:
            steer.scale_to_length(STEERING_FORCE)
        return steer

    def seek_and_arrive(self, target):
        APPROACH_RADIUS = 50
        self.desired_velocity = target - self.position
        distance = (
            self.desired_velocity.length()
        )  # we get the distance before normalizing the desired
        self.desired_velocity.normalize_ip()  # ip = in place
        if distance < APPROACH_RADIUS:
            self.desired_velocity *= distance / APPROACH_RADIUS * self.speed
        else:
            self.desired_velocity *= self.speed
        steer = self.desired_velocity - self.velocity
        STEERING_FORCE = 0.5
        if steer.length() > STEERING_FORCE:
            steer.scale_to_length(STEERING_FORCE)
        return steer

    def draw_vectors(self):
        scale = 25
        # APPROACH_RADIUS = 50
        # vel vector
        pygame.draw.line(
            self.screen,
            YELLOW,
            self.position,
            (self.position + self.velocity * scale),
            5,
        )
        # # desired
        # pygame.draw.line(self.screen,
        #                 RED,
        #                 self.position,
        #                 (self.position + self.desired * scale),
        #                 5)
        # # approach radius
        # pygame.draw.circle(self.screen, WHITE, pygame.mouse.get_pos(), APPROACH_RADIUS, 1)
