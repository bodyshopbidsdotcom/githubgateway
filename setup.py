from distutils.core import setup

setup(
  name = 'githubgateway',
  version = '0.2',
  py_modules = ['githubgateway'],
  description = 'A class to make api calls to github',
  author = 'Snapsheet',
  author_email = 'technotifications@snapsheet.me',
  url = 'https://github.com/bodyshopbidsdotcom/githubgateway',
  download_url = 'https://github.com/bodyshopbidsdotcom/githubgateway/tarball/0.2',
  keywords = ['api', 'gateway', 'http', 'REST'],
  install_requires = [
    'basegateway==0.7',
    'GitPython==1.0.1'
  ],
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
