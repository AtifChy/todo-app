from setuptools import setup

setup(
    name='todo-app',
    version='1.0.0',
    license='Apache-2.0',
    install_requires=[
        'prompt_toolkit>=3.0',
    ],
    entry_points={
        'console_scripts': [
            'todo=todo_app.todo:main',
        ],
    },
    python_requires='>=3.7',
)
