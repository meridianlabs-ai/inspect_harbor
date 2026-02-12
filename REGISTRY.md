# Inspect Harbor Registry

The following table lists all available Harbor datasets and their corresponding Inspect tasks.

## Usage

**CLI:**
```bash
inspect eval inspect_harbor/aime_1_0 --model openai/gpt-5
```

**Python:**
```python
from inspect_ai import eval
from inspect_harbor import aime_1_0

eval(aime_1_0(), model="openai/gpt-5")
```

## Available Datasets

| Harbor Dataset | Inspect Task | Description | Samples |
|---------------|--------------|-------------|---------|
| [aider-polyglot@1.0](https://harborframework.com/registry/aider-polyglot/1.0) | `aider_polyglot_1_0` | A polyglot coding benchmark that evaluates AI agents' ability to perform code editing and generation tasks across multiple programming languages. | 225 |
| [aime@1.0](https://harborframework.com/registry/aime/1.0) | `aime_1_0` | American Invitational Mathematics Examination (AIME) benchmark for evaluating mathematical reasoning and problem-solving capabilities. Contains 60 competition-level mathematics problems from AIME 2024, 2025-I, and 2025-II competitions. | 60 |
| [algotune@1.0](https://harborframework.com/registry/algotune/1.0) | `algotune_1_0` | AlgoTune: 154 algorithm optimization tasks focusing on speedup-based scoring from the AlgoTune benchmark. | 154 |
| [arc_agi_2@1.0](https://harborframework.com/registry/arc_agi_2/1.0) | `arc_agi_2_1_0` | ARC-AGI-2: A benchmark measuring abstract reasoning through visual grid puzzles requiring rule inference and generalization. | 167 |
| [autocodebench@lite200](https://harborframework.com/registry/autocodebench/lite200) | `autocodebench_lite200` | Adapter for AutoCodeBench (https://github.com/Tencent-Hunyuan/AutoCodeBenchmark). | 200 |
| [bixbench@1.5](https://harborframework.com/registry/bixbench/1.5) | `bixbench_1_5` | BixBench - A benchmark for evaluating AI agents on bioinformatics and computational biology tasks. | 205 |
| [bixbench-cli@1.5](https://harborframework.com/registry/bixbench-cli/1.5) | `bixbench_cli_1_5` | bixbench-cli - A benchmark for evaluating AI agents on bioinformatics and computational biology tasks. (Adapted for CLI execution) | 205 |
| [codepde@1.0](https://harborframework.com/registry/codepde/1.0) | `codepde_1_0` | CodePDE evaluates code generation capabilities on scientific computing tasks, specifically focusing on Partial Differential Equation (PDE) solving. | 5 |
| [compilebench@1.0](https://harborframework.com/registry/compilebench/1.0) | `compilebench_1_0` | Version 1.0 of CompileBench, a benchmark on real open-source projects against dependency hell, legacy toolchains, and complex build systems. | 15 |
| [crustbench@1.0](https://harborframework.com/registry/crustbench/1.0) | `crustbench_1_0` | CRUST-bench: 100 C-to-safe-Rust transpilation tasks from real-world C repositories. | 100 |
| [ds-1000@head](https://harborframework.com/registry/ds-1000/head) | `ds_1000_head` | DS-1000 is a code generation benchmark with 1000 realistic data science problems across seven popular Python libraries. | 1000 |
| [evoeval@1.0](https://harborframework.com/registry/evoeval/1.0) | `evoeval_1_0` | EvoEval_difficult: 100 challenging Python programming tasks evolved from HumanEval. | 100 |
| [gpqa-diamond@1.0](https://harborframework.com/registry/gpqa-diamond/1.0) | `gpqa_diamond_1_0` | GPQA Diamond subset: 198 graduate-level multiple-choice questions in biology, physics, and chemistry for evaluating scientific reasoning. | 198 |
| [hello-world@1.0](https://harborframework.com/registry/hello-world/1.0) | `hello_world_1_0` | A simple example task to create a hello.txt file with 'Hello, world!' as content. | 1 |
| [humanevalfix@1.0](https://harborframework.com/registry/humanevalfix/1.0) | `humanevalfix_1_0` | HumanEvalFix: 164 Python code repair tasks from HumanEvalPack. | 164 |
| [ineqmath@1.0](https://harborframework.com/registry/ineqmath/1.0) | `ineqmath_1_0` | This adapter brings IneqMath, the dev set of the first inequality-proof Q\&A benchmark for LLMs, into Harbor, enabling standardized evaluation of models on mathematical reasoning and proof construction. | 100 |
| [lawbench@1.0](https://harborframework.com/registry/lawbench/1.0) | `lawbench_1_0` | LawBench: Benchmarking Legal Knowledge of Large Language Models | 1000 |
| [livecodebench@6.0](https://harborframework.com/registry/livecodebench/6.0) | `livecodebench_6_0` | A subset of 100 sampled tasks from the release_v6 version of LiveCodeBench tasks. | 100 |
| [mlgym-bench@1.0](https://harborframework.com/registry/mlgym-bench/1.0) | `mlgym_bench_1_0` | Evaluates agents on ML tasks across computer vision, RL, tabular ML, and game theory. | 12 |
| [mmau@1.0](https://harborframework.com/registry/mmau/1.0) | `mmau_1_0` | MMAU: 1000 carefully curated audio clips paired with human-annotated natural language questions and answers spanning speech, environmental sounds, and music. | 1000 |
| [mmmlu@parity](https://harborframework.com/registry/mmmlu/parity) | `mmmlu_parity` | MMMLU (Multilingual MMLU) parity validation subset with 10 tasks per language across 15 languages (150 tasks total). Evaluates language models' subject knowledge and reasoning across multiple languages using multiple-choice questions covering 57 academic subjects. | 150 |
| [reasoning-gym-easy@parity](https://harborframework.com/registry/reasoning-gym-easy/parity) | `reasoning_gym_easy_parity` | Reasoning Gym benchmark (easy difficulty). Original benchmark: https://github.com/open-thought/reasoning-gym | 288 |
| [reasoning-gym-hard@parity](https://harborframework.com/registry/reasoning-gym-hard/parity) | `reasoning_gym_hard_parity` | Reasoning Gym benchmark (hard difficulty). Original benchmark: https://github.com/open-thought/reasoning-gym | 288 |
| [replicationbench@1.0](https://harborframework.com/registry/replicationbench/1.0) | `replicationbench_1_0` | ReplicationBench - A benchmark for evaluating AI agents on reproducing computational results from astrophysics research papers. Adapted from Christine8888/replicationbench-release. | 90 |
| [seta-env@1.0](https://harborframework.com/registry/seta-env/1.0) | `seta_env_1_0` | CAMEL SETA Environment for RL training | 1376 |
| [sldbench@1.0](https://harborframework.com/registry/sldbench/1.0) | `sldbench_1_0` | SLDBench: A benchmark for scaling law discovery with symbolic regression tasks. | 8 |
| [spider2-dbt@1.0](https://harborframework.com/registry/spider2-dbt/1.0) | `spider2_dbt_1_0` | Spider 2.0-DBT is a comprehensive code generation agent task that includes 68 examples. Solving these tasks requires models to understand project code, navigating complex SQL environments and handling long contexts, surpassing traditional text-to-SQL challenges. | 64 |
| [strongreject@parity](https://harborframework.com/registry/strongreject/parity) | `strongreject_parity` | StrongReject benchmark for evaluating LLM safety and jailbreak resistance. Parity subset with 150 tasks (50 prompts * 3 jailbreaks). | 150 |
| [swe-gen-js@1.0](https://harborframework.com/registry/swe-gen-js/1.0) | `swe_gen_js_1_0` | SWE-gen-JS: 1000 JavaScript/TypeScript bug fix tasks from 30 open-source GitHub repos, generated using SWE-gen. | 1000 |
| [swe-lancer-diamond@all](https://harborframework.com/registry/swe-lancer-diamond/all) | `swe_lancer_diamond_all` | Adapter for SWE-Lancer (https://github.com/openai/preparedness/blob/main/project/swelancer/README.md). Both manager and individual contributor tasks. | 463 |
| [swe-lancer-diamond@ic](https://harborframework.com/registry/swe-lancer-diamond/ic) | `swe_lancer_diamond_ic` | Adapter for SWE-Lancer (https://github.com/openai/preparedness/blob/main/project/swelancer/README.md). Only the individual contributor SWE tasks. | 198 |
| [swe-lancer-diamond@manager](https://harborframework.com/registry/swe-lancer-diamond/manager) | `swe_lancer_diamond_manager` | Adapter for SWE-Lancer (https://github.com/openai/preparedness/blob/main/project/swelancer/README.md). Only the manager tasks. | 265 |
| [swebench-verified@1.0](https://harborframework.com/registry/swebench-verified/1.0) | `swebench_verified_1_0` | A human-validated subset of 500 SWE-bench tasks | 500 |
| [swebenchpro@1.0](https://harborframework.com/registry/swebenchpro/1.0) | `swebenchpro_1_0` | SWE-bench Pro: A multi-language software engineering benchmark with 731 instances covering Python, JavaScript/TypeScript, and Go. Evaluates AI systems' ability to resolve real-world bugs and implement features across diverse production codebases. Original benchmark: https://github.com/scaleapi/SWE-bench_Pro-os. Adapter details: https://github.com/laude-institute/harbor/tree/main/adapters/swebenchpro | 731 |
| [swesmith@1.0](https://harborframework.com/registry/swesmith/1.0) | `swesmith_1_0` | SWE-smith is a synthetically generated dataset of software engineering tasks derived from GitHub issues for training and evaluating code generation models. | 100 |
| [swtbench-verified@1.0](https://harborframework.com/registry/swtbench-verified/1.0) | `swtbench_verified_1_0` | SWTBench Verified - Software Testing Benchmark for code generation | 433 |
| [terminal-bench@2.0](https://harborframework.com/registry/terminal-bench/2.0) | `terminal_bench_2_0` | Version 2.0 of Terminal-Bench, a benchmark for testing agents in terminal environments. More tasks, harder, and higher quality than 1.0. | 89 |
| [terminal-bench-pro@1.0](https://harborframework.com/registry/terminal-bench-pro/1.0) | `terminal_bench_pro_1_0` | Terminal-Bench Pro (Public Set) is an extended benchmark dataset for testing AI agents in real terminal environments. From compiling code to training models and setting up servers, Terminal-Bench Pro evaluates how well agents can handle real-world, end-to-end tasks autonomously. | 200 |
| [terminal-bench-sample@2.0](https://harborframework.com/registry/terminal-bench-sample/2.0) | `terminal_bench_sample_2_0` | A sample of tasks from Terminal-Bench 2.0. | 10 |
| [usaco@2.0](https://harborframework.com/registry/usaco/2.0) | `usaco_2_0` | USACO: 304 Python programming problems from USACO competition. | 304 |
| [vmax-tasks@1.0](https://harborframework.com/registry/vmax-tasks/1.0) | `vmax_tasks_1_0` | A collection of 1,043 validated real-world bug-fixing tasks from popular open-source JavaScript projects including Vue.js, Docusaurus, Redux, and Chalk. Each task presents an authentic bug report with reproduction steps and expected behavior. | 1043 |

---

*This file is auto-generated by `scripts/generate_tasks.py`. Do not edit manually.*

*Registry: https://raw.githubusercontent.com/laude-institute/harbor/refs/heads/main/registry.json*
