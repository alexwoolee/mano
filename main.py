import art
import sqlite3
from typing import List, Any
from datetime import date, time
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Container, Grid, Vertical, Center
from textual.screen import Screen
from textual.validation import ValidationResult, Validator
from textual.widgets import Welcome, Button, Label, Header, Input, Static, RichLog

        
# Helpers
def prepare_data_for_add_skill(user_input: object) -> object:
    pass

def load_user_table(connection: sqlite3.Connection) -> tuple[str, bool] | None:
    cursor = connection.cursor() 
    cursor.execute("SELECT name, new_user FROM user LIMIT 1")
    row = cursor.fetchone()
    if row: 
        user_name = row[0]
        new_user = row[1]
        return user_name, bool(new_user)
    return None


def add_skill_command(connection: sqlite3.Connection, skill_id: int, name: str, start_date: date, start_time: time, total_days: int) -> None:
    """Adds a command to the database and interface"""
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO SKILLS (SKILL_ID, NAME, START_DATE, START_TIME, TOTAL_DAYS) VALUES (?, ?, ?, ?, ?)",
        (skill_id, name, start_date, start_time, total_days),
    )
    

def remove_skill_command(connection: sqlite3.Connection, skill_id: int) -> None: 
    cursor = connection.cursor()
    cursor.execute( 
        "DELETE FROM SKILLS (SKILL_ID, START_DATE DAYS)"
    )
    pass
    
   
def time_skill_command(connection: sqlite3.Connection, skill_id: int) -> None: 
    """Times the skill and adds the data to stats and sessions table"""
    pass 


def list_skills_command(connection: sqlite3.Connection) -> None: 
    """List all the skills the user has"""
    pass


def help_command(log: RichLog, help_information: str) -> None: 
    """Displays help information in the TUI"""
    log.write(help_information)
    

def quit_command(self) -> None: 
    """Exits the app"""
    self.app.exit()
    

def setup_database(name: str, age: int) -> None:
    """Setup user info table and data"""
    with sqlite3.connect("user.db") as connection:
        cursor = connection.cursor()

        cursor.execute(
            "CREATE TABLE IF NOT EXISTS user (user_id INTEGER PRIMARY KEY, name TEXT, age INT, new_user BOOLEAN)"
        )
        cursor.execute(
            "INSERT INTO user (name, age, new_user) VALUES (?, ?, ?)",
            (name, age, False),
        )

        # Setup skills table
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS skills (skill_id INTEGER PRIMARY KEY, name TEXT, start_date DATE, start_time TIME, total_days INTEGER)"
        )

        # Setup skills statistics table
        cursor.execute("CREATE TABLE IF NOT EXISTS skills_stats (skill_id INTEGER)")

        # Setup sessions table
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS sessions (skill TEXT, date DATE, start_time TIME, duration TIMESTAMP)"
        )

        # Commit changes
        connection.commit()
        

class WelcomeScreen(Screen):
    """Welcome screen shown only to new users"""

    def compose(self) -> ComposeResult:
        with Container(id="welcome-screen"):
            with Vertical(name="Components of Welcome Screen", id="welcome-interface"):
                with Center():
                    yield Label("Welcome to PekoFocus", id="welcome-title")
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
            print(name, age)

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
        self.command_list = [
            "/help",
            "/add",
            "/list",
            "/clear",
            "/quit",
            "/timer", 
        ]

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="main-screen"):
            with Grid(id="grid"):
                yield Static(
                    id="static1",
                    classes="panel",
                )
                yield Static(
                    "N/A",
                    id="static3",
                    classes="panel",
                )

            with Container(id="command-history"):
                yield RichLog(
                    id="output",
                    auto_scroll=True,
                )

            yield Input(
                placeholder="Enter a command",
                classes="input-text",
                id="input",
                max_length=256,
                validate_on=["submitted"],
                validators=[ValidateCommand(self.command_list)],
            )

    def on_input_changed(self, event: Input.Changed) -> None:
        """o.i.c. -> reacts to typing (i.e. UI feedback only)"""
        log = self.query_one("#output", RichLog)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """o.i.s. -> does things (command parsing, execution)"""
        log = self.query_one("#output", RichLog)

        if event.value:
            parsed_command = self.command_handler.parse_command(
                event.value, self.command_list
            )
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
                help_command(log, f" /add \n /list \n /quit \n /clear")
        else:
            log.write(Text.from_markup(f"\n>[red]No command entered.[/red]"))

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
        self.sub_title = "One second towards 万"
        
        current_app: Any = self.app
        user_name = current_app.user_name
        welcome_static_widget = self.query_one(
            "#static1", Static
        )  # figure out why .value isn't needed
        welcome_static_widget.update(
            f"{draw_art(art.BASIC_SCENE)}\n\nWelcome {user_name}!"
        )


def draw_art(art_grid: List[List[str]]) -> str:
    result = []
    for row in art_grid:
        line = "".join(row)
        result.append(line)

    return "\n".join(result)


class CommandHandler:
    def parse_command(self, command: str, command_list: List[str]) -> dict[str, Any]:
        if command in command_list:
            result = {"status": 1, "command": "dummy", "message": "dummy"}
            if command == "/quit" or command == "/q":
                result = self.create_result(0, "quit", "[orange]exiting...[/orange]")
            elif command == "/help":
                """Append help info to Static"""
                result = self.create_result(
                    0, "help", "[green]printing help...[/green]"
                )
            elif command == "/clear":
                result = self.create_result(
                    0, "clear", "[green]clearing log...[/green]"
                )
            return result

        else:
            """Append error msg to Static"""
            result = self.create_result(
                1, "error", "[red]error occured: command faulty[/red]"
            )
            return result

    def create_result(self, status: int, command: str, message: str) -> dict[str, Any]:
        return {"status": status, "command": command, "message": message}


class ValidateCommand(Validator):
    def __init__(self, command_list):
        self.command_list = command_list

    def validate(self, value: str) -> ValidationResult:
        if is_valid_command(value, self.command_list):
            return self.success()
        else:
            return self.failure("Not a valid command")


def is_valid_command(command: str, command_list: List[str]) -> bool:
    """Helper function to validate a command"""
    return command in command_list


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
