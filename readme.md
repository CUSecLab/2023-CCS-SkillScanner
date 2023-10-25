# SkillScanner: Detecting Policy-Violating Voice Applications Through Static Analysis at the Development Phase

## System Overview
![Overview](https://github.com/CUSecLab/SkillScanner/blob/main/image/system_overview.png)
## Results
![Results](https://github.com/CUSecLab/SkillScanner/blob/main/image/Results.png)

## Usage

### Prerequisites

You need to download the CodeQL from [CodeQL](https://github.com/github/codeql-action/releases) to do the skill taint analysis.

After downloading and unzipping it, rename it as "codeql-home" and put it in the root path of this repo.

When you plan to scan a skill, go to the "skillscanner" folder and run with: 


```bash
pip install -r requirements.txt
python scan_skills.py ../skills_code 1
```

"1" means there might be several skills in the target folder and "0" means only one skill. Ensure that all the skill files are in one folder.

The results will be in the folder "skillscanner/results" and each skill will have a folder for storing results.


### Dataset

To download all the skill code on GitHub platform (updated dataset), you can run:

```bash
python search_github.py
python clone_repo.py
```

After generating report for each skill, you can run:


```bash
python summarize_results.py
```

And issues of all skills will be in the "summary" folder.
