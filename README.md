# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/meridianlabs-ai/inspect_harbor/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                           |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|----------------------------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| src/inspect\_harbor/\_\_init\_\_.py            |        4 |        0 |        0 |        0 |    100% |           |
| src/inspect\_harbor/\_harbor/\_\_init\_\_.py   |        0 |        0 |        0 |        0 |    100% |           |
| src/inspect\_harbor/\_harbor/converters.py     |       93 |        0 |       40 |        1 |     99% |   71-\>90 |
| src/inspect\_harbor/\_harbor/sandbox\_utils.py |       38 |        0 |       14 |        0 |    100% |           |
| src/inspect\_harbor/\_harbor/scorer.py         |       76 |        3 |       18 |        2 |     95% |72-73, 161 |
| src/inspect\_harbor/\_harbor/solver.py         |       34 |        2 |        8 |        0 |     95% |     43-44 |
| src/inspect\_harbor/\_harbor/task.py           |      115 |       26 |       44 |        8 |     77% |244, 246, 248, 265, 267, 269, 271, 293-302, 321-330, 343-358, 370-378, 386-394 |
| src/inspect\_harbor/\_registry.py              |        4 |        0 |        0 |        0 |    100% |           |
| src/inspect\_harbor/\_tasks.py                 |      308 |      101 |        0 |        0 |     67% |32, 63, 125, 156, 187, 218, 249, 280, 311, 342, 373, 404, 435, 466, 497, 528, 559, 590, 621, 652, 683, 714, 745, 776, 807, 838, 869, 900, 931, 962, 993, 1024, 1055, 1086, 1117, 1148, 1179, 1210, 1241, 1272, 1303, 1334, 1365, 1396, 1427, 1458, 1489, 1520, 1551, 1582, 1613, 1644, 1675, 1706, 1737, 1768, 1799, 1830, 1861, 1892, 1923, 1954, 1985, 2016, 2047, 2078, 2109, 2140, 2171, 2202, 2233, 2264, 2295, 2332, 2363, 2394, 2425, 2456, 2487, 2518, 2549, 2580, 2611, 2642, 2673, 2704, 2735, 2766, 2797, 2828, 2859, 2890, 2921, 2952, 2983, 3014, 3045, 3076, 3107, 3138, 3169 |
| src/inspect\_harbor/\_version.py               |       11 |       11 |        0 |        0 |      0% |      3-24 |
| **TOTAL**                                      |  **683** |  **143** |  **124** |   **11** | **81%** |           |


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