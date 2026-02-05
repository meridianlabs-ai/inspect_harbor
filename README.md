# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/meridianlabs-ai/inspect_harbor/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                           |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|----------------------------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| src/inspect\_harbor/\_\_init\_\_.py            |        3 |        0 |        0 |        0 |    100% |           |
| src/inspect\_harbor/\_registry.py              |        2 |        2 |        0 |        0 |      0% |       2-3 |
| src/inspect\_harbor/harbor/\_\_init\_\_.py     |        0 |        0 |        0 |        0 |    100% |           |
| src/inspect\_harbor/harbor/\_converters.py     |       40 |        1 |       12 |        2 |     94% |44->51, 49 |
| src/inspect\_harbor/harbor/\_sandbox\_utils.py |       18 |        0 |        6 |        0 |    100% |           |
| src/inspect\_harbor/harbor/\_scorer.py         |       69 |        3 |       16 |        2 |     94% |70-71, 147 |
| src/inspect\_harbor/harbor/\_solver.py         |       33 |        2 |        6 |        0 |     95% |     42-43 |
| src/inspect\_harbor/harbor/\_task.py           |       71 |       18 |       20 |        1 |     73% |196-200, 221-228, 241-264 |
| **TOTAL**                                      |  **236** |   **26** |   **60** |    **5** | **88%** |           |


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