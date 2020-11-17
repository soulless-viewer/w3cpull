from setuptools import setup, find_packages

readme = None
with open('README.md', encoding='utf-8') as f:
    readme = f.read()
f.close()

requirements = None
with open('requirements.txt', encoding='utf-8') as f:
    requirements = f.read().splitlines()
f.close()

setup(
    name="w3cpull",
    version="1.0.0",
    author="Mikalai Lisitsa",
    author_email="Mikalai.Lisitsa@ibm.com",
    url="https://github.com/soulless-viewer/w3cpull",
    description="W3Cpull is an application for pulling data from IBM W3 Connections.",
    long_description=readme,
    long_description_content_type="text/markdown",
    keywords='w3connections w3c ibm',
    license='MIT',
    packages=find_packages(),
    install_requires=requirements,
    include_package_data=True,
    python_requires='>=3.6',
    scripts=['bin/w3cpull'],
)
