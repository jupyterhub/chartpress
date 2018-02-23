import sys
from setuptools import setup
from setuptools.command.bdist_egg import bdist_egg

with open('chartpress.py') as f:
    for line in f:
        if line.startswith('__version__'):
            __version__ = eval(line.split('=', 1)[1])
            break


class bdist_egg_disabled(bdist_egg):
    """Disabled version of bdist_egg

    Prevents setup.py install from performing setuptools' default easy_install,
    which it should never ever do.
    """

    def run(self):
        sys.exit(
            "Aborting implicit building of eggs."
            " Use `pip install .` to install from source."
        )


cmdclass = {
    'bdist_egg': bdist_egg if 'bdist_egg' in sys.argv else bdist_egg_disabled,
}

setup(
    name='chartpress',
    version=__version__,
    py_modules=['chartpress'],
    cmdclass=cmdclass,
    entry_points={
        'console_scripts': [
            'chartpress = chartpress:main',
        ],
    },
    description="ChartPress: render and publish helm charts and images",
    author="Jupyter Development Team",
    author_email="jupyter@googlegroups.com",
    url="https://github.com/jupyterhub/chartpress",
    license="BSD",
    platforms="Linux, Mac OS X",
    keywords=['helm', 'kubernetes'],
    python_requires=">=3.4",
    install_requires=[
        'ruamel.yaml>=0.15',
    ],
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
)
