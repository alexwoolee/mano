import typer
import sqlite3
import time
import sys
import welcome
from enum import Enum
from rich import print
from typing import Any

# Specify the DDL/query to create tables
create_skills_table_sql = """CREATE TABLE IF NOT EXISTS SKILLS ( 
                SKILL_ID TEXT,
                START_DATE TEXT,
                DAYS INTEGER)"""
skills_schema = """CREATE TABLE IF NOT EXISTS SESSIONS (
                SKILL_ID TEXT,
                SESSION_DATE TEXT,
                TIME REAL)"""

# Create a connection object to local db
with sqlite3.connect("sample.db") as database_connection:
    # Define a cursor object: allows you to traverse and manipulate results of SQL query row-by-row
    cursor = database_connection.cursor()

    # Pass query string to cursor's execute method
    cursor.execute(create_skills_table_sql)
    cursor.execute(skills_schema)

    # Iterate over the cursor's result set (list of tuples)
    for record in cursor:
        print("Hello world")
        print(record)
    # connection auto-closes here

app = typer.Typer()


def start_pekoprogress_app():
    database_connection = sqlite3.connect("sample.db")
    cursor = database_connection.cursor()

    while True:
        # Get command from user
        user_input = input(">>> ").strip()

        if user_input == "/exit":
            print("Bye!")
            break
        elif user_input.startswith("/skill add"):
            add_skill(cursor, user_input)
            # Save changes to db
            con.commit()
        elif user_input == "/help":
            print("Commands: /skill and <name>, /timer, /exit")
        else:
            print("Unknown command.")

    database_connection.close()


def add_skill(cursor: sqlite3.Cursor, user_input: str) -> None:
    cursor.execute(
        "INSERT INTO SKILLS (SKILL_ID, START_DATE DAYS) VALUES (?, ?, ?)",
        (user_input, start_date),
    )


if __name__ == "__main__":
    # typer.run(main)
    welcome.welcome_new("Alex", 20)
    start_pekoprogress_app()
