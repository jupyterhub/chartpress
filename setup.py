import sys
from setuptools import setup
from setuptools.command.bdist_egg import bdist_egg


class bdist_egg_disabled(bdist_egg):
    """Disabled version of bdist_egg

    Prevents setup.py install from performing setuptools' default easy_install,
    which it should never ever do.
    """

    def run(self):
        sys.exit(
            "Aborting implicit building of eggs."
            "Use `pip install .` to install from source."
        )


cmdclass = {
    'bdist_egg': bdist_egg if 'bdist_egg' in sys.argv else bdist_egg_disabled,
}

with open("README.md") as f:
    readme = f.read()

setup(
    name='chartpress',
    version='0.7.0',
    py_modules=['chartpress'],
    cmdclass=cmdclass,
    entry_points={
        'console_scripts': [
            'chartpress = chartpress:main',
        ],
    },
    description="ChartPress: render and publish helm charts and images",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Jupyter Development Team",
    author_email="jupyter@googlegroups.com",
    url="https://github.com/jupyterhub/chartpress",
    license="BSD",
    platforms="Linux, Mac OS X",
    keywords=['helm', 'kubernetes'],
    python_requires=">=3.6",
    install_requires=[
        'ruamel.yaml>=0.15',
        'docker>=3.2.0',
    ],
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
)
