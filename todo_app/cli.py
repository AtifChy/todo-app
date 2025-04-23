import argparse
import shlex

from rich_argparse import RawTextRichHelpFormatter

from todo_app.constants import COMMANDS_ALIASES, LIST_FILTERS, LIST_SORTS
from todo_app.enums import PRIORITY_VALUES


def build_parser():
    RawTextRichHelpFormatter.styles['argparse.groups'] = "yellow"

    parser = argparse.ArgumentParser(
        prog='todo',
        description='To-Do App CLI',
        epilog=(
            'Examples:\n'
            '  add "Finish report" --priority=high\n'
            '  list --filter=pending --sort=due_date\n'
            '  add --help\n'
            '\n'
            'Tip: use the --key=value form to get tab‑completion for both flags and their values.\n'
            '      e.g. --filter=pending, --sort=due_date, --priority=high\n'
        ),
        formatter_class=RawTextRichHelpFormatter,
        add_help=False
    )
    subparsers = parser.add_subparsers(dest='command')

    # add
    p = subparsers.add_parser(
        'add',
        aliases=[COMMANDS_ALIASES['add']],
        help='Add a new task',
        formatter_class=parser.formatter_class
    )
    p.add_argument('description', help='Task description')
    p.add_argument('--priority', choices=PRIORITY_VALUES,
                   default='none', help='Task priority')
    p.add_argument('--due', default=None,
                   help='Due date (YYYY-MM-DD or YYYY-MM-DD HH:MM AM/PM)')

    # list
    p = subparsers.add_parser(
        'list',
        aliases=[COMMANDS_ALIASES['list']],
        help='List tasks',
        formatter_class=parser.formatter_class
    )
    p.add_argument(
        'filters',
        choices=LIST_FILTERS,
        nargs='*',
        help='Filter tasks (default: all)'
    )
    p.add_argument('--sort', choices=LIST_SORTS, default='priority')
    p.add_argument('-r', '--reverse',  action='store_true')

    # toggle / del
    for cmd in ('toggle', 'del'):
        p = subparsers.add_parser(
            cmd,
            aliases=[COMMANDS_ALIASES[cmd]],
            help=f'{cmd.capitalize()} a task'
        )
        p.add_argument('id', help='Task ID prefix')

    # edit
    p = subparsers.add_parser(
        'edit',
        aliases=[COMMANDS_ALIASES['edit']],
        help='Edit a task',
        formatter_class=parser.formatter_class
    )
    p.add_argument('id', help='Task ID prefix')
    p.add_argument('--desc', help='New description')
    p.add_argument('--priority', choices=PRIORITY_VALUES, help='New priority')
    p.add_argument('--due', help='New due date or "none" to clear')

    # clear
    subparsers.add_parser(
        'clear',
        aliases=[COMMANDS_ALIASES['clear']],
        help='Clear the screen',
        formatter_class=parser.formatter_class
    )

    # help
    subparsers.add_parser(
        'help',
        aliases=[COMMANDS_ALIASES['help']],
        help='Show this help message',
        formatter_class=parser.formatter_class
    )

    # exit
    subparsers.add_parser(
        'exit',
        aliases=[COMMANDS_ALIASES['exit']],
        help='Exit the application',
        formatter_class=parser.formatter_class
    )

    return parser


def parse_input(parser, input_str):
    try:
        # Use shlex to split the input string into arguments
        parts = shlex.split(input_str)
        if not parts:
            return None
        # Parse the arguments using argparse
        args = parser.parse_args(parts)
        return args
    except argparse.ArgumentError as e:
        # Argument definitions or mutual‐exclusion errors
        print(f"Argument Error: {e}")
        return None
    except SystemExit as e:
        # argparse uses SystemExit(code) for --help (code==0) or errors (>0).
        if getattr(e, "code", 1) != 0:
            print(f"Error parsing input (exit code {e.code})")
        # on code==0 (--help) we let the built‐in help text stand
        return None
    except Exception as e:
        # Handle unexpected errors
        print(f"Unexpected error: {e}")  # e.g. shlex.split failure
        return None
