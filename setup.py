from setuptools import setup, find_packages

setup(
    name='mmmaya',
    version='0.1.dev0',
    description='Mark Media\'s Maya tools',
    url='http://github.com/mmpipeline/mmmaya',
    
    packages=find_packages(exclude=['build*', 'tests*']),
    
    author='Mike Boers',
    author_email='mmmaya@mikeboers.com',
    license='BSD-3',
    
    entry_points={
        'console_scripts': '''
            maya = mmmaya.launcher:main
        ''',
        'appinit.maya': '''
            100_mm_dirmap = mmmaya.dirmap:setup
        ''',
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
