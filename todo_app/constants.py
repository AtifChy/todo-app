DATA_FILE = "~/todo_tasks.json"
HISTORY_FILE = "~/.todo_app_history"

DATETIME_FORMAT = "%Y-%m-%d %I:%M%p"
DATE_FORMAT = "%Y-%m-%d"

COMMANDS = ['add', 'list', 'done', 'undone',
            'toggle', 'edit', 'del', 'help', 'clear', 'exit']
LIST_FILTERS = ['all', 'pending', 'completed', 'priority:high',
                'priority:medium', 'priority:low', 'priority:none', 'due_today', 'overdue']
LIST_SORTS = ['priority', 'due_date', 'description']
EDIT_ADD_KEYWORDS = ['priority=', 'due=', 'desc=']
