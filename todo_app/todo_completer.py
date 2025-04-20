import datetime
import shlex

from prompt_toolkit.completion import Completer, Completion

from todo_app.constants import COMMANDS, DATE_FORMAT, DATETIME_FORMAT, EDIT_ADD_KEYWORDS, LIST_FILTERS, LIST_SORTS
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
        self.update_task_ids()  # Ensure task IDs are fresh

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

        # 1. Complete Command Name
        if word_count <= 1 and not text_before_cursor.endswith(' '):
            for cmd in COMMANDS:
                if cmd.startswith(current_word):
                    yield Completion(cmd, start_position=-len(current_word))
            return

        command = words[0].lower() if word_count > 0 else ""

        # 2. Complete Task IDs
        if command in ['done', 'undone', 'toggle', 'del', 'edit'] and word_count == 2 and not text_before_cursor.endswith(' '):
            for task_id_prefix in self.task_ids:
                if task_id_prefix.startswith(current_word):
                    full_id_match = [
                        fid for fid in self.full_task_ids if fid.startswith(task_id_prefix)]
                    meta_desc = "Task ID"
                    if len(full_id_match) == 1:
                        task = self.app._find_task_by_id(
                            full_id_match[0])  # Use find method
                        if task:
                            meta_desc = task.description[:40] + \
                                ('...' if len(task.description) > 40 else '')
                    yield Completion(task_id_prefix, start_position=-len(current_word), display_meta=meta_desc)
            return

        # 3. Complete Arguments for 'list'
        if command == 'list':
            has_sort_keyword = any(w.startswith("sort=") for w in words[:-1])
            has_filter_keyword = any(
                # Basic check
                f in words[1:-1] for f in LIST_FILTERS if f != 'all')

            # Suggest filters or 'sort=' keyword
            if word_count == 2:
                if current_word.startswith("sort="):
                    typed = current_word[len("sort="):]
                    for key in LIST_SORTS:
                        if key.startswith(typed):
                            yield Completion(key, start_position=0, display_meta='Sort Key')
                else:
                    if not has_sort_keyword:
                        for filt in LIST_FILTERS:
                            if filt.startswith(current_word):
                                yield Completion(filt, start_position=-len(current_word), display_meta='Filter')
                    if not has_sort_keyword and "sort=".startswith(current_word):
                        yield Completion("sort=", start_position=-len(current_word), display_meta='Sort key')

            # Suggest sort key values
            # elif word_count >= 2 and words[-1].startswith("sort="):
            #     typed = current_word[len("sort="):]
            #     for key in LIST_SORTS:
            #         if key.startswith(typed):
            #             yield Completion(f"sort={key}", start_position=-len(current_word), display_meta='Sort Key')

            # Suggest 'sort=' keyword after a filter
            elif word_count == 3 and text_before_cursor.endswith(' ') and not has_sort_keyword:
                is_filter_likely = words[1] in LIST_FILTERS or words[1].startswith(
                    "priority:")
                if is_filter_likely:
                    yield Completion("sort=", start_position=0, display_meta='Sort key')

            # Suggest filters after 'sort=' keyword
            elif word_count == 3 and text_before_cursor.endswith(' ') and has_sort_keyword and not has_filter_keyword:
                for filt in LIST_FILTERS:
                    yield Completion(filt, start_position=0, display_meta='Filter')

            return

        # 4. Complete Arguments for 'add' and 'edit'
        if command in ['add', 'edit']:
            existing_keywords = {word.split('=')[0]
                                 for word in words[1:] if '=' in word}

            # Suggest keywords
            if text_before_cursor.endswith(' '):
                for keyword in EDIT_ADD_KEYWORDS:
                    kw_base = keyword.split('=')[0]
                    # Avoid suggesting 'desc=' if it's already present for 'edit'/'add' implicitly
                    if kw_base not in existing_keywords:
                        yield Completion(keyword, start_position=0, display_meta='Keyword')

            # Suggest keyword values
            elif '=' in current_word:
                keyword_part, value_part = current_word.split('=', 1)
                if keyword_part == 'priority':
                    for prio in PRIORITY_VALUES:
                        if prio.startswith(value_part):
                            yield Completion(prio, start_position=-len(value_part), display_meta='Priority')
                elif keyword_part == 'due':
                    if 'none'.startswith(value_part):
                        yield Completion('none', start_position=-len(value_part), display_meta='Remove due date')
                    # Add suggestions for today's date and current datetime
                    today_str = datetime.date.today().strftime(DATE_FORMAT)
                    quoted_today = f'"{today_str}"'
                    if today_str.startswith(value_part):
                        yield Completion(quoted_today, start_position=-len(value_part), display_meta='Today\'s date')
                    now_str = datetime.datetime.now().strftime(DATETIME_FORMAT)
                    quoted_now = f'"{now_str}"'
                    if now_str.startswith(value_part):
                        yield Completion(quoted_now, start_position=-len(value_part), display_meta='Current datetime')

            # Suggest keywords if typing a word
            elif not any(current_word.startswith(kw) for kw in existing_keywords):
                for keyword in EDIT_ADD_KEYWORDS:
                    kw_base = keyword.split('=')[0]
                    if kw_base not in existing_keywords and keyword.startswith(current_word):
                        yield Completion(keyword, start_position=-len(current_word), display_meta='Keyword')
            return

# --- Command Line Interface ---
