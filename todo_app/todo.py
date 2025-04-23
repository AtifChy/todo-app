import json
import os
import datetime
import uuid
import traceback

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import print_formatted_text as print_ft

from todo_app.cli import build_parser, parse_input
from todo_app.constants import ALIAS_COMMANDS, DATA_FILE, HISTORY_FILE
from todo_app.enums import Priority
from todo_app.task import Task
from todo_app.helpers import format_due_date_display, get_datetime_from_iso, parse_datetime_flexible
from todo_app.todo_completer import TodoCompleter


class TodoApp:
    def __init__(self, data_file=DATA_FILE):
        self.data_file = os.path.expanduser(data_file)
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

    def _find_task_by_id(self, identifier):
        """Finds a task by its unique ID."""
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

    def list_tasks(self, filter_by=None, sort_by="priority", reverse=False):
        """Lists tasks, with optional filtering and sorting."""
        filters = filter_by or ['all']
        filtered_tasks = list(self.tasks)   # work on a copy

        now = datetime.datetime.now()
        original_filters = filters[:]
        for f in filters:
            key = f.lower()
            if key == "all":
                continue
            if key == "pending":
                filtered_tasks = [t for t in filtered_tasks if not t.completed]
            elif key == "completed":
                filtered_tasks = [t for t in filtered_tasks if t.completed]
            elif key.startswith("priority:"):
                priority_str = key.split(":", 1)[1].lower()
                priority_enum = Priority.from_string(priority_str)
                if str(priority_enum) == priority_str:
                    filtered_tasks = [
                        t for t in filtered_tasks if t.priority == priority_enum]
                else:
                    print(
                        f"Invalid priority filter: {priority_str}. Showing all.")
                    original_filters = ["all"]
                    filtered_tasks = list(self.tasks)
            elif key == "due_today":
                today = now.date()
                filtered_tasks = [
                    t for t in filtered_tasks
                    if not t.completed and
                    t.due_date and
                    get_datetime_from_iso(
                        t.due_date).date() == today  # Compare dates
                ]
            elif key == "overdue":
                filtered_tasks = [
                    t for t in filtered_tasks
                    if not t.completed and
                    t.due_date and
                    # Compare full datetime
                    get_datetime_from_iso(t.due_date) < now
                ]
            else:
                # unknown filter: warn once, but keep going
                print(f"Invalid filter: {f}. Ignored.")

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

        if reverse:
            sorted_tasks.reverse()

        filters_str = ', '.join(original_filters)

        # Colorized header block
        print_ft(HTML('\n<u><b><ansiyellow>--- Your Tasks ---</ansiyellow></b></u>'))
        print_ft(HTML(
            f"<ansicyan>Filter:</ansicyan> {filters_str} <ansigray>|</ansigray> <ansicyan>Sort:</ansicyan> {sort_by}"))
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

        for task in sorted_tasks:
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
        task = self._find_task_by_id(identifier)
        if task:
            task.completed = not task.completed
            self._save_tasks()
            status = "completed" if task.completed else "pending"
            print(f"Task '{task.description}' marked as {status}.")

    def delete_task(self, identifier):
        """Deletes a task."""
        task_to_delete = self._find_task_by_id(identifier)
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
        task = self._find_task_by_id(identifier)
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


def main():
    app = TodoApp()
    parser = build_parser()
    history = FileHistory(os.path.expanduser(HISTORY_FILE))
    session = PromptSession(history=history)
    todo_completer = TodoCompleter(app)

    print("Welcome to To-Do App!\n")
    print(parser.format_help())

    while True:
        try:
            raw_input = session.prompt(
                HTML('<b>Todo></b> '),
                completer=todo_completer,
                complete_while_typing=True,
                refresh_interval=0.5
            )

            if not raw_input:
                continue

            parsed_args = parse_input(parser, raw_input)
            if parsed_args is None:
                continue

            command = parsed_args.command
            command = ALIAS_COMMANDS.get(command, command)

            if command == "exit":
                print("Exiting. Goodbye!")
                break
            elif command == "help":
                print(parser.format_help())
            elif command == "clear":
                os.system('cls' if os.name == 'nt' else 'clear')
            elif command == "add":
                app.add_task(
                    parsed_args.description,
                    parsed_args.priority,
                    parsed_args.due
                )
                todo_completer.update_task_ids()
            elif command == "list":
                app.list_tasks(
                    filter_by=parsed_args.filters,
                    sort_by=parsed_args.sort,
                    reverse=parsed_args.reverse
                )
            elif command == "toggle":
                ident = parsed_args.id
                app.toggle_complete(ident)
            elif command == "del":
                before = len(app.tasks)
                app.delete_task(parsed_args.id)
                if len(app.tasks) < before:
                    todo_completer.update_task_ids()
            elif command == "edit":
                if not any((parsed_args.desc, parsed_args.priority, parsed_args.due)):
                    print("Error: Edit requires --desc, --priority or --due.")
                    print(parser.format_help())
                    continue
                app.edit_task(
                    parsed_args.id,
                    new_description=parsed_args.desc,
                    new_priority=parsed_args.priority,
                    new_due_date=parsed_args.due
                )
            else:
                print(f"Error: Unknown command '{command}'")
                print(parser.format_help())

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
