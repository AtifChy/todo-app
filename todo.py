import json
import os
import datetime
import uuid
import shlex
import traceback

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import print_formatted_text as print_ft

from constants import DATA_FILE
from enums import Priority
from task import Task
from helpers import format_due_date_display, get_datetime_from_iso, parse_datetime_flexible
from todo_completer import TodoCompleter


class TodoApp:
    def __init__(self, data_file=DATA_FILE):
        self.data_file = data_file
        self.tasks = self._load_tasks()

    def _load_tasks(self):
        """Loads tasks from the JSON data file."""
        if not os.path.exists(self.data_file):
            return []
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                return [Task.from_dict(d) for d in data]
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading tasks: {e}. Starting with an empty list.")
            return []

    def _save_tasks(self):
        """Saves the current list of tasks to the JSON data file."""
        try:
            with open(self.data_file, 'w') as f:
                json.dump([t.to_dict() for t in self.tasks], f, indent=4)
        except IOError as e:
            print(f"Error saving tasks: {e}")

    def _find_task_by_id_or_index(self, identifier):
        """Finds a task by its unique ID (prioritized) or index (less reliable)."""
        # Try finding by full ID
        for task in self.tasks:
            if task.id == identifier:
                return task

        # Try finding by partial ID (e.g., first few chars)
        possible_matches = [
            task for task in self.tasks if task.id.startswith(identifier)]
        if len(possible_matches) == 1:
            return possible_matches[0]
        elif len(possible_matches) > 1:
            print(
                f"Ambiguous identifier '{identifier}'. Multiple tasks match:")
            for t in possible_matches:
                print(f"  - {t.id[:8]}... ({t.description})")
            return None  # Indicate ambiguity

        # Avoid index-based lookup as it's unreliable without stable list view
        print(f"Error: Task with identifier '{identifier}' not found.")
        return None

    def add_task(self, description, priority="none", due_date_str=None):
        """Adds a new task. Parses date/time."""
        if not description:
            print("Error: Task description cannot be empty.")
            return

        priority_enum = Priority.from_string(priority)
        if str(priority_enum) != priority.lower() and priority.lower() != "none":
            print(
                f"Warning: Invalid priority '{priority}'. Setting to 'none'.")

        parsed_due_datetime = parse_datetime_flexible(due_date_str)
        due_date_iso = None
        if due_date_str and parsed_due_datetime is None:
            print(
                f"Warning: Invalid date/time format '{due_date_str}'. Use YYYY-MM-DD or YYYY-MM-DD HH:MM. Due date not set.")
        elif parsed_due_datetime:
            due_date_iso = parsed_due_datetime.isoformat()  # Store as ISO string

        task = Task(
            id=str(uuid.uuid4()),
            description=description,
            completed=False,
            priority=priority_enum,
            due_date=due_date_iso,
            created_at=datetime.datetime.now().isoformat()
        )
        self.tasks.append(task)
        self._save_tasks()
        print(f"Task added: '{description}' (ID: {task.id[:8]}...)")

    def list_tasks(self, filter_by="all", sort_by="priority"):
        """Lists tasks, with optional filtering and sorting."""
        filtered_tasks = self.tasks
        now = datetime.datetime.now()  # Get current time for filtering

        # --- Filtering ---
        original_filter = filter_by
        filter_by = filter_by.lower()

        if filter_by == "pending":
            filtered_tasks = [t for t in self.tasks if not t.completed]
        elif filter_by == "completed":
            filtered_tasks = [t for t in self.tasks if t.completed]
        elif filter_by.startswith("priority:"):
            priority_str = filter_by.split(":", 1)[1].lower()
            priority_enum = Priority.from_string(priority_str)
            if str(priority_enum) == priority_str:
                filtered_tasks = [
                    t for t in self.tasks if t.priority == priority_str]
            else:
                print(f"Invalid priority filter: {priority_str}. Showing all.")
                original_filter = "all"
                filtered_tasks = self.tasks
        elif filter_by == "due_today":
            today = now.date()
            filtered_tasks = [
                t for t in self.tasks
                if not t.completed and
                t.due_date and
                get_datetime_from_iso(
                    t.due_date).date() == today  # Compare dates
            ]
        elif filter_by == "overdue":
            filtered_tasks = [
                t for t in self.tasks
                if not t.completed and
                t.due_date and
                # Compare full datetime
                get_datetime_from_iso(t.due_date) < now
            ]
        elif filter_by != "all":
            print(f"Invalid filter: {original_filter}. Showing all tasks.")
            original_filter = "all"
            filtered_tasks = self.tasks

        # --- Sorting ---
        sort_by = sort_by.lower()
        key_func = None

        if sort_by == "priority":
            def key_func(t): return (
                -t.priority,
                get_datetime_from_iso(t.due_date),
                t.description.lower()
            )
        elif sort_by == "due_date":
            def key_func(t): return (
                get_datetime_from_iso(t.due_date),
                -t.priority,
                t.description.lower()
            )
        elif sort_by == "description":
            def key_func(t): return t.description.lower()
        else:
            print(f"Invalid sort key: {sort_by}. Using default (priority).")
            sort_by = "priority"

            # Assign default key func again
            def key_func(t): return (
                -t.priority,
                get_datetime_from_iso(t.due_date),
                t.description.lower()
            )

        try:
            sorted_tasks = sorted(filtered_tasks, key=key_func)
        except Exception as e:
            print(f"Error during sorting: {e}")
            traceback.print_exc()  # Print full error
            sorted_tasks = filtered_tasks

        # --- Display ---
        if not sorted_tasks:
            print("No tasks to show for the current filter.")
            return

        # Colorized header block
        print_ft(HTML('\n<u><b><ansiyellow>--- Your Tasks ---</ansiyellow></b></u>'))
        print_ft(HTML(
            f"<ansicyan>Filter:</ansicyan> {original_filter} <ansigray>|</ansigray> <ansicyan>Sort:</ansicyan> {sort_by}"))
        print_ft(HTML(f"<ansigray>{'-'*80}</ansigray>"))
        header = HTML(
            '<b>'
            f'<ansiyellow>{"ID":<10}</ansiyellow>'
            f'<ansigreen>{"Status":<10}</ansigreen>'
            f'<ansimagenta>{"Priority":<12}</ansimagenta>'
            f'<ansiblue>{"Due Date/Time":<20}</ansiblue>'
            f'Description'
            '</b>'
        )
        print_ft(header)
        print_ft(HTML(f"<ansigray>{'-'*80}</ansigray>"))

        for i, task in enumerate(sorted_tasks):
            status = "[X]" if task.completed else "[ ]"
            # Format and color each field
            short_id = task.id[:8]
            priority_display = str(task.priority).capitalize()
            due_display = format_due_date_display(task.due_date)
            status_color = "ansigreen" if task.completed else "ansired"
            row = HTML(
                f"<ansiyellow>{short_id:<10}</ansiyellow>"
                f"<{status_color}>{status:<10}</{status_color}>"
                f"<ansimagenta>{priority_display:<12}</ansimagenta>"
                f"<ansiblue>{due_display:<20}</ansiblue>"
                f"{task.description}"
            )
            print_ft(row)

        print_ft(HTML(f"<ansigray>{'-'*80}</ansigray>"))
        print_ft(
            HTML(f"<ansiblue>Total tasks shown:</ansiblue> <b>{len(sorted_tasks)}</b>"))

    def toggle_complete(self, identifier):
        """Marks a task as complete or incomplete."""
        task = self._find_task_by_id_or_index(identifier)
        if task:
            task.completed = not task.completed
            self._save_tasks()
            status = "completed" if task.completed else "pending"
            print(f"Task '{task.description}' marked as {status}.")

    def delete_task(self, identifier):
        """Deletes a task."""
        task_to_delete = self._find_task_by_id_or_index(identifier)
        if task_to_delete:
            desc = task_to_delete.description
            confirm = input(
                f"Are you sure you want to delete task '{desc}' (ID: {task_to_delete.id[:8]})? (y/N): ")
            if confirm.lower() == 'y':
                self.tasks.remove(task_to_delete)
                self._save_tasks()
                print(f"Task '{desc}' deleted.")
            else:
                print("Deletion cancelled.")

    def edit_task(self, identifier, new_description=None, new_priority=None, new_due_date=None):
        """Edits properties of an existing task. Parses date/time."""
        task = self._find_task_by_id_or_index(identifier)
        if task:
            updated = False
            if new_description is not None:
                task.description = new_description
                print(f"Description updated for task ID {task.id[:8]}.")
                updated = True
            if new_priority is not None:
                priority_enum = Priority.from_string(new_priority)
                if str(priority_enum) == new_priority.lower() or new_priority.lower() == "none":
                    task.priority = priority_enum
                    print(
                        f"Priority updated to '{new_priority}' for task ID {task.id[:8]}.")
                    updated = True
                else:
                    print(
                        f"Error: Invalid priority '{new_priority}'. No change made.")

            if new_due_date is not None:
                if new_due_date.lower() == 'none':
                    task.due_date = None
                    print(f"Due date removed for task ID {task.id[:8]}.")
                    updated = True
                else:
                    parsed_due_datetime = parse_datetime_flexible(new_due_date)
                    if parsed_due_datetime:
                        task.due_date = parsed_due_datetime.isoformat()
                        print(
                            f"Due date updated to '{format_due_date_display(task.due_date)}' for task ID {task.id[:8]}.")
                        updated = True
                    else:
                        print(
                            f"Error: Invalid date/time format '{new_due_date}'. Use YYYY-MM-DD or YYYY-MM-DD HH:MM. No change made.")

            if updated:
                self._save_tasks()
            else:
                print("No valid changes specified for the task.")


