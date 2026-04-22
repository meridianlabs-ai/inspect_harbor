# Registry – Inspect Harbor

All Harbor datasets available as Inspect tasks. Use the search box to filter by name or description, the category chips to filter by topic, and the column headers to sort. Click a dataset’s name to open its page here, which includes a link to the dataset’s page on the Harbor registry.

## Usage

**CLI:**

``` bash
inspect eval inspect_harbor/aime_1_0 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import aime_1_0

eval(aime_1_0(), model="openai/gpt-5")
```

## Available Datasets

| Harbor Dataset | Inspect Task | Description | Samples |
|----|----|----|----|
| [ade-bench@1.0](registry/ade_bench_1_0.html.md) | ade_bench_1_0 | Analytics Data Engineer Bench: tasks evaluating AI agents on dbt/SQL data analytics engineering bugs. | 48 |
| [aider-polyglot@1.0](registry/aider_polyglot_1_0.html.md) | aider_polyglot_1_0 | A polyglot coding benchmark that evaluates AI agents’ ability to perform code editing and generation tasks across multiple programming languages. | 225 |
| [aime@1.0](registry/aime_1_0.html.md) | aime_1_0 | American Invitational Mathematics Examination (AIME) benchmark for evaluating mathematical reasoning and problem-solving capabilities. Contains 60 competition-level mathematics problems from AIME 2024, 2025-I, and 2025-II competitions. | 60 |
| [algotune@1.0](registry/algotune_1_0.html.md) | algotune_1_0 | AlgoTune: 154 algorithm optimization tasks focusing on speedup-based scoring from the AlgoTune benchmark. | 154 |
| [arc_agi_2@1.0](registry/arc_agi_2_1_0.html.md) | arc_agi_2_1_0 | ARC-AGI-2: A benchmark measuring abstract reasoning through visual grid puzzles requiring rule inference and generalization. | 167 |
| [autocodebench@lite200](registry/autocodebench_lite200.html.md) | autocodebench_lite200 | Adapter for AutoCodeBench. | 200 |
| [bfcl@1.0](registry/bfcl_1_0.html.md) | bfcl_1_0 | Berkeley Function-Calling Leaderboard: 3,641 function calling tasks for evaluating LLM tool use capabilities across simple, multiple, parallel, and irrelevance categories. | 3641 |
| [bfcl_parity@1.0](registry/bfcl_parity_1_0.html.md) | bfcl_parity_1_0 | BFCL parity subset: 123 stratified sampled tasks for validating Harbor adapter equivalence with original BFCL benchmark. | 123 |
| [bigcodebench-hard-complete@1.0.0](registry/bigcodebench_hard_complete_1_0_0.html.md) | bigcodebench_hard_complete_1_0_0 | BigCodeBench-Hard complete benchmark adapter for Harbor - challenging Python programming tasks with reward-based verification. | 145 |
| [binary-audit@1.0](registry/binary_audit_1_0.html.md) | binary_audit_1_0 | An open-source benchmark for evaluating AI agents’ ability to find backdoors hidden in compiled binaries. | 46 |
| [bird-bench@parity](registry/bird_bench_parity.html.md) | bird_bench_parity | BIRD SQL parity subset (150 tasks, seed 42). | 150 |
| [bixbench-cli@1.5](registry/bixbench_cli_1_5.html.md) | bixbench_cli_1_5 | bixbench-cli - A benchmark for evaluating AI agents on bioinformatics and computational biology tasks. (Adapted for CLI execution). | 205 |
| [bixbench@1.5](registry/bixbench_1_5.html.md) | bixbench_1_5 | BixBench - A benchmark for evaluating AI agents on bioinformatics and computational biology tasks. | 205 |
| [code-contests@1.0](registry/code_contests_1_0.html.md) | code_contests_1_0 | A competitive programming benchmark from DeepMind that evaluates AI agents’ ability to solve algorithmic problems, covering algorithms, data structures, and competitive programming challenges. | 9644 |
| [codepde@1.0](registry/codepde_1_0.html.md) | codepde_1_0 | CodePDE evaluates code generation capabilities on scientific computing tasks, specifically focusing on Partial Differential Equation (PDE) solving. | 5 |
| [compilebench@1.0](registry/compilebench_1_0.html.md) | compilebench_1_0 | Version 1.0 of CompileBench, a benchmark on real open-source projects against dependency hell, legacy toolchains, and complex build systems. | 15 |
| [cooperbench@1.0](registry/cooperbench_1_0.html.md) | cooperbench_1_0 | CooperBench: multi-agent cooperation benchmark. 652 feature pairs across 12 repos requiring two agents to coordinate via messaging. | 652 |
| [crustbench@1.0](registry/crustbench_1_0.html.md) | crustbench_1_0 | CRUST-bench: 100 C-to-safe-Rust transpilation tasks from real-world C repositories. | 100 |
| [dabstep@1.0](registry/dabstep_1_0.html.md) | dabstep_1_0 | DABstep: Data Agent Benchmark for Multi-step Reasoning. 450 tasks where agents analyze payment transaction data with Python/pandas to answer business questions. | 450 |
| [deveval@1.0](registry/deveval_1_0.html.md) | deveval_1_0 | DevEval benchmark: comprehensive evaluation of LLMs across software development lifecycle (implementation, unit testing, acceptance testing) for 21 real-world repositories across Python, C++, Java, and JavaScript. | 63 |
| [ds-1000@head](registry/ds_1000_head.html.md) | ds_1000_head | DS-1000 is a code generation benchmark with 1000 realistic data science problems across seven popular Python libraries. | 1000 |
| [evoeval@1.0](registry/evoeval_1_0.html.md) | evoeval_1_0 | EvoEval_difficult: 100 challenging Python programming tasks evolved from HumanEval. | 100 |
| [featurebench-lite-modal@1.0](registry/featurebench_lite_modal_1_0.html.md) | featurebench_lite_modal_1_0 | FeatureBench lite split for Modal: 30 feature-implementation tasks with gpus=1 for GPU tasks (7/30). Use with -e modal. | 30 |
| [featurebench-lite@1.0](registry/featurebench_lite_1_0.html.md) | featurebench_lite_1_0 | FeatureBench lite split: 30 feature-implementation tasks (26 lv1 + 4 lv2) across Python repos. | 30 |
| [featurebench-modal@1.0](registry/featurebench_modal_1_0.html.md) | featurebench_modal_1_0 | FeatureBench full split for Modal: 200 feature-implementation tasks with gpus=1 for GPU tasks (44/200). Use with -e modal. | 200 |
| [featurebench@1.0](registry/featurebench_1_0.html.md) | featurebench_1_0 | FeatureBench full split: 200 feature-implementation tasks across 24 Python repos. 7 tasks require Ampere+ GPU. | 200 |
| [financeagent@public](registry/financeagent_public.html.md) | financeagent_public | Finance Agent is a tool for financial research and analysis that leverages large language models and specialized financial tools to answer complex queries about companies, financial statements, and SEC filings. | 50 |
| [gaia@1.0](registry/gaia_1_0.html.md) | gaia_1_0 | GAIA (General AI Assistants): 165 validation tasks for multi-step reasoning, tool use, and multimodal question answering. | 165 |
| [gpqa-diamond@1.0](registry/gpqa_diamond_1_0.html.md) | gpqa_diamond_1_0 | GPQA Diamond subset: 198 graduate-level multiple-choice questions in biology, physics, and chemistry for evaluating scientific reasoning. | 198 |
| [gso@1.0](registry/gso_1_0.html.md) | gso_1_0 | GSO: 102 software optimization tasks focusing on performance improvement. | 102 |
| [hello-world@1.0](registry/hello_world_1_0.html.md) | hello_world_1_0 | A simple example task to create a hello.txt file with ‘Hello, world!’ as content. | 1 |
| [humanevalfix@1.0](registry/humanevalfix_1_0.html.md) | humanevalfix_1_0 | HumanEvalFix: 164 Python code repair tasks from HumanEvalPack. | 164 |
| [ineqmath@1.0](registry/ineqmath_1_0.html.md) | ineqmath_1_0 | This adapter brings IneqMath, the dev set of the first inequality-proof Q&A benchmark for LLMs, into Harbor, enabling standardized evaluation of models on mathematical reasoning and proof construction. | 100 |
| [kumo@1.0](registry/kumo_1_0.html.md) | kumo_1_0 | KUMO full dataset (5300 tasks; 50 instances per scenario). | 5300 |
| [kumo@easy](registry/kumo_easy.html.md) | kumo_easy | KUMO(easy) split (5050 tasks; 50 instances per scenario). | 5050 |
| [kumo@hard](registry/kumo_hard.html.md) | kumo_hard | KUMO(hard) split (250 tasks; 50 instances per scenario). | 250 |
| [kumo@parity](registry/kumo_parity.html.md) | kumo_parity | KUMO parity subset (seeds 0/1; 212 tasks). | 212 |
| [labbench@1.0](registry/labbench_1_0.html.md) | labbench_1_0 | LAB-Bench FigQA: 181 scientific figure reasoning tasks in biology from Future-House LAB-Bench. | 181 |
| [lawbench@1.0](registry/lawbench_1_0.html.md) | lawbench_1_0 | LawBench: Benchmarking Legal Knowledge of Large Language Models. | 1000 |
| [legacy-bench@1.0](registry/legacy_bench_1_0.html.md) | legacy_bench_1_0 | A benchmark for evaluating AI agents on legacy code maintenance and modernization tasks across multiple language families including COBOL, Java 7, C, Fortran, and Assembly. | 10 |
| [livecodebench@6.0](registry/livecodebench_6_0.html.md) | livecodebench_6_0 | A subset of 100 sampled tasks from the release_v6 version of LiveCodeBench tasks. | 100 |
| [medagentbench@1.0](registry/medagentbench_1_0.html.md) | medagentbench_1_0 | MedAgentBench: 300 patient-specific clinically-derived tasks across 10 categories in a FHIR-compliant interactive healthcare environment. | 300 |
| [ml-dev-bench@1.0](registry/ml_dev_bench_1_0.html.md) | ml_dev_bench_1_0 | ML-Dev-Bench: A benchmark for testing AI agents on machine learning development tasks including model implementation, training, debugging, and optimization. | 33 |
| [mlgym-bench@1.0](registry/mlgym_bench_1_0.html.md) | mlgym_bench_1_0 | Evaluates agents on ML tasks across computer vision, RL, tabular ML, and game theory. | 12 |
| [mmau@1.0](registry/mmau_1_0.html.md) | mmau_1_0 | MMAU: 1000 carefully curated audio clips paired with human-annotated natural language questions and answers spanning speech, environmental sounds, and music. | 1000 |
| [mmmlu@parity](registry/mmmlu_parity.html.md) | mmmlu_parity | MMMLU (Multilingual MMLU) parity validation subset with 10 tasks per language across 15 languages (150 tasks total). Evaluates language models’ subject knowledge and reasoning across multiple languages using multiple-choice questions covering 57 academic subjects. | 150 |
| [openthoughts-tblite@2.0](registry/openthoughts_tblite_2_0.html.md) | openthoughts_tblite_2_0 | OpenThoughts-TBLite: A difficulty-calibrated benchmark of 100 tasks for building terminal agents. By OpenThoughts Agent team, Snorkel AI, Bespoke Labs. | 100 |
| [otel-bench@1.0](registry/otel_bench_1_0.html.md) | otel_bench_1_0 | OpenTelemetry Benchmark - evaluates AI agents’ ability to instrument applications with OpenTelemetry tracing across multiple languages. | 26 |
| [pixiu@parity](registry/pixiu_parity.html.md) | pixiu_parity | PIXIU: A Large Language Model, Instruction Data and Evaluation Benchmark for Finance. Total tasks: 435 across 29 financial NLP datasets. | 435 |
| [qcircuitbench@1.0](registry/qcircuitbench_1_0.html.md) | qcircuitbench_1_0 | QCircuitBench evaluates agents on quantum algorithm design using quantum programming languages. | 28 |
| [quixbugs@1.0](registry/quixbugs_1_0.html.md) | quixbugs_1_0 | QuixBugs is a multi-lingual program repair benchmark with 40 Python and 40 Java programs, each containing a single-line defect. Tasks cover algorithms and data structures including sorting, graph, dynamic programming, math, and string/array operations. | 80 |
| [reasoning-gym-easy@parity](registry/reasoning_gym_easy_parity.html.md) | reasoning_gym_easy_parity | Reasoning Gym benchmark (easy difficulty). | 288 |
| [reasoning-gym-hard@parity](registry/reasoning_gym_hard_parity.html.md) | reasoning_gym_hard_parity | Reasoning Gym benchmark (hard difficulty). | 288 |
| [replicationbench@1.0](registry/replicationbench_1_0.html.md) | replicationbench_1_0 | ReplicationBench - A benchmark for evaluating AI agents on reproducing computational results from astrophysics research papers. Adapted from Christine8888/replicationbench-release. | 90 |
| [researchcodebench@1.0](registry/researchcodebench_1_0.html.md) | researchcodebench_1_0 | ResearchCodeBench evaluates AI agents’ ability to implement algorithms from academic papers. Contains 212 code implementation tasks across 20 ML/AI research problems from top-tier venues (ICLR, NeurIPS, CVPR, COLM). Tests paper comprehension, algorithm understanding, and precise code implementation skills with 1,449 lines of reference code. | 212 |
| [rexbench@1.0](registry/rexbench_1_0.html.md) | rexbench_1_0 | A benchmark to evaluate the ability of AI agents to extend existing AI research through research experiment implementation tasks. | 2 |
| [satbench@1.0](registry/satbench_1_0.html.md) | satbench_1_0 | SATBench is a benchmark for evaluating the logical reasoning capabilities of LLMs through logical puzzles derived from Boolean satisfiability (SAT) problems. | 2100 |
| [scale-ai/swe-atlas-qna@1.0](registry/scale_ai_swe_atlas_qna_1_0.html.md) | scale_ai_swe_atlas_qna_1_0 | SWE-Atlas Codebase QnA benchmark that evaluates AI agents’ ability to comprehend and query existing codebases. | 124 |
| [scale-ai/swe-atlas-tw@1.0](registry/scale_ai_swe_atlas_tw_1_0.html.md) | scale_ai_swe_atlas_tw_1_0 | SWE-Atlas Test Writing benchmark that evaluates AI agents’ ability to write comprehensive unit tests. | 90 |
| [seta-env@1.0](registry/seta_env_1_0.html.md) | seta_env_1_0 | CAMEL SETA Environment for RL training. | 1376 |
| [simpleqa@1.0](registry/simpleqa_1_0.html.md) | simpleqa_1_0 | SimpleQA: 4,326 short, fact-seeking questions from OpenAI for evaluating language model factuality. Uses LLM-as-a-judge grading. | 4326 |
| [sldbench@1.0](registry/sldbench_1_0.html.md) | sldbench_1_0 | SLDBench: A benchmark for scaling law discovery with symbolic regression tasks. | 8 |
| [spider2-dbt@1.0](registry/spider2_dbt_1_0.html.md) | spider2_dbt_1_0 | Spider 2.0-DBT is a comprehensive code generation agent task that includes 68 examples. Solving these tasks requires models to understand project code, navigating complex SQL environments and handling long contexts, surpassing traditional text-to-SQL challenges. | 64 |
| [spreadsheetbench-verified@1.0](registry/spreadsheetbench_verified_1_0.html.md) | spreadsheetbench_verified_1_0 | A benchmark evaluating AI agents on real-world spreadsheet manipulation tasks (400 tasks from verified_400). Tasks involve Excel file manipulation including formula writing, data transformation, formatting, and conditional logic. | 400 |
| [strongreject@parity](registry/strongreject_parity.html.md) | strongreject_parity | StrongReject benchmark for evaluating LLM safety and jailbreak resistance. Parity subset with 150 tasks (50 prompts \* 3 jailbreaks). | 150 |
| [swe-gen-js@1.0](registry/swe_gen_js_1_0.html.md) | swe_gen_js_1_0 | SWE-gen-JS: 1000 JavaScript/TypeScript bug fix tasks from 30 open-source GitHub repos, generated using SWE-gen. | 1000 |
| [swe-lancer-diamond@all](registry/swe_lancer_diamond_all.html.md) | swe_lancer_diamond_all | Adapter for SWE-Lancer. Both manager and individual contributor tasks. | 463 |
| [swe-lancer-diamond@ic](registry/swe_lancer_diamond_ic.html.md) | swe_lancer_diamond_ic | Adapter for SWE-Lancer. Only the individual contributor SWE tasks. | 198 |
| [swe-lancer-diamond@manager](registry/swe_lancer_diamond_manager.html.md) | swe_lancer_diamond_manager | Adapter for SWE-Lancer. Only the manager tasks. | 265 |
| [swebench-verified@1.0](registry/swebench_verified_1_0.html.md) | swebench_verified_1_0 | A human-validated subset of 500 SWE-bench tasks. | 500 |
| [swebench_multilingual@1.0](registry/swebench_multilingual_1_0.html.md) | swebench_multilingual_1_0 | SWE-bench Multilingual extends the original Python-focused SWE-bench benchmark to support multiple programming languages. | 300 |
| [swebenchpro@1.0](registry/swebenchpro_1_0.html.md) | swebenchpro_1_0 | SWE-bench Pro: A multi-language software engineering benchmark with 731 instances covering Python, JavaScript/TypeScript, and Go. Evaluates AI systems’ ability to resolve real-world bugs and implement features across diverse production codebases. | 731 |
| [swesmith@1.0](registry/swesmith_1_0.html.md) | swesmith_1_0 | SWE-smith is a synthetically generated dataset of software engineering tasks derived from GitHub issues for training and evaluating code generation models. | 100 |
| [swtbench-verified@1.0](registry/swtbench_verified_1_0.html.md) | swtbench_verified_1_0 | SWTBench Verified - Software Testing Benchmark for code generation. | 433 |
| [termigen-environments@1.0](registry/termigen_environments_1_0.html.md) | termigen_environments_1_0 | 3,500+ verified Docker environments for training and evaluating terminal agents, spanning 11 task categories across infrastructure, data/algorithm applications, and specialized domains including software build, system administration, security, data processing, ML/MLOps, algorithms, scientific computing, and more. | 3566 |
| [terminal-bench-pro@1.0](registry/terminal_bench_pro_1_0.html.md) | terminal_bench_pro_1_0 | Terminal-Bench Pro (Public Set) is an extended benchmark dataset for testing AI agents in real terminal environments. From compiling code to training models and setting up servers, Terminal-Bench Pro evaluates how well agents can handle real-world, end-to-end tasks autonomously. | 200 |
| [terminal-bench-sample@2.0](registry/terminal_bench_sample_2_0.html.md) | terminal_bench_sample_2_0 | A sample of tasks from Terminal-Bench 2.0. | 10 |
| [terminal-bench@2.0](registry/terminal_bench_2_0.html.md) | terminal_bench_2_0 | Version 2.0 of Terminal-Bench, a benchmark for testing agents in terminal environments. More tasks, harder, and higher quality than 1.0. | 89 |
| [usaco@2.0](registry/usaco_2_0.html.md) | usaco_2_0 | USACO: 304 Python programming problems from USACO competition. | 304 |
| [vmax-tasks@1.0](registry/vmax_tasks_1_0.html.md) | vmax_tasks_1_0 | A collection of 1,043 validated real-world bug-fixing tasks from popular open-source JavaScript projects including Vue.js, Docusaurus, Redux, and Chalk. Each task presents an authentic bug report with reproduction steps and expected behavior. | 1043 |

No matching items
