import time
import sys
import keyboard
import typer


def stopwatch() -> None:
    # Start stopwatch
    start_time = time.monotonic()
    print("Press X to stop the stopwatch")

    while True:
        # Stop the stopwatch
        end_time = time.monotonic()

        # Calculate the elapsed time
        elapsed_time = end_time - start_time

        time_display = f"Elapsed time: {elapsed_time:.2f} seconds"

        display_stopwatch_terminal(time_display)

        if keyboard.is_pressed("x"):
            print("\nStopwatch stopped.")
            break


def display_stopwatch_terminal(time_display: string) -> None:
    sys.stdout.write("\r" + time_display)
    sys.stdout.flush()

    time.sleep(0.01)


if __name__ == "__main__":
    stopwatch()