def print_help():
    """Prints the help menu with colors and formatting."""
    print_ft(
        HTML('\n<u><b><ansiyellow>--- To-Do App Commands ---</ansiyellow></b></u>'))
    print_ft(HTML('  <ansicyan>add</ansicyan> '
                  '<b><i>&lt;description&gt;</i></b> '
                  '[<ansiyellow>priority=&lt;prio&gt;</ansiyellow>] '
                  '[<ansiyellow>due=&lt;date|datetime&gt;</ansiyellow>] '
                  '- Add a new task'))
    print_ft(HTML(
        '      <ansigreen>Priorities:</ansigreen> high, medium, low, none (default)'))
    print_ft(HTML('      <ansigreen>Due Format:</ansigreen> '
                  '\'YYYY-MM-DD\' or \'YYYY-MM-DD HH:MM AM/PM\''))
    print_ft(HTML('  <ansicyan>list</ansicyan> [<b>filter</b>] [<ansiyellow>sort=&lt;key&gt;</ansiyellow>] '
                  '- List tasks'))
    print_ft(HTML('      <ansigreen>Filters:</ansigreen> all (default), pending, completed, '
                  'priority:&lt;prio&gt;, due_today, overdue'))
    print_ft(HTML(
        '      <ansigreen>Sort Keys:</ansigreen> priority (default), due_date, description'))
    print_ft(HTML(
        '  <ansicyan>done</ansicyan> <b><i>&lt;task_id&gt;</i></b> - Mark task as completed'))
    print_ft(HTML(
        '  <ansicyan>undone</ansicyan> <b><i>&lt;task_id&gt;</i></b> - Mark task as pending'))
    print_ft(HTML(
        '  <ansicyan>toggle</ansicyan> <b><i>&lt;task_id&gt;</i></b> - Toggle task status'))
    print_ft(HTML('  <ansicyan>edit</ansicyan> <b><i>&lt;task_id&gt;</i></b> '
                  '[<ansiyellow>desc="&lt;new_desc&gt;"</ansiyellow>] '
                  '[<ansiyellow>priority=&lt;prio&gt;</ansiyellow>] '
                  '[<ansiyellow>due=&lt;date|datetime|none&gt;</ansiyellow>] '
                  '- Edit task'))
    print_ft(
        HTML('  <ansicyan>del</ansicyan> <b><i>&lt;task_id&gt;</i></b> - Delete a task'))
    print_ft(HTML('  <ansicyan>help</ansicyan> - Show this help message'))
    print_ft(HTML('  <ansicyan>exit</ansicyan> - Exit the application'))
    print_ft(
        HTML('<ansiblue>----------------------------------------------</ansiblue>\n'))
    print_ft(HTML(
        '<i>Hint:</i> Use <b><ansiblue>TAB</ansiblue></b> to autocomplete commands and arguments.'))


