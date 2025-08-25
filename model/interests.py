from dataclasses import dataclass

@dataclass
class Interests:
    """структура интересова пользователя"""
    movie: bool = False
    memes: bool = False
    music: bool = False
    just_talking: bool = False