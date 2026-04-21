# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/meridianlabs-ai/inspect_harbor/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                           |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|----------------------------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| src/inspect\_harbor/\_\_init\_\_.py            |        4 |        0 |        0 |        0 |    100% |           |
| src/inspect\_harbor/\_harbor/\_\_init\_\_.py   |        0 |        0 |        0 |        0 |    100% |           |
| src/inspect\_harbor/\_harbor/converters.py     |       70 |        0 |       26 |        1 |     99% |   78-\>92 |
| src/inspect\_harbor/\_harbor/sandbox\_utils.py |       38 |        0 |       14 |        0 |    100% |           |
| src/inspect\_harbor/\_harbor/scorer.py         |       75 |        3 |       18 |        2 |     95% |72-73, 159 |
| src/inspect\_harbor/\_harbor/solver.py         |       34 |        2 |        8 |        0 |     95% |     43-44 |
| src/inspect\_harbor/\_harbor/task.py           |       65 |       18 |       20 |        1 |     71% |198-202, 223-230, 243-266 |
| src/inspect\_harbor/\_registry.py              |        4 |        0 |        0 |        0 |    100% |           |
| src/inspect\_harbor/\_tasks.py                 |      467 |      154 |        0 |        0 |     67% |31, 91, 121, 151, 181, 211, 241, 271, 301, 331, 361, 391, 421, 451, 481, 511, 541, 571, 601, 631, 661, 691, 721, 751, 781, 811, 841, 871, 901, 931, 961, 991, 1021, 1051, 1081, 1111, 1141, 1171, 1201, 1231, 1261, 1291, 1321, 1351, 1381, 1411, 1441, 1471, 1501, 1531, 1561, 1591, 1621, 1651, 1681, 1711, 1741, 1771, 1801, 1831, 1861, 1891, 1921, 1951, 1981, 2011, 2041, 2071, 2101, 2131, 2161, 2191, 2221, 2251, 2281, 2311, 2341, 2371, 2401, 2431, 2461, 2491, 2521, 2551, 2581, 2611, 2641, 2671, 2701, 2731, 2761, 2791, 2821, 2851, 2881, 2911, 2941, 2971, 3001, 3031, 3061, 3091, 3121, 3151, 3181, 3211, 3241, 3271, 3301, 3331, 3361, 3391, 3421, 3451, 3481, 3511, 3541, 3571, 3601, 3631, 3661, 3691, 3721, 3751, 3781, 3811, 3841, 3871, 3901, 3931, 3961, 3991, 4021, 4051, 4081, 4111, 4141, 4171, 4201, 4231, 4261, 4291, 4321, 4351, 4381, 4411, 4441, 4471, 4501, 4531, 4561, 4591, 4621, 4651 |
| src/inspect\_harbor/\_version.py               |       11 |       11 |        0 |        0 |      0% |      3-24 |
| **TOTAL**                                      |  **768** |  **188** |   **86** |    **4** | **77%** |           |


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