def parse_args(input_str):
    """Parses arguments using shlex for better quote handling."""
    try:
        # Use posix=False on Windows if paths with backslashes are arguments,
        # otherwise default (True) is usually fine. Keep default for now.
        parts = shlex.split(input_str)
    except ValueError as e:
        print(f"Warning: Input parsing issue (maybe unmatched quotes?): {e}")
        parts = input_str.split()  # Fallback

    args = {'command': None, 'params': [], 'kwargs': {}}
    if not parts:
        return args

    args['command'] = parts[0].lower()
    description_parts = []
    # Assume first non-kwarg part starts description *unless* it's an ID command
    is_description_mode = args['command'] in ['add']

    id_expected = args['command'] in [
        'edit', 'del', 'done', 'undone', 'toggle']
    id_captured = False

    for part in parts[1:]:
        is_kwarg = '=' in part and part.index(
            '=') > 0  # Basic check for key=value

        if is_kwarg:
            key, value = part.split('=', 1)
            args['kwargs'][key.lower()] = value  # Store kwarg
            is_description_mode = False  # Stop description mode if kwarg found

        elif id_expected and not id_captured:
            args['params'].append(part)  # Capture the ID
            id_captured = True
            if args['command'] == 'edit':  # For edit, things after ID could be description
                is_description_mode = True  # Re-enable description for edit *after* ID

        elif is_description_mode:
            description_parts.append(part)  # Collect description parts

        # Not ID, not kwarg, not description mode -> treat as positional param (e.g., list filter)
        else:
            # Only capture first positional for list filter
            if args['command'] == 'list' and not args['params']:
                args['params'].append(part)
            # Ignore extra positional args for most commands
            elif args['command'] not in ['add', 'edit']:
                print(
                    f"Warning: Ignoring extra argument '{part}' for {args['command']} command.")

    # Consolidate description if parts were collected and 'desc=' wasn't used
    if description_parts:
        if 'desc' not in args['kwargs']:
            args['kwargs']['desc'] = " ".join(description_parts)
        else:
            # If both positional desc and desc= provided, kwarg takes precedence
            print(
                "Warning: Both positional description and desc= provided. Using desc= value.")
            # The positional parts were already ignored due to is_description_mode=False

    return args


