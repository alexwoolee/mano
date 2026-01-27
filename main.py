# Technologies I need to research on
# - Typer or Click library 
# - Rich library
# - Pandas library 
# - For visualization I'd recommend: Plotext 
# - For data storage I'm planning to use: SQLite

def getInput():
    user_input = input("Did you work on Japanese today? (yes/no) : ") 
    if user_input == "yes": 
        print("Good job!")
    else:
        print("You got this next time!")

getInput()
