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
| src/inspect\_harbor/tasks.py                   |      254 |       83 |        0 |        0 |     67% |30, 88, 117, 146, 175, 204, 233, 262, 291, 320, 349, 378, 407, 436, 465, 494, 523, 552, 581, 610, 639, 668, 697, 726, 755, 784, 813, 842, 871, 900, 929, 958, 987, 1016, 1045, 1074, 1103, 1132, 1161, 1190, 1219, 1248, 1277, 1306, 1335, 1364, 1393, 1422, 1451, 1480, 1509, 1538, 1567, 1596, 1625, 1654, 1683, 1712, 1741, 1770, 1799, 1828, 1857, 1886, 1915, 1944, 1973, 2002, 2031, 2060, 2089, 2118, 2147, 2176, 2205, 2234, 2263, 2292, 2321, 2350, 2379, 2408, 2437 |
| **TOTAL**                                      |  **527** |  **120** |   **72** |    **5** | **78%** |           |


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