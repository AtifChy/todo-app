DATA_FILE = "~/todo_tasks.json"
HISTORY_FILE = "~/.todo_app_history"

DATETIME_FORMAT = "%Y-%m-%d %I:%M%p"
DATE_FORMAT = "%Y-%m-%d"

COMMANDS_ALIASES = {
    'add': 'a',
    'list': 'ls',
    'toggle': 't',
    'edit': 'e',
    'del': 'rm',
    'help': '?',
    'clear': 'cls',
    'exit': 'q'
}

COMMANDS = list(COMMANDS_ALIASES.keys()) + \
    [alias for alias in COMMANDS_ALIASES.values()]
ALIAS_COMMANDS = {
    alias: cmd for cmd, alias in COMMANDS_ALIASES.items()
}

LIST_FILTERS = [
    'all',
    'pending',
    'completed',
    'due_today',
    'overdue',
    'priority:high',
    'priority:medium',
    'priority:low',
    'priority:none'
]
LIST_SORTS = ['priority', 'due_date', 'description']
