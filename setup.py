import setuptools

with open("README.md", "r",encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name="mcvqoe-nist",
    author="Jesse Frey, Peter Fink, Jaden Pieper",
    author_email="jesse.frey@nist.gov,jaden.pieper@nist.gov",
    description="Common code for MCV QoE Measurement Classes",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.nist.gov/gitlab/PSCR/MCV/mcv-qoe-library",
    packages=setuptools.find_packages(),
    include_package_data=True,
    use_scm_version={'write_to' : 'mcvqoe/version.py'},
    setup_requires=['setuptools_scm'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Public Domain",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'numpy','scipy','sounddevice','serial','pyserial','soundfile','appdirs'
    ],
    entry_points={
        'console_scripts':[
            'testCpy=mcvqoe.utilities.testCpy:main',
            'local-copy=mcvqoe.utilities.local_copy:main'
        ],
    },
    python_requires='>=3.6',
)
