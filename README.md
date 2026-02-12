# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/meridianlabs-ai/inspect_harbor/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                           |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|----------------------------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| src/inspect\_harbor/\_\_init\_\_.py            |        4 |        0 |        0 |        0 |    100% |           |
| src/inspect\_harbor/\_registry.py              |        4 |        0 |        0 |        0 |    100% |           |
| src/inspect\_harbor/\_version.py               |       13 |       13 |        0 |        0 |      0% |      4-34 |
| src/inspect\_harbor/harbor/\_\_init\_\_.py     |        0 |        0 |        0 |        0 |    100% |           |
| src/inspect\_harbor/harbor/\_converters.py     |       40 |        1 |       12 |        2 |     94% |74->81, 79 |
| src/inspect\_harbor/harbor/\_sandbox\_utils.py |       38 |        0 |       14 |        0 |    100% |           |
| src/inspect\_harbor/harbor/\_scorer.py         |       75 |        3 |       18 |        2 |     95% |72-73, 159 |
| src/inspect\_harbor/harbor/\_solver.py         |       34 |        2 |        8 |        0 |     95% |     43-44 |
| src/inspect\_harbor/harbor/\_task.py           |       65 |       18 |       20 |        1 |     71% |198-202, 223-230, 243-266 |
| src/inspect\_harbor/tasks.py                   |      242 |       79 |        0 |        0 |     67% |31, 89, 118, 147, 176, 205, 234, 263, 292, 321, 350, 379, 408, 437, 466, 495, 524, 553, 582, 611, 640, 669, 698, 727, 756, 785, 814, 843, 872, 901, 930, 959, 988, 1017, 1046, 1075, 1104, 1133, 1162, 1191, 1220, 1249, 1278, 1307, 1336, 1365, 1394, 1423, 1452, 1481, 1510, 1539, 1568, 1597, 1626, 1655, 1684, 1713, 1742, 1771, 1800, 1829, 1858, 1887, 1916, 1945, 1974, 2003, 2032, 2061, 2090, 2119, 2148, 2177, 2206, 2235, 2264, 2293, 2322 |
| **TOTAL**                                      |  **515** |  **116** |   **72** |    **5** | **78%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/meridianlabs-ai/inspect_harbor/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/meridianlabs-ai/inspect_harbor/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/meridianlabs-ai/inspect_harbor/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/meridianlabs-ai/inspect_harbor/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Fmeridianlabs-ai%2Finspect_harbor%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/meridianlabs-ai/inspect_harbor/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.