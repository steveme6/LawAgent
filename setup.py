from setuptools import setup, find_packages

setup(
    name="lawagent_packets",
    version="0.1.0",
    packages=['app', 'config'],   # 自动发现包
    author="steveme6",
    author_email="development.email@example.com",
    description="mcp_packet",
    python_requires=">=3.12",
)