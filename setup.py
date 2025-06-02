from setuptools import setup, find_namespace_packages


setup(
    name='qc-collector-template',
    version='0.1.0',
    packages=find_namespace_packages(),
    entry_points={
        "console_scripts": [
            "qc-collector = qc_collector.__main__:main",
        ]
    },
    scripts=[],
    package_data={
    },
    install_requires=[
    ],
    description='Collect Genomics QC Data',
    url='https://github.com/BCCDC-PHL/qc-collector-template',
    author='',
    author_email='',
    include_package_data=True,
    keywords=[],
    zip_safe=False
)
