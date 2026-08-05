"""
utils/display.py

Functions for displaying formatted output.
"""

from tabulate import tabulate


def print_title(title):

    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def print_table(data):

    table = [[k, v] for k, v in data.items()]

    print(
        tabulate(
            table,
            headers=["Property", "Value"],
            tablefmt="grid"
        )
    )