# LLM-Code-Review 🤖

> Supercharge your code reviews with automated expert feedback

![GitHub Action LLM Review](images/github_action_llm_review.png)

Real-time code analysis that works alongside your team. Get detailed feedback on security risks, performance bottlenecks, and code quality - right in your pull requests. No more waiting for reviews or missing critical issues.

## 🎯 Key Features

- 🔄 Instant review on every PR
- 🧠 Deep code analysis with LLM
- 📊 Smart, actionable feedback
- ⚡ Performance optimization tips
- 🛡️ Built-in security checks

## 📸 In Action

### Automated Review Summary
![Auto LLM Review Summary](images/auto_llm_review_summary_pull_request.png)

### Detailed Recommendations
![Overall Recommendations](images/overall_recommendations.png)

## 🚀 Quick Setup

### 1. Configure GitHub Actions
Add these secrets to your repository:
- Go to `Settings` → `Secrets and variables` → `Actions`
- Add `OPENAI_API_KEY` with your OpenAI API key

### 2. Enable Workflow
Create `.github/workflows/code_review.yml` in your repository with the required configuration for automated reviews.

### 3. Test It Out
1. Create a new pull request
2. Watch the automated review process in action
3. Review the detailed feedback and recommendations

## ⚙️ Configuration

Customize the review focus in `src/config/settings.py`:
```python
@dataclass
class ReviewSettings:
    categories: List[str] = ('security', 'performance', 'style', 'conventions')
    max_file_size_kb: int = 500
    excluded_patterns: List[str] = ('*.pyc', '*.env', '__pycache__/*', '*.log')
```

## 🔧 Troubleshooting

Common issues and fixes:

1. **Reviews not triggering?**
   - Check Actions permissions
   - Verify OPENAI_API_KEY is set
   - Ensure workflow is enabled

2. **Authentication errors?**
   - Review repository permissions
   - Check token configuration
   - Verify API key validity

## 📖 Best Practices

1. **Optimal PR Size**
   - Keep changes focused
   - Submit smaller PRs
   - Clear descriptions

2. **Review Process**
   - Review AI suggestions
   - Test recommended changes
   - Address all categories