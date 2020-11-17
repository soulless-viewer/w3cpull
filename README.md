# W3Cpull Application

## Description
**W3Cpull** is an application for pulling data from IBM W3 Connections.

### Environment
* Language: Python3
* Frameworks: Selenium
* Interface: CLI
* Supported OS: Linux, OS X (not tested yet)

## Installation

 1. pip install w3cpull

## Usage

```
Usage:
    w3cpull --community-url=COMMUNITY_URL --target-dir=TARGET_DIR_PATH [--temp-dir=TEMP_DIR_PATH] [--w3id-auth=W3ID_AUTH] [--browser=BROWSER] [--recursive] [--visual]
    w3cpull -h | --help
    w3cpull -v | --version

Options:
    --community-url=COMMUNITY_URL   Set the URL of the target community
    --target-dir=TARGET_DIR_PATH    Set the path to the directory where the content will be saved (by default, the content is deleted after completion)
    --temp-dir=TEMP_DIR_PATH        Set the path to the folder where the content will be temporarily stored and processed (by default, /tmp)
    --w3id-auth=W3ID_AUTH           Set the uername:password value for automatic authentication
    --browser=BROWSER               Set the name of the browser to use (by default, Firefox)
    --recursive                     Set the recursive execution type (with subcommunity processing)
    --visual                        Set the visual execution type (with the browser open)
    -h, --help                      Show this help message.
    -v, --version                   Show the version.
```

## Additional info
>The app is currently under development. The app may contain errors. Use at your own risk.

## Contributing

1.  Fork it.
2.  Create your feature branch:  `git checkout -b my-new-feature`
3.  Commit your changes:  `git commit -am 'Add some feature'`
4.  Push to the branch:  `git push origin my-new-feature`
5.  Submit a pull request :D

## License
The MIT License (MIT)

Copyright (c) 2020 Mikalai Lisitsa

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
