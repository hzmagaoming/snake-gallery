import pygame

from config import WINDOW_HEIGHT, WINDOW_WIDTH
from game import Game


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("EMERGENCY RUN")

    game = Game(screen)
    game.run()
    pygame.quit()


if __name__ == "__main__":
    main()
