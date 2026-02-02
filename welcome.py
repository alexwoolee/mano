from console import console, prompt
from typing import List
import art


def welcome_new(name: str, age: int) -> None:
    welcome_new_msg()


def welcome_new_msg() -> None:
    print_empty_line(1)
    console.print(
        """[bright_cyan]Welcome to PekoProgres![/bright_cyan] [bright_black]v0.1.0[/bright_black]"""
    )

    print_divider("ceiling")
    draw_art(art.DOG_SCENE)
    print_divider("floor")

    print_empty_line(1)
    console.print("Let's get started.")
    print_empty_line(1)

    console.print("[bold]Type what you go by[/bold]")
    console.print("[bright_black]To change this later, run /name[/bright_black]")
    print_empty_line(1)

    name = prompt.ask("Enter your [bold cyan]username[/]")
    print(f"Glad to see you {name}")


def print_divider(type: str) -> None:
    # Ceiling divider
    if type == "ceiling":
        print("\u28c0" * 50)
    # Floor divider
    elif type == "floor":
        print("\u2809" * 50)
    else:
        print("(!) Please enter a valid type")


def print_empty_line(count: int) -> None:
    console.print("\n" * (count - 1))


def draw_art(art: List[List[str]]) -> None:
    for row in range(len(art)):
        for col in range(len(art[row])):
            print(art[row][col], end="")
        print_empty_line(1)


if __name__ == "__main__":
    welcome_new("Kepo", 20)
