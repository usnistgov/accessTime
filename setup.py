import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="mcvqoe-nist",
    author="Jesse Frey, Peter Fink, Jaden Pieper",
    author_email="jesse.frey@nist.gov,jaden.pieper@nist.gov",
    description="Common code for MCV QoE Measurement Classes",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.nist.gov/gitlab/PSCR/MCV/mcv-qoe-library",
    packages=setuptools.find_namespace_packages(include=['mcvqoe.*']),
    include_package_data=True,
    package_data={
        "mcvqoe": ["audio_clips", "test.wav"],
        "mcvqoe": ["gui", "MCV-sm.png"],
    },
    use_scm_version={"write_to": "mcvqoe/base/version.py"},
    setup_requires=["setuptools_scm"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Public Domain",
        "Operating System :: OS Independent",
    ],
    license="NIST software License",
    install_requires=[
        "numpy",
        "scipy",
        "sounddevice",
        "pyserial",
        "soundfile",
        "appdirs",
        'importlib-metadata ; python_version < "3.8"',
    ],
    entry_points={
        "console_scripts": [
            "testCpy=mcvqoe.utilities.testCpy:main",
            "local-copy=mcvqoe.utilities.local_copy:main",
            "mcvqoe-test-play=mcvqoe.hardware.PTT_play:main",
        ],
        "mcvqoe.channel": "clean=mcvqoe.simulation.cleanchan",
    },
    python_requires=">=3.6",
)
