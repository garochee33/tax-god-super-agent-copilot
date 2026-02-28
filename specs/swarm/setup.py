from setuptools import setup, find_packages

setup(
    name="agent_swarm",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.7",
        "tomli>=2.0; python_version < '3.11'",
        "rich>=13.7",
        "requests>=2.31",
    ],
    entry_points={"console_scripts": ["agent-swarm=swarm.cli:main"]},
)
