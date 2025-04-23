import datetime
import shlex

from prompt_toolkit.completion import Completer, Completion

from todo_app.constants import (
    ALIAS_COMMANDS,
    COMMANDS,
    DATE_FORMAT,
    DATETIME_FORMAT,
    LIST_FILTERS,
    LIST_SORTS
)
from todo_app.enums import PRIORITY_VALUES

# --- Completer Class ---


class TodoCompleter(Completer):
    def __init__(self, todo_app_instance):
        self.app = todo_app_instance
        self.task_ids = {task.id[:8] for task in self.app.tasks}
        self.full_task_ids = {task.id for task in self.app.tasks}

    def update_task_ids(self):
        self.task_ids = {task.id[:8] for task in self.app.tasks}
        self.full_task_ids = {task.id for task in self.app.tasks}

    def get_completions(self, document, complete_event):
        self.update_task_ids()

        text_before_cursor = document.text_before_cursor
        try:
            words = shlex.split(text_before_cursor)
            if text_before_cursor.endswith(' '):
                words.append('')
        except ValueError:
            words = text_before_cursor.split()

        word_count = len(words)
        current_word = words[-1] if word_count > 0 and not text_before_cursor.endswith(
            ' ') else ""

        # Always offer --help for any command
        # if current_word.startswith('-'):
        #     yield Completion("--help", start_position=-len(current_word), display_meta='Help')

        # 1. Complete Command Name
        if word_count <= 1 and not text_before_cursor.endswith(' '):
            for cmd in COMMANDS:
                if cmd.startswith(current_word):
                    yield Completion(cmd, start_position=-len(current_word), display_meta='Command')
            return

        command = words[0].lower() if word_count > 0 else ""
        command = ALIAS_COMMANDS.get(command, command)

        # 2. Complete Task IDs
        if command in ['done', 'undone', 'toggle', 'del', 'edit'] and \
                word_count == 2 and not text_before_cursor.endswith(' '):
            if current_word.startswith('-'):
                yield Completion("--help", start_position=-len(current_word), display_meta='Help')
                return

            # 2a. complete task ID for done, undone, toggle, del
            for task_id_prefix in self.task_ids:
                if task_id_prefix.startswith(current_word):
                    full_id_match = [
                        fid for fid in self.full_task_ids if fid.startswith(task_id_prefix)]
                    meta_desc = "Task ID"
                    if len(full_id_match) == 1:
                        task = self.app._find_task_by_id(full_id_match[0])
                        if task:
                            meta_desc = task.description[:40] + (
                                '...' if len(task.description) > 40 else '')
                    yield Completion(
                        task_id_prefix, start_position=-len(current_word), display_meta=meta_desc
                    )
            return

        # 3. Complete Arguments for 'list'
        if command == 'list':
            used = set(words[1:])
            flags = ['--sort=', '--reverse', '-r', '--help', '-h']

            # 3a. suggest filter values
            if not current_word.startswith('-'):
                val = current_word.split('=', 1)[-1]
                for opt in LIST_FILTERS:
                    if opt.startswith(val):
                        yield Completion(opt, start_position=-len(val), display_meta='Filter')
            # 3b. suggest sort values
            elif current_word.startswith('--sort='):
                val = current_word.split('=', 1)[-1]
                for opt in LIST_SORTS:
                    if opt.startswith(val):
                        yield Completion(opt, start_position=-len(val), display_meta='Sort Key')
            # 3c. flag name completion
            elif current_word.startswith('--'):
                for f in flags:
                    name = f.rstrip('=') if f.endswith('=') else f
                    if name.startswith(current_word) and name not in used:
                        yield Completion(
                            name, start_position=-len(current_word), display_meta='Flag'
                        )
            elif current_word.startswith('-'):
                for f in flags:
                    if f.startswith('--'):
                        continue
                    name = f.rstrip('=') if f.endswith('=') else f
                    if name.startswith(current_word) and name not in used:
                        yield Completion(
                            name, start_position=-len(current_word), display_meta='Flag'
                        )
            return

        # 4. Complete Arguments for 'add' and 'edit'
        if command in ['add', 'edit']:
            # after 'edit ' we complete ID, then flags
            idx = word_count - 1
            # 4a. complete task ID for edit
            if command == 'edit' and idx == 1 and not text_before_cursor.endswith(' '):
                for tid in self.task_ids:
                    if tid.startswith(current_word):
                        yield Completion(tid, start_position=-len(current_word), display_meta='ID')
                return

            # 4b. suggest priority values
            if words[-1].startswith('--priority='):
                val = current_word.split('=', 1)[-1]
                for p in PRIORITY_VALUES:
                    if p.startswith(val):
                        yield Completion(p, start_position=-len(val), display_meta='Priority')
                return

            # 4c. suggest due date values
            if words[-1].startswith('--due='):
                val = current_word.split('=', 1)[-1]
                for fmt in [DATE_FORMAT, DATETIME_FORMAT]:
                    today_str = datetime.datetime.now().strftime(fmt)
                    quoted = f'"{today_str}"'
                    yield Completion(quoted, start_position=-len(val), display_meta='Date')
                return

            # 4d. flags for both add and edit
            used = {w.split('=')[0] for w in words[1:] if w.startswith('--')}
            base_defs = ['--priority=', '--due=', '--help']
            flag_defs = (['--desc='] if command == 'edit' else []) + base_defs
            if current_word.startswith('-'):
                for f in flag_defs:
                    name = f.rstrip('=')
                    if name.startswith(current_word) and name not in used:
                        yield Completion(
                            name, start_position=-len(current_word), display_meta='Flag'
                        )
                return

            return

# --- Command Line Interface ---
