from setuptools import setup, find_packages

setup(
    name='mmmaya',
    version='0.1.dev0',
    description='Mark Media\'s Maya tools',
    url='http://github.com/mmpipeline/mmmaya',
    
    packages=find_packages(exclude=['build*', 'tests*']),
    include_package_data=True,
    
    author='Mike Boers',
    author_email='mmmaya@mikeboers.com',
    license='BSD-3',
    
    entry_points={
        'console_scripts': '''
            maya = mmmaya.launcher:main
            mayapy = mmmaya.launcher:main_python
            Render = mmmaya.launcher:main_render
        ''',
        'appinit.maya': '''
            100_mm_dirmap = mmmaya.dirmap:setup
        ''',
        'appinit.maya.gui': '''
            500_mm_shelves = mmmaya.shelves:setup_gui
        ''',
    },
    
    metatools_scripts={
        'mmmaya-inspect': {
            'entrypoint': 'mmmaya.inspect:main',
            'interpreter': 'mayapy',
        }
    },

    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    
)
