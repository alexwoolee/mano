# Writing Good Quality Python 101
## Docstring vs In-line Comments
Comments are a non-negotiable feature in most languages that developers must use to maintain good quality and documentation. In python there are main ways to write comments: docstrings, in-lines. 

### Docstring 
The first method you could use is a docstring, shorthand for documentation string. As the name suggests, docstrings are used to document larger projects, especially when there's a plethora of functions in your files. The syntax is """...""" 
and it must be the very first thing in your function block. Python will officially recognize them and assign them to the object's __doc__ attribute. Note that docstrings are also useful if you simply want to write multiline comments and is the preferred choice to do so.

### In-line Comments
In-line comments on the otherhand is quite simple. If you want step-by-step explanation or document individual lines of code, in-line will be the best choice here. To utilize in-line comments, simply use the # symbol followed by your comment.
