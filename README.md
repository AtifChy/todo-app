# Todo App

A simple, terminal-based to-do application written in Python. Track your tasks, set priorities, and manage due dates all from the command line with powerful tab-completion support.

## Features

- Add tasks with descriptions, priority levels (high, medium, low, none), and optional due dates.
- List tasks with filters (pending, completed, due_today, overdue) and sorting (priority, due_date, description).
- Mark tasks as done/undone or toggle status.
- Edit or delete tasks.
- Interactive prompt with syntax highlighting and tab completion.

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/AtifChy/todo-app.git
   cd todo-app
   ```

2. (Optional) Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate        # Linux/macOS
   .\.venv\Scripts\activate.bat     # Windows
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. (Optional) Install as a CLI tool:
   ```bash
   pip install .
   ```
   Then run with:
   ```bash
   todo
   ```

## Usage

Start the application:

```bash
todo
```

At the `Todo>` prompt, type `help` to see available commands.

## Contributing

Feel free to submit issues or pull requests. Please follow [PEP 8 style guidelines](https://peps.python.org/pep-0008/) and include tests for new features.
