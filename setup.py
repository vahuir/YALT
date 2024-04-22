from setuptools import setup, find_namespace_packages

setup(
    version="0.1",
    name="YALT",
    description="Telegram Notifier executes bash commands and monitors them.",
    author="Vicent Ahuir",
    author_email="viahes@dsic.upv.es",
    packages=find_namespace_packages("src"),
    package_dir={"": "src"},
    package_data={
        "yalt.static": [
            "css/*.css",
            "js/*.js",
            "img/*.png",
            "img/*.svg",
            "img/*.jpg"
        ],
        "yalt.templates": ["*.html"]
    } ,
    entry_points={"console_scripts": [
        "yalt = yalt.cli:run"]},
    install_requires=[
        "Flask==3.0.3", "pywebview==5.0.5", "pyyaml==6.0.1"
    ],
    python_requires=">=3.8.0",
)

