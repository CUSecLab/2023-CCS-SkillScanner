# SkillScanner: Detecting Policy-Violating Voice Applications Through Static Analysis at the Development Phase

You can find our paper [here](https://arxiv.org/pdf/2309.05867.pdf). If you find our paper useful for you, please consider citing:


    @article{liao2023skillscanner,
    title={SkillScanner: Detecting Policy-Violating Voice Applications Through Static Analysis at the Development Phase},
    author={Liao, Song and Cheng, Long and Cai, Haipeng and Guo, Linke and Hu, Hongxin},
    journal={arXiv preprint arXiv:2309.05867},
    year={2023}
}

In this repository, the folder "skillscanner" contains the code for skillscanner. "skills_code" contains one example skill code for testing. "user-study" folder includes the data about our user study. "results" folder contains the results in our work based on our dataset. The "image" folder contains some images for presentation.





## System Overview
![Overview](https://github.com/CUSecLab/SkillScanner/blob/main/image/system_overview.png)
## Results
![Results](https://github.com/CUSecLab/SkillScanner/blob/main/image/Results.png)

## Usage

### Prerequisites

You can download the necessary Python libraries with:

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

You need to download the CodeQL from [CodeQL](https://github.com/github/codeql-action/releases) to do the skill taint analysis.

In our version, we used the CodeQL version v2.13.1. We ran all our experiments on Ubuntu 16.04 with Python 3.6. The tool might work on similar versions but this was not tested


After downloading and unzipping it, rename it as "codeql-home" and put it in the root path of this repo.

If you want to scan/download skill code datasets from GitHub or analyze skill content/html safety, you need to apply for tokens about GitHub, Google Perspective, and Virustotal. Then you need to put them in the "tokens.txt" file in the "skillscanner" folder.

When you plan to scan a skill, go to the "skillscanner" folder and run with: 


```bash
python scan_skills.py ../skills_code 1
```

"1" means there might be several skills in the target folder and "0" means only one skill. Ensure that all the skill files are in one folder.

If you download a new dataset using "clone_repo.py", it will appear in "repo" folder. So the code for analyzing it is:

```bash
python scan_skills.py repo 1
```

The results will be in the folder "skillscanner/results" and each skill will have a folder for storing results. There will also be a report that summarizes all the results of the skill. The detailed results, such as different issues in code inconsistency will be saved in "results/skillname/code_inconsistency/issuename".


### Dataset

To download all the skill code on GitHub platform (updated dataset), you can run:

```bash
python search_github.py
python clone_repo.py
```

After generating a report for each skill, you can run:


```bash
python summarize_results.py
```

And issues of all skills will be in the "summary" folder.

The Github commit hash for the artifact evaluation is 28ef6b98b6fa2802faaceab61d142212d65bda2c.
