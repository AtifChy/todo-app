from setuptools import setup

setup(
    name='todo-app',
    version='1.0.0',
    license='Apache-2.0',
    py_modules=[
        "todo",
        "constants",
        "helpers",
        "task",
        "enums",
        "todo_completer",
    ],
    install_requires=[
        'prompt_toolkit>=3.0',
    ],
    entry_points={
        'console_scripts': [
            'todo=todo:main',
        ],
    },
    python_requires='>=3.7',
)
