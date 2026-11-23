# Machine Learning for Web Attack Detection
### OWASP Top 10:2025 – A05: Injection

**Group 2 – Master Intelligence Artificielle et Cybersécurité**  
Université Sultan Moulay Slimane (USMS), FST Béni Mellal.

## Project Overview

This project investigates the ability of Machine Learning models to detect web injection attacks from HTTP activity logs.

Models are trained on the filtered **CSIC 2010 HTTP dataset** and evaluated on independently collected HTTP requests from **OWASP Juice Shop** in an isolated local environment.

**Models:**
- Logistic Regression – TF-IDF character n-grams.
- Random Forest – Handcrafted features.
- DistilBERT – Fine-tuned Transformer model.

The main objective is to evaluate how well these models generalize to a different web application and HTTP request format.

---

## Project Structure

```text
web-attack-detection/
│
├── data/                  # Datasets (not versioned)
├── docs/                  # Project documentation and proposal
├── lab/                   # Juice Shop, traffic generators and live tests
├── models/                # Trained models (not versioned)
├── monitoring/            # Prediction monitoring and drift detection
├── notebooks/             # Data exploration and experiments
├── reports/               # Results, figures and final report
├── serving/               # FastAPI prediction service and Dockerfile
├── src/
│   ├── evaluation/        # Evaluation metrics
│   ├── features/          # Handcrafted feature extraction
│   ├── models/            # ML models and DistilBERT
│   └── preprocessing/     # HTTP request normalization
│
├── tests/                 # Automated tests
├── .gitignore
├── README.md
└── requirements.txt
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/SalmaAitKaddour/web-attack-detection.git

cd web-attack-detection
```

### 2. Create a Python virtual environment

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

# Git Collaboration Workflow

All team members must follow the same Git workflow to avoid conflicts, accidental overwrites and configuration problems.

## 1. Branch Strategy

We use the following branch structure:

| Branch | Purpose |
|---|---|
| `main` | Stable and validated project version |
| `develop` | Shared integration branch |
| `feature/*` | Individual development branches |

**Important:**
- Never develop directly on `main`.
- Never push directly to `develop`.
- Each collaborator must work on their own feature branch.
- All contributions must be integrated through Pull Requests.

## 2. Initial Setup (First Time Only)

After cloning the repository, each collaborator must retrieve the latest remote branches:

```bash
git fetch origin
```

Verify available branches:

```bash
git branch -a
```

You should see:

```text
main
remotes/origin/main
remotes/origin/develop
```

Create your personal branch from the shared `develop` branch.

**Example: DistilBERT developer**

```bash
git switch -c feature/distilbert origin/develop
```

**Example: Logistic Regression developer**

```bash
git switch -c feature/logistic-regression origin/develop
```

**Example: Random Forest developer**

```bash
git switch -c feature/random-forest origin/develop
```

**Example: Juice Shop lab developer**

```bash
git switch -c feature/juice-shop-lab origin/develop
```

Publish your branch to GitHub:

```bash
git push -u origin feature/your-feature
```

Replace `your-feature` with your actual branch name.

## 3. Daily Development Workflow

Before starting a new working session, synchronize your local repository with the latest integrated changes.

```bash
# Update remote branch information
git fetch origin

# Switch to develop
git switch develop

# Update develop
git pull origin develop

# Return to your personal branch
git switch feature/your-feature

# Integrate the latest develop changes
git merge develop
```

Now you can continue working on your assigned task.

## 4. Save and Push Your Changes

After implementing and testing your changes:

```bash
# Check modified files
git status

# Stage your changes
git add .

# Commit your work
git commit -m "feat: describe your changes"

# Push your branch
git push
```

Use clear and descriptive commit messages.

Examples:

```text
feat: implement DistilBERT fine-tuning
feat: add HTTP request normalization
fix: correct SQL injection feature extraction
test: add preprocessing unit tests
docs: update project documentation
```

## 5. Create a Pull Request

When your task is ready:

1. Open the GitHub repository.
2. Navigate to **Pull Requests**.
3. Click **New Pull Request**.
4. Select the following branches:

   - **Base:** `develop`
   - **Compare:** `feature/your-feature`

5. Describe your implementation and tests.
6. Request a review from another team member.
7. Wait for approval before merging.

**Never merge directly into `main` through a feature branch.**

After successful review and integration, the team leader can merge `develop` into `main` when a stable project version is ready.

## 6. Important Git Rules

- Always check `git status` before committing.
- Always synchronize with `develop` before starting a new task.
- Never work on another member's feature branch without coordination.
- Do not commit temporary files, virtual environments, datasets or trained model checkpoints.
- Do not force-push shared branches.
- Avoid modifying shared configuration files without informing the team.
- Keep commits small and focused on one task.
- Test your code before opening a Pull Request.

---

## Dataset Policy

| Dataset | Usage |
|---|---|
| CSIC 2010 | Training and validation |
| OWASP Juice Shop | Final external evaluation |

**Important:** The Juice Shop test dataset must never be used for training, hyperparameter tuning or decision-threshold selection.

All datasets must be documented and stored locally or in an appropriate shared storage solution. Large datasets must not be committed directly to Git.

See `data/README.md` for dataset instructions.

---

## Development Guidelines

- Use Python for preprocessing, training and evaluation.
- Keep reusable code inside `src/`.
- Use notebooks for exploration and experimentation.
- Keep model implementations independent.
- Use a common input representation for all models.
- Maintain consistent prediction outputs:

```python
{
    "label": 1,
    "score": 0.97
}
```

Where:
- `0` = Normal request.
- `1` = Injection request.
- `score` = Predicted injection probability or confidence score, consistently defined by each model.

- Write tests for reusable components.
- Document important implementation decisions.

---

## Evaluation Metrics

The project evaluates models using:

- Precision
- Recall (Injection class)
- F1-score
- Accuracy
- Confusion Matrix
- Prediction latency
- False positive rate during live testing

Accuracy must never be reported alone. Injection Recall and F1-score are the primary evaluation metrics.

---

## MLOps

The project includes:

- FastAPI model serving.
- Docker containerization.
- Prediction logging and latency monitoring.
- Input drift monitoring.
- Model and experiment versioning.
- Periodic evaluation using labelled traffic replays.

---

## Security and Ethics

All experiments must be performed exclusively in our own isolated local laboratory.

- OWASP Juice Shop runs locally through Docker.
- The application is accessible through `localhost:3000`.
- No third-party system may be targeted.
- SQL injection and XSS experiments must remain within the authorized lab.
- The live detection system operates in alert-only mode.

---

## Team

**Group 2 – Master Intelligence Artificielle et Cybersécurité**

Université Sultan Moulay Slimane – FST Béni Mellal.