def main():
    app = TodoApp()
    history = FileHistory(os.path.expanduser('~/.todo_app_history'))
    session = PromptSession(history=history)
    todo_completer = TodoCompleter(app)

    print("Welcome to To-Do App!")
    print_help()

    while True:
        try:
            raw_input = session.prompt(
                HTML("<b>Todo&gt;</b> "),
                completer=todo_completer,
                complete_while_typing=True,
                refresh_interval=0.5
            )

            if not raw_input:
                continue

            parsed = parse_args(raw_input)
            command = parsed['command']
            params = parsed['params']
            kwargs = parsed['kwargs']

            if command == "exit":
                print("Exiting. Goodbye!")
                break
            elif command == "help":
                print_help()
            elif command == "clear":
                os.system('cls' if os.name == 'nt' else 'clear')
            elif command == "add":
                description = kwargs.get('desc')
                if not description:
                    print("Error: Description is required for adding a task.")
                    print_help()
                    continue
                priority = kwargs.get('priority', 'none')
                due_date = kwargs.get('due')  # String from input
                app.add_task(description, priority, due_date)
                todo_completer.update_task_ids()
            elif command == "list":
                filter_by = params[0] if params else "all"
                sort_by = kwargs.get('sort', 'priority')
                app.list_tasks(filter_by=filter_by, sort_by=sort_by)
            elif command in ("done", "undone", "toggle", "del", "edit"):
                if not params:
                    print(
                        f"Error: Task ID is required for command '{command}'.")
                    print_help()
                    continue
                identifier = params[0]

                # Pre-find task for commands that benefit from knowing if it exists first
                task_exists = app._find_task_by_id_or_index(identifier) if command in [
                    "done", "undone"] else True  # Assume exists for others initially

                if not task_exists and command in ["done", "undone"]:
                    # _find already prints error, just continue
                    continue

                if command == "done":
                    task = app._find_task_by_id_or_index(
                        identifier)  # Find again for status check
                    if task and not task.completed:
                        app.toggle_complete(identifier)
                    elif task:
                        print(
                            f"Task '{task.description}' is already marked as done.")
                elif command == "undone":
                    task = app._find_task_by_id_or_index(identifier)
                    if task and task.completed:
                        app.toggle_complete(identifier)
                    elif task:
                        print(
                            f"Task '{task.description}' is already marked as pending.")
                elif command == "toggle":
                    # Let toggle handle find/error
                    app.toggle_complete(identifier)
                elif command == "del":
                    # delete_task handles find/error/confirmation internally
                    original_tasks_count = len(app.tasks)
                    app.delete_task(identifier)
                    # Check if deletion likely succeeded
                    if len(app.tasks) < original_tasks_count:
                        todo_completer.update_task_ids()
                elif command == "edit":
                    new_desc = kwargs.get('desc')
                    new_prio = kwargs.get('priority')
                    new_due = kwargs.get('due')  # String from input or None
                    if new_desc is None and new_prio is None and new_due is None:
                        print(
                            "Error: Edit command requires at least one property to change (desc=, priority=, due=).")
                        print_help()
                        continue
                    # edit_task handles find/error internally
                    app.edit_task(identifier, new_description=new_desc,
                                  new_priority=new_prio, new_due_date=new_due)

            else:
                print(f"Error: Unknown command '{command}'")
                print_help()

        except KeyboardInterrupt:
            print("\nExiting due to interrupt.")
            break
        except EOFError:
            print("\nExiting.")
            break
        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}")
            traceback.print_exc()  # Print detail for debugging


if __name__ == "__main__":
    main()
