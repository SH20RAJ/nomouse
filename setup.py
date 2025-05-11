from setuptools import setup, find_packages

setup(
    name="nomouse",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "opencv-python>=4.7.0",
        "mediapipe>=0.9.0",
        "pyautogui>=0.9.53",
        "numpy>=1.21.0",
        "PyQt6>=6.4.0",
        "pillow>=9.0.0",
    ],
    entry_points={
        "console_scripts": [
            "nomouse=app:main",
        ],
    },
    author="SH20RAJ",
    author_email="shaswatraj3@gmail.com",
    description="Control your PC without mouse or trackpad using hand gestures",
    keywords="gesture, control, mouse, computer vision",
    url="https://github.com/sh20raj/nomouse",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Utilities",
    ],
    python_requires=">=3.7",
)
