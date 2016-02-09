from distutils.core import setup

install_requires = []
with open('requirements.txt', 'r') as requirements_file:
  lines = requirements_file.read().splitlines()
  install_requires = [line for line in lines if len(line.strip()) > 0]

setup(
  name = 'githubgateway',
  version = '0.1',
  py_modules = ['githubgateway'],
  description = 'A class to make api calls to github',
  author = 'Snapsheet',
  author_email = 'technotifications@snapsheet.me',
  url = 'https://github.com/bodyshopbidsdotcom/githubgateway',
  download_url = 'https://github.com/bodyshopbidsdotcom/githubgateway/tarball/0.1',
  keywords = ['api', 'gateway', 'http', 'REST'],
  install_requires = install_requires,
  classifiers = [
    "Topic :: Internet :: WWW/HTTP",
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
  ],
)
