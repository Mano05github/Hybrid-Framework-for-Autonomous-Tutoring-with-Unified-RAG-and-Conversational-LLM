# Python Basics: Variables and Data Types

## Introduction to Variables

In Python, a variable is a named location in memory that stores a value. Think of it as a labeled box where you can put different things.

### Creating Variables

Python uses dynamic typing, which means you don't need to declare the type of a variable explicitly. The type is inferred from the value you assign.

```python
# Integer variable
age = 25

# String variable
name = "Alice"

# Float variable
height = 5.8

# Boolean variable
is_student = True
```

### Variable Naming Rules

1. Variable names must start with a letter or underscore (_)
2. Can contain letters, numbers, and underscores
3. Case-sensitive (age and Age are different variables)
4. Cannot use Python keywords (like if, for, while, etc.)

**Good variable names:**
- student_name
- total_score
- is_valid

**Bad variable names:**
- 1st_name (starts with number)
- student-name (contains hyphen)
- for (Python keyword)

## Data Types

Python has several built-in data types:

### 1. Numeric Types

**Integer (int):** Whole numbers without decimal points
```python
count = 10
negative = -5
large_number = 1_000_000  # Underscores for readability
```

**Float:** Numbers with decimal points
```python
pi = 3.14159
temperature = -12.5
scientific = 1.5e-4  # Scientific notation
```

**Complex:** Numbers with real and imaginary parts
```python
z = 3 + 4j
```

### 2. String (str)

Strings are sequences of characters enclosed in quotes.

```python
# Single quotes
message = 'Hello, World!'

# Double quotes
greeting = "Welcome to Python"

# Triple quotes for multi-line strings
paragraph = """This is a
multi-line
string"""
```

**String Operations:**
```python
# Concatenation
full_name = "John" + " " + "Doe"

# Repetition
stars = "*" * 10  # **********

# Indexing (0-based)
first_char = message[0]  # 'H'

# Slicing
substring = message[0:5]  # 'Hello'
```

### 3. Boolean (bool)

Boolean values represent True or False.

```python
is_raining = False
has_permission = True

# Boolean operations
result = True and False  # False
result = True or False   # True
result = not True        # False
```

### 4. None Type

None represents the absence of a value.

```python
result = None
```

## Type Conversion

You can convert between types using built-in functions:

```python
# String to integer
age = int("25")  # 25

# Integer to string
age_str = str(25)  # "25"

# String to float
price = float("19.99")  # 19.99

# Integer to float
decimal = float(10)  # 10.0
```

## Checking Types

Use the `type()` function to check a variable's type:

```python
x = 42
print(type(x))  # <class 'int'>

y = "Hello"
print(type(y))  # <class 'str'>
```

## Common Pitfalls

### 1. Division Behavior
```python
# Float division (always returns float)
result = 10 / 3  # 3.3333...

# Integer division (floor division)
result = 10 // 3  # 3

# Modulo (remainder)
result = 10 % 3  # 1
```

### 2. String Immutability
Strings cannot be changed after creation:
```python
text = "Hello"
# text[0] = "h"  # ERROR! Strings are immutable

# Instead, create a new string
text = "h" + text[1:]  # "hello"
```

### 3. Type Mixing
Be careful when mixing types:
```python
# This works (implicit conversion)
result = 5 + 2.5  # 7.5 (int + float = float)

# This doesn't work
# result = "5" + 2  # ERROR! Can't add string and int

# Solution: explicit conversion
result = int("5") + 2  # 7
```

## Quick Check Questions

1. What is the difference between `=` and `==`?
   - `=` is assignment (storing a value)
   - `==` is comparison (checking equality)

2. What will `type(3.0)` return?
   - `<class 'float'>` (even though it looks like an integer)

3. Is `student_name` a valid variable name?
   - Yes! It follows all naming rules.

## Practice Exercise

Try creating variables for a student profile:
```python
student_name = "Emma Watson"
student_age = 20
student_gpa = 3.85
is_enrolled = True
graduation_year = None  # Not yet determined
```

Remember: Variables are the foundation of programming. Understanding data types helps you write correct and efficient code!
