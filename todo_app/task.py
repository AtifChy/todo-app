import datetime
import uuid

from todo_app.enums import Priority


class Task:
    def __init__(
            self,
            id,
            description,
            completed=False,
            priority=Priority.NONE,
            due_date=None,
            created_at=None
    ):
        self.id = id
        self.description = description
        self.completed = completed
        self.priority = priority
        self.due_date = due_date
        self.created_at = created_at or datetime.datetime.now().isoformat()

    @classmethod
    def from_dict(cls, data):
        priority_str = data.get('priority', 'none')
        priority_enum = Priority.from_string(priority_str)
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            description=data.get('description'),
            completed=data.get('completed', False),
            priority=priority_enum,
            due_date=data.get('due_date'),
            created_at=data.get('created_at')
        )

    def to_dict(self):
        return {
            'id': self.id,
            'description': self.description,
            'completed': self.completed,
            'priority': str(self.priority),
            'due_date': self.due_date,
            'created_at': self.created_at
        }
