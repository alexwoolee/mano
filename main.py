# 1. Standard Library
import sqlite3
from typing import Any
from datetime import date, time

# 2. Third-party (Rich, Textual)
from rich.text import Text
from rich.rule import Rule
from rich.panel import Panel 
from rich.columns import Columns
from rich.style import Style
from rich.align import Align
from textual.app import App, ComposeResult
from textual.containers import Container, Grid, Vertical, Center
from textual.screen import Screen
from textual.validation import ValidationResult, Validator
from textual.widgets import Button, Label, Header, Input, Static, RichLog

# 3. Local
import art

COMMANDS = {
    "/help", "/add", "/list", "/clear", "/quit", "/timer", "/q"
}

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def setup_database(name: str, age: int) -> None:
    """Setup user info table and data."""
    with sqlite3.connect("user.db") as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user (
                user_id INTEGER PRIMARY KEY, 
                name TEXT, 
                age INT, 
                new_user BOOLEAN)
            """
        )
        cursor.execute(
            "INSERT INTO user (name, age, new_user) VALUES (?, ?, ?)",
            (name, age, False),
        )
        # Setup skills table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS skills (
                skill_id INTEGER PRIMARY KEY, 
                name TEXT, 
                start_date DATE DEFAULT CURRENT_DATE, 
                start_time TIME DEFAULT CURRENT_TIMESTAMP, 
                total_days INTEGER DEFAULT 0)
            """
        )
        # Setup skills statistics table
        cursor.execute("CREATE TABLE IF NOT EXISTS skills_stats (skill_id INTEGER)")
        # Setup sessions table
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS sessions (
                skill TEXT, 
                date DATE, 
                start_time TIME, 
                duration TIMESTAMP)
            """
        )
        # Commit changes
        connection.commit()
        

def load_user_table(connection: sqlite3.Connection) -> tuple[str, bool] | None:
    """Loads all the data from the user table."""
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT name, new_user FROM user LIMIT 1")
    except sqlite3.OperationalError:
        return None
    row = cursor.fetchone()
    if row:
        user_name = row[0]
        new_user = row[1]
        return user_name, bool(new_user)
    return None


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def add_skill_command(connection: sqlite3.Connection, name: str) -> None:
    """Adds a command to the database and interface"""
    cursor = connection.cursor()
    cursor.execute("INSERT INTO SKILLS (name) VALUES (?)", (name,))
    connection.commit()


def remove_skill_command(connection: sqlite3.Connection, skill_id: int) -> None:
    cursor = connection.cursor()
    query = "DELETE FROM SKILLS WHERE SKILL_ID = ?"
    cursor.execute(query, (skill_id,))


def time_skill_command(connection: sqlite3.Connection, skill_id: int) -> None:
    """Times the skill and adds the data to stats and sessions table"""
    # On function called, get the current timestamp 
    
    # Using python's time library
    # Output live timer in terminal
    # Get cool animated spinner
    
    # On function exit, get the final timestamp
    # Get the difference 
    # Store the difference in sessions
    pass


def list_skills_command(self, connection: sqlite3.Connection) -> None:
    """List all the skills the user has"""
    cursor = connection.cursor()
    query = "SELECT name FROM skills"    
    cursor.execute(query)
    
    skills = cursor.fetchall()   
    
    output = []           
    
    # for each row in rows, place in panel, and print each skill
    log = self.query_one("#output", RichLog)
        
    log_feed = ""
        
    for skill in skills: 
        log_feed += format_skill_output(skill)
        
    log.write(Panel(f"{log_feed}"))
    
def format_skill_output(skill: str) -> str: 
    return f"{skill}\n"


def help_command(log: RichLog, help_information: str) -> None:
    """Displays help information in the TUI"""
    log.write(help_information)


def quit_command(self) -> None:
    """Exits the app"""
    self.app.exit()


# ---------------------------------------------------------------------------
# Utils/Helpers
# ---------------------------------------------------------------------------

def prepare_data_for_add_skill(user_input: object) -> object:
    """Handles user input into an deliverable object for adding skills"""
    pass


def draw_art(art_grid: list[list[str]]) -> str:
    """Draws ASCII art"""
    result = []
    for row in art_grid:
        line = "".join(row)
        result.append(line)

    return "\n".join(result)


def is_valid_command(command: str) -> bool:
    """Helper function to validate a command"""
    if not command:
        return False
    base_command = command.split(" ", maxsplit=1)[0]
    return base_command in COMMANDS


# ---------------------------------------------------------------------------
# Command handling
# ---------------------------------------------------------------------------

class CommandHandler:
    def parse_command(self, command: str) -> dict[str, Any]:
        command = command.strip()
        if not command:
            return self.create_result(1, "error", "[red]No command entered.[/red]")
        
        cmd = command.split()[0] if command.split() else command
        if cmd in COMMANDS:
            result = {"status": 1, "command": "dummy", "message": "dummy"}
            if cmd == "/quit" or cmd == "/q":
                result = self.create_result(0, "quit", "[blue]•[/blue] [orange]exiting...[/orange]")
            elif cmd == "/help":
                # Append help info to Static
                result = self.create_result(
                    0, "help", "[blue]•[/blue] [green]printing help...[/green]"
                )
            elif cmd == "/clear":
                result = self.create_result(
                    0, "clear", "[blue]•[/blue] [green]clearing log...[/green]"
                )
            elif cmd == "/add": 
                result = self.create_result(
                    0, "add", "[blue]•[/blue] [yellow]adding skill...[/yellow]"
                ) 
            elif cmd == "/list":
                result = self.create_result(
                    0, "list", "[blue]•[/blue] [pink]listing skills...[/pink]"
                ) 
            elif cmd == "/timer":
                result = self.create_result( 
                    0, "timer", "[blue]•[/blue] [purple]starting timer...[/purple]"
                )
            return result

        else:
            # Append error msg to Static
            result = self.create_result(
                1, "error", "[red]error occured: command faulty[/red]"
            )
            return result

    def create_result(self, status: int, command: str, message: str) -> dict[str, Any]:
        return {"status": status, "command": command, "message": message}


class ValidateCommand(Validator):
    """Validate commands"""
    
    def validate(self, value: str) -> ValidationResult:
        command = value.split()[0] if value.split() else value
        if is_valid_command(command):
            return self.success()
        else:
            return self.failure("Not a valid command")


# ---------------------------------------------------------------------------
# Screens
# ---------------------------------------------------------------------------

class WelcomeScreen(Screen):
    """Welcome screen shown only to new users"""

    def compose(self) -> ComposeResult:
        with Container(id="welcome-screen"):
            with Vertical(name="Components of Welcome Screen", id="welcome-interface"):
                with Center():
                    yield Label("Welcome to Mano", id="welcome-title")
                with Center():
                    yield Input(
                        placeholder="Username",
                        type="text",
                        classes="user-input",
                        id="name-input",
                    )
                with Center():
                    yield Input(
                        placeholder="Age",
                        type="integer",
                        classes="user-input",
                        id="age-input",
                    )
                with Center():
                    yield Button(
                        label="Submit",
                        variant="default",
                        name="New User Submit Button",
                        id="submit-button",
                        disabled=False,
                    )
                with Center():
                    yield Static("", id="error")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        name_input = self.query_one("#name-input", Input)
        age_input = self.query_one("#age-input", Input)
        error_msg = self.query_one("#error", Static)

        name = name_input.value.rstrip()
        age = age_input.value

        if name and age:
            age = int(age)

            # Setup database personal database for user
            setup_database(name, age)

            self.app.user_name = name # type: ignore

            # Switch from Welcome to Main Screen
            self.app.switch_screen(MainScreen())
        else:
            error_msg.update("Please enter a valid input!")


class MainScreen(Screen):
    """The main screen the users see"""

    def __init__(self):
        # Call the parent class constructor to initalize its variables
        super().__init__()
        self.command_handler = CommandHandler()
        # Let MainScreen act as source of truth for commands

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="main-screen"):
            with Container(id="command-history"):
                yield RichLog(
                    id="output",
                    auto_scroll=True,
                )

            yield Input(
                placeholder="Type @ to mention skills, / for commands",
                classes="input-text",
                id="input",
                max_length=256,
                validate_on=["submitted"],
                validators=[ValidateCommand()],
            )

    def on_input_changed(self, event: Input.Changed) -> None:
        """o.i.c. -> reacts to typing (i.e. UI feedback only)"""
        log = self.query_one("#output", RichLog)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """o.i.s. -> does things (command parsing, execution)"""
        log = self.query_one("#output", RichLog)

        if event.value:
            parsed_command = self.command_handler.parse_command(event.value)
            status = parsed_command["status"]
            command = parsed_command["command"]
            message = parsed_command["message"]

            output_text = f"\n> {event.value}\n{parsed_command['message']}"

            log.write(Text.from_markup(output_text))

            if command == "quit":
                quit_command(self)
            elif command == "clear":
                log.clear()
            elif command == "help":
                log.write(Rule(title="A list of all possible commands", align="center"))
                help_command(log, f"/add <skill_name> -- adds a skill\nlist -- lists all your skills\n/quit -- quit the app\nclear -- clear the terminalk")
                log.write(Rule())
            elif command == "add": 
                with sqlite3.connect("user.db") as connection: 
                    arg_list = event.value.split(" ", maxsplit=1)
                    # Ensure that a parameter was provided
                    skill_name = arg_list[1]
                    add_skill_command(connection, skill_name)
            elif command == "list": 
                with sqlite3.connect("user.db") as connection: 
                    list_skills_command(self, connection)
            elif command == "timer": 
                with sqlite3.connect("user.db") as connection: 
                    # TODO
                    # time_skill_command
                    pass
        else:
            log.write(Text.from_markup(f"\n❯[red]No command entered.[/red]"))

        event.input.clear()

        """
        Input submition flow: 
            1. User presses Enter
            2. Validator checks the command entered 
            (Done when defining the Input widget)
            3. If command valid -> handler parses it 
            4. Handler returns something
            5. Output panel displays result
        """

    def on_mount(self) -> None:
        self.title = "Mano"
        self.sub_title = "Road to 万"

        current_app: Any = self.app
        user_name = current_app.user_name
        
        log = self.query_one("#output", RichLog)
        
        panel = Panel(f"Mano v0.0.1!\nTrack your skills to 10,000. Be diligent.", border_style="magenta")
        log.write(Align(panel, align="center", vertical="middle"))
                

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

class CommandLine(App):
    """Control manager for what screen is shown"""
    CSS_PATH = "styles.tcss"

    def on_mount(self) -> None:
        self.user_name = "Kepo"
        self.new_user = True

        with sqlite3.connect("user.db") as connection:
            user = load_user_table(connection)

        if user:
            self.user_name, self.new_user = user

        if self.new_user:
            self.push_screen(WelcomeScreen())
        else:
            self.push_screen(MainScreen())


app = CommandLine()
if __name__ == "__main__":
    """Run the app!"""
    app.run()
