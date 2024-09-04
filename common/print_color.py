from colorama import Fore, Style
from pprint import pformat

def print_green(content: str):
    print(Fore.GREEN + pformat(content))
    print(Style.RESET_ALL, end="")


def print_yellow(content: str):
    print(Fore.YELLOW + pformat(content))
    print(Style.RESET_ALL, end="")


def print_red(content: str):
    print(Fore.RED + pformat(content))
    print(Style.RESET_ALL, end="")


def print_blue(content: str):
    print(Fore.BLUE + pformat(content))
    print(Style.RESET_ALL, end="")
