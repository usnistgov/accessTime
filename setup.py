import setuptools

with open("README.md", "r",encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name="mcvqoe-accesstime",
    author="PSCR",
    author_email="PSCR@PSCR.gov",
    description="Measurement code for access time",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/usnistgov/accessTime",
    packages=setuptools.find_namespace_packages(include=['mcvqoe.*']),
    include_package_data=True,
    use_scm_version={'write_to' : 'mcvqoe/accesstime/version.py'},
    setup_requires=['setuptools_scm'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Public Domain",
        "Operating System :: OS Independent",
    ],
    license='NIST software License',
    install_requires=[
        'mcvqoe-nist>=0.4',
        'abcmrt-nist>=0.1.3',
    ],
    entry_points={
        'console_scripts':[
            'accessTime-sim=mcvqoe.accesstime.access_time_sim:main',
            'accessTime-measure=mcvqoe.accesstime.access_time_hw_test:main',
        ],
    },
    python_requires='>=3.6',
)

