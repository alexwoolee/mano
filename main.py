# Author: Alex W. Lee

# 1. Standard Library
import sqlite3
from typing import Any
from datetime import date, time, datetime

# 2. Third-party (Rich, Textual)
from rich import box
from rich.text import Text
from rich.rule import Rule
from rich.panel import Panel 
from rich.columns import Columns
from rich.style import Style
from rich.align import Align
from textual.binding import Binding
from textual.app import App, ComposeResult
from textual.containers import Container, Grid, Vertical, Center, Horizontal, VerticalScroll
from textual.reactive import reactive
from textual.screen import Screen
from textual.validation import ValidationResult, Validator
from textual.widgets import Button, Label, Header, Input, Footer, Static, RichLog
from textual.widget import Widget

# 3. Local
import art

COMMANDS = {
    "/help", "/add", "/list", "/clear", "/quit", "/q", "/timer", "/delete", 
}


def normalize_command_token(token: str) -> str:
    """Normalize command tokens so both 'add' and '/add' resolve to '/add'."""
    token = token.strip().lower()
    if not token:
        return token
    if token.startswith("/"):
        return token
    return f"/{token}"

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
                start_time TIME DEFAULT CURRENT_TIMESTAMP)
            """
        )
        # Setup skills statistics table
        cursor.execute("CREATE TABLE IF NOT EXISTS skills_stats (skill_id INTEGER)")
        # Setup sessions table
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS sessions (
                session_id INTEGER PRIMARY KEY,
                skill_id INTEGER, 
                date DATE DEFAULT CURRENT_DATE, 
                start_time DATETIME DEFAULT CURRENT_TIMESTAMP, 
                duration INTEGER,
                FOREIGN KEY(skill_id) REFERENCES skills(skill_id)
            )
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
        user_name, new_user = row
        return user_name, bool(new_user)
    return None


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def add_skill_command(connection: sqlite3.Connection, name: str) -> None:
    """Adds a command to the database and interface"""
    cursor = connection.cursor()
    name = name.strip().lower()
    cursor.execute("INSERT INTO SKILLS (name) VALUES (?)", (name,))
    connection.commit()


def remove_skill_command(connection: sqlite3.Connection, skill_name: str) -> bool:
    cursor = connection.cursor()
    skill_name = skill_name.strip().lower()
    query = "DELETE FROM SKILLS WHERE NAME = ?"
    cursor.execute(query, (skill_name,))
    connection.commit()
    return cursor.rowcount > 0


def time_skill_command(connection: sqlite3.Connection, skill_name: str, action: str, history: VerticalScroll) -> bool:
    """Times the skill and adds the data to stats and sessions table"""
    success = False
    # Function called, get the current timestamp 
    cursor = connection.cursor()
        
    cursor.execute(
        "SELECT skill_id FROM skills WHERE LOWER(name) = LOWER(?)", 
        (skill_name.strip().lower(),)
    )
    print(f"DEBUG skill_name='{skill_name}'")
    
    row = cursor.fetchone()
    
    if row is None:
        history.mount(Static("[#cba6f7]•[/#cba6f7] [#f38ba8]Error: this skill does not exist.[/#f38ba8]", classes="output-message"))
        return success

    skill_id = row[0]
        
    # action is start 
    if action == "start": 
        # Using datecursortime to track timer live
        # Output live timer in terminal
        # Get cool animated spinner
        match_query = "SELECT name, skill_id FROM skills WHERE name = ? AND skill_id = ?"
        cursor.execute(match_query, (skill_name, skill_id))
        cursor.execute("INSERT INTO sessions (skill_id) VALUES (?)" , (skill_id, ),)
        success = True 
        timer_widget = MyTimerBox(skill_name=skill_name, classes="message")
        timer_widget.start()
        history.mount(timer_widget)
    # action is stop
    elif action == "stop":
        # get the starting timestamp we obtained in action start
        # get the current timestamp
        # find the difference
        # store it as duration in sessions 
        
        # Find the most recent unfinished session, ensure only close unfinished sessions with IS NULL condition
        query = "SELECT start_time FROM sessions WHERE skill_id = ? AND duration IS NULL ORDER BY start_time DESC LIMIT 1"
        cursor.execute(query, (skill_id,))
        row = cursor.fetchone()
        if row is None:
            history.mount(Static("[#cba6f7]•[/#cba6f7] [#f38ba8]Error: no active session was found for that skill.[/#f38ba8]", classes="output-message"))
            return False

        start_time_string = row[0]
        start_time = datetime.fromisoformat(start_time_string)
        end_time = datetime.now()
        
        duration = int((end_time - start_time).total_seconds())
        
        update_query = "UPDATE sessions SET duration = ? WHERE start_time = ? AND skill_id = ?"
        cursor.execute(update_query, (duration, start_time, skill_id, ))
        connection.commit()
        success = True
    # invalid action
    else: 
        history.mount(Static("[#cba6f7]•[/#cba6f7] [#f38ba8]Error: please write a valid timer action.[/#f38ba8]", classes="output-message"))
        success = False
    
    return success

# NOTE
def list_skills_command(self, connection: sqlite3.Connection, history: VerticalScroll) -> None:
    """List all the skills the user has"""
    cursor = connection.cursor()
    query = "SELECT name FROM skills"    
    cursor.execute(query)
    
    skills = cursor.fetchall()   
    if not skills:
        empty_message = (
            "[bold #cba6f7]Skills[/bold #cba6f7]\n"
            "[dim]No skills yet.[/dim]\n"
            "[dim]Use[/dim] [bold]add reading[/bold] [dim]to get started.[/dim]"
        )
        history.mount(Static(empty_message, classes="output-message"))
        return

    styled_output = (
        "[bold #cba6f7]Skills[/bold #cba6f7]\n"
        f"[dim]{len(skills)} tracked[/dim]\n"
        "[dim]────────────────────────[/dim]\n"
        + "\n".join(format_skill_output(i, skill) for i, (skill,) in enumerate(skills, start=1))
    )
    history.mount(Static(styled_output, classes="output-message"))
    
     
def format_skill_output(index: int, skill: str) -> str: 
    return (
        f"[dim]{index:>2}.[/dim] "
        f"[bold #cdd6f4]{skill.title()}[/bold #cdd6f4]"
    )


def help_command(history: VerticalScroll) -> None:
    """Displays help information in the TUI"""
    command_width = 31
    help_lines = [
        ("add <skill>", "add a new skill"),
        ("delete <skill>", "remove a skill"),
        ("list", "view all tracked skills"),
        ("timer <skill> <start|stop>", "track session time"),
        ("clear", "clear command history"),
        ("quit", "exit Mano"),
    ]
    help_text = "[bold #cba6f7]Commands[/bold #cba6f7]\n[dim]Use slash commands in the input below.[/dim]\n\n"
    help_text += "\n".join(
        f"[#89dceb]{command:<{command_width}}[/#89dceb] [dim]{description}[/dim]"
        for command, description in help_lines
    )
    history.mount(Static(help_text, classes="output-message"))

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
    base_command = normalize_command_token(command.split(" ", maxsplit=1)[0])
    return base_command in COMMANDS


class WelcomeWidget(Static):
    """Animated welcome card with a blinking mascot."""

    blink_closed: reactive[bool] = reactive(False)

    def __init__(self, user_name: str, **kwargs: Any) -> None:
        super().__init__("", **kwargs)
        self.user_name = user_name
        self._blink_frame = 0
        self._blink_pattern = (False, False, False, True, False, False)

    def _build_ascii_art(self) -> str:
        eye_row = (
            "[medium_orchid1]██[/medium_orchid1][on #11111b] [/on #11111b]"
            "[thistle1]██[/thistle1][on #11111b]  [/on #11111b][light_pink3]██[/light_pink3]"
            "[on #11111b] [/on #11111b][light_cyan1]██[/light_cyan1]"
        )
        if self.blink_closed:
            eye_row = (
                "[medium_orchid1]██[/medium_orchid1][on #11111b] [/on #11111b]"
                "[#11111b]██[/#11111b][on #11111b]  [/on #11111b][#11111b]██[/#11111b]"
                "[on #11111b] [/on #11111b][light_cyan1]██[/light_cyan1]"
            )

        return (
            "[plum2]██████████[/plum2]\n"
            f"{eye_row}\n"
            "[medium_purple1]██████████[/medium_purple1]\n\n"
        )

    def _build_panel(self) -> Panel:
        brand = "[bold #bac2de]MANO[/bold #bac2de]\n"
        title = f"[bold #cdd6f4]Welcome back, [#f5c2e7]{self.user_name}[/#f5c2e7].[/bold #cdd6f4]\n"
        subtitle = (
            "[#a6adc8]Start with [#89b4fa]/help[/#89b4fa] or log your next session "
            "with [#cba6f7]/timer start[/#cba6f7].[/#a6adc8]"
        )
        content = Text.from_markup(brand + "\n" + self._build_ascii_art() + title + subtitle, justify="center")
        return Panel(
            content,
            border_style="#585b70",
            expand=False,
            padding=(1, 3),
            title="[bold #89b4fa]Mano[/bold #89b4fa]",
            subtitle="[#7f849c]v0.0.1[/#7f849c]",
            box=box.ROUNDED,
        )

    def watch_blink_closed(self, _: bool) -> None:
        self.update(self._build_panel())

    def _animate_blink(self) -> None:
        self._blink_frame = (self._blink_frame + 1) % len(self._blink_pattern)
        self.blink_closed = self._blink_pattern[self._blink_frame]

    def on_mount(self) -> None:
        self.update(self._build_panel())
        self.set_interval(0.35, self._animate_blink)

def print_welcome_message(self, user_name: str) -> None: 
    history = self.query_one("#command-history", VerticalScroll)
    history.mount(WelcomeWidget(user_name, classes="welcome-widget"))
    

# ---------------------------------------------------------------------------
# Command handling
# ---------------------------------------------------------------------------

class CommandHandler:
    def parse_command(self, command: str) -> dict[str, Any]:
        command = command.strip()
        if not command:
            return self.create_result(1, "error", "[#cba6f7]•[/#cba6f7] [#f38ba8]Error: no command entered.[/#f38ba8]")
        
        raw_cmd = command.split()[0] if command.split() else command
        cmd = normalize_command_token(raw_cmd)
        if cmd in COMMANDS:
            result = {"status": 1, "command": "dummy", "message": "dummy"}
            if cmd == "/quit" or cmd == "/q":
                result = self.create_result(0, "quit", "[#cba6f7]•[/#cba6f7] [#fab387]Exiting.[/#fab387]")
            elif cmd == "/help":
                # Append help info to Static
                result = self.create_result(
                    0, "help", "[#cba6f7]•[/#cba6f7] [#a6e3a1]Printing help.[/#a6e3a1]"
                )
            elif cmd == "/clear":
                result = self.create_result(
                    0, "clear", "[#cba6f7]•[/#cba6f7] [#a6e3a1]Clearing log.[/#a6e3a1]"
                )
            elif cmd == "/add": 
                result = self.create_result(
                    0, "add", "[#cba6f7]•[/#cba6f7] [#f9e2af]Adding skill.[/#f9e2af]"
                ) 
            elif cmd == "/delete":
                result = self.create_result( 
                    0, "delete", "[#cba6f7]•[/#cba6f7] [#94e2d5]Removing skill.[/#94e2d5]"
                )
            elif cmd == "/list":
                result = self.create_result(
                    0, "list", "[#cba6f7]•[/#cba6f7] [#a6e3a1]Listing skills.[/#a6e3a1]"
                ) 
            elif cmd == "/timer":
                result = self.create_result( 
                    0, "timer", "[#cba6f7]•[/#cba6f7] [#cba6f7]Timer command.[/#cba6f7]"
                )
            return result

        else:
            # Append error msg to Static
            result = self.create_result(
                1, "error", "[#cba6f7]•[/#cba6f7] [#f38ba8]Error: command faulty.[/#f38ba8]"
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
            return self.failure("Error: not a valid command.")


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
            error_msg.update("[#cba6f7]•[/#cba6f7] Error: please enter a valid input.")


class MainScreen(Screen):
    """Main screen that the users see."""
    COMMAND_HANDLERS = {
        "quit": "_handle_quit",
        "clear": "_handle_clear",
        "help": "_handle_help",
        "add": "_handle_help",
        "delete": "_handle_delete",
        "list": "_handle_list",
        "timer": "_handle_timer",
    }

    def __init__(self):
        # Call the parent class constructor to initalize its variables
        super().__init__()
        self.command_handler = CommandHandler()

    def compose(self) -> ComposeResult:
        # Main user interactable elements
        with Horizontal(): 
            with Container(id="main-section"):
                # 1: Area for logged commands and results
                with VerticalScroll(id="command-history"):
                    pass
                # 2: Box for users to provide us input
                yield Input(
                    placeholder="Type @ to mention skills, / for commands",
                    classes="input-text",
                    id="input",
                    max_length=256,
                    validate_on=["submitted"],
                    validators=[ValidateCommand()],
                )
                yield MyFooter(id="my-footer")
            yield Container(id="side-info-panel")


    def _handle_quit(self, input_value: str) -> None: 
        quit_command(self)
    
    def _handle_clear(self, input_value: str) -> None:
        pass
    

    def on_input_submitted(self, event: Input.Submitted) -> None:
        # Grab the VerticalScroll container        
        history = self.query_one("#command-history", VerticalScroll)
        
        if not event.value: 
            history.mount(Static("• Error: no command entered.", classes="error-message"))
            return
        
        # Mount the user's message
        user_msg = Static(event.value, classes="user-message")
        history.mount(user_msg)

        # Parse command and extract values
        parsed_command = self.command_handler.parse_command(event.value)
        command = parsed_command["command"]
        message = parsed_command["message"]
        
        # Mount the initial system response
        response_message = Static(parsed_command["message"], classes="system-message")
        history.mount(response_message)

        if command == "quit":
            quit_command(self)
            
        elif command == "clear":
            history.query("*").remove()

        elif command == "help":
            help_command(history)

        elif command in ["add", "delete", "list", "timer"]:
            with sqlite3.connect("user.db") as connection:
                arg_list = event.value.split(" ", maxsplit=1)

                if command == "delete" and len(arg_list) > 1:
                    # Ensure that a parameter was provided
                    skill_name = arg_list[1]
                    deleted = remove_skill_command(connection, skill_name)
                    if deleted:
                        history.mount(Static(f"• Removed skill: [bold]{skill_name.strip().lower()}[/bold].", classes="system-message"))
                    else:
                        history.mount(Static(f"• Error: skill not found: [bold]{skill_name.strip().lower()}[/bold].", classes="error-message"))

                elif command == "add" and len(arg_list) > 1:
                    # Ensure that a parameter was provided
                    skill_name = arg_list[1]
                    add_skill_command(connection, skill_name)
                    history.mount(Static(f"• Added skill: [bold]{skill_name.strip().lower()}[/bold].", classes="system-message"))

                elif command == "list":
                    list_skills_command(self, connection, history)

                elif command == "timer":
                    arg_list = event.value.split()

                    if len(arg_list) != 3:
                        history.mount(Static("• Error: usage: /timer <skill> <start|stop>.", classes="error-message"))
                    else:
                        _, skill_name, action = arg_list
                        time_skill_command(connection, skill_name, action, history)
        
        history.scroll_end(animate=False)
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
        current_app: Any = self.app
        user_name = current_app.user_name
    
        # Print welcome message in RichLog
        print_welcome_message(self, user_name)

        side_info_panel = self.query_one("#side-info-panel", Container)
        side_info_panel.mount(
            Static(
                "[bold #89b4fa]Quick Tips[/bold #89b4fa]\n"
                "[dim]Use /help to see commands.\n"
                "Track a skill with /timer <skill> <start|stop>.[/dim]",
                classes="output-message",
                id="side-info-content",
            )
        )

# --------------------------------------------------------------------------- 
# Footer 
# ---------------------------------------------------------------------------

class MyFooter(Footer): 
    BINDINGS = [
        Binding(key="q", action="quit", description="Quit the app"),
        Binding(key="question_mark", action="help", description="Show help screen", key_display="?")
    ]

# --------------------------------------------------------------------------- 
# Timer
# ---------------------------------------------------------------------------

class MyTimerBox(Vertical): 
    """Times each skill session and displays elapsed time."""
    # Holds the time for the specific session
    elapsed_time: reactive[int] = reactive(0)
    # Flag that tracks if the timer should run or not, controlled by start() and stop()
    running: bool = False
    skill_name: str = "Unknown"

    def __init__(self, skill_name: str = "Unknown", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.skill_name = skill_name
    
    def on_mount(self) -> None: 
        self.set_interval(1, self._tick)
    
    def _tick(self) -> None: 
        if (self.running):
            self.elapsed_time += 1
        
    def watch_elapsed_time(self, value: int) -> None: 
        minutes = value // 60
        seconds = value % 60 
        hours = minutes // 60
        self.query_one("#time-display", Static).update(f"Time: {hours:02}h:{minutes:02}m:{seconds:02}s")
    
    def start(self): 
        self.running = True
        try:
            self.query_one("#timer-status", Static).update("Status: running")
        except Exception:
            pass
        
    def stop(self):
        self.running = False
        try:
            self.query_one("#timer-status", Static).update("Status: stopped")
        except Exception:
            pass
        
    def reset(self):
        self.elapsed_time = 0
    
    def compose(self): 
        # to be displayed: skill name, timer, start/pause, stop, number of sessions for that skill, total time for that skill, most recent 5 sessions with dates duration, progress bar to 10,000 hours, 
        yield Static(f"Skill: {self.skill_name}", id="skill-name")
        yield Static("Time: 00:00", id="time-display")
        yield Static("Status: running", id="timer-status")
        
    
# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

class CommandLine(App):
    """Control manager for what screen is shown"""
    CSS_PATH = "styles.tcss"

    def on_mount(self) -> None:
        self.user_name = "Unknown"
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
