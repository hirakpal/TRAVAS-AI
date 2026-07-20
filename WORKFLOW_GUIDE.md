# Development Workflow - Pull & Test Guide

## 📋 Simple Workflow for Every Change

### **The Process (5 Steps)**

```
1. Make Changes (local workspace)
   ↓
2. Push to GitHub
   ↓
3. Pull in Cloned Repo
   ↓
4. Test Changes
   ↓
5. Verify Success
```

---

## 🔄 Complete Workflow

### **Step 1: Make Changes in Local Workspace**

```bash
# Work in local workspace
cd D:\BuildfastwithAI\Capstone\TRAVAS-AI\main

# Create/edit files
# e.g., Create annapurna_agent.py
echo "# New Food Agent" > agents/annapurna_agent.py

# Test locally if you want
python demo_atithi.py
```

---

### **Step 2: Push to GitHub**

```bash
cd D:\BuildfastwithAI\Capstone\TRAVAS-AI\main

# Check what changed
git status

# Add all changes
git add .

# Commit with clear message
git commit -m "feat: Add Annapurna Food Agent

- Restaurant recommendation specialist
- 3 food-related tools
- Mock restaurant database"

# Push to GitHub
git push origin main

# Verify push was successful
git log --oneline | head -5
# Should show your commit at the top
```

---

### **Step 3: Pull in Cloned Repo**

```bash
# Go to cloned repo
cd ~/TRAVAS-AI

# Pull latest changes
git pull origin main

# Verify files were pulled
ls -la agents/
# Should show new/updated files
```

---

### **Step 4: Test Changes**

```bash
# Install dependencies (if needed)
pip install -r requirements.txt

# Run appropriate test
python run_test.py          # For Atithi tests
python demo_sanchalak.py    # For Sanchalak demo
python demo_annapurna.py    # For new agent

# Or test specific scenario
python -c "from agents.annapurna_agent import AnnapurnaAgent; print('✅ Import successful')"
```

---

### **Step 5: Verify Success**

```bash
# Check status
git status
# Should show: "On branch main, nothing to commit"

# Verify changes
cat agents/annapurna_agent.py
# Should show new code

# Test works
python demo_annapurna.py
# Should run without errors
```

---

## 📝 Quick Reference

### **Push Changes (3 commands)**

```bash
cd D:\BuildfastwithAI\Capstone\TRAVAS-AI\main
git add . && git commit -m "your message" && git push origin main
```

### **Pull Changes (2 commands)**

```bash
cd ~/TRAVAS-AI
git pull origin main
```

### **Full Cycle (One-liner)**

```bash
# In local workspace: push
cd D:\BuildfastwithAI\Capstone\TRAVAS-AI\main && git add . && git commit -m "feat: description" && git push origin main

# Then in cloned repo: pull and test
cd ~/TRAVAS-AI && git pull origin main && python demo_sanchalak.py
```

---

## 🎯 Different Types of Changes

### **A. Bug Fix**

**Local:**
```bash
cd D:\BuildfastwithAI\Capstone\TRAVAS-AI\main
# Fix the bug in a file
git add .
git commit -m "fix: Fix hotel tool bug in search_hotels"
git push origin main
```

**Cloned:**
```bash
cd ~/TRAVAS-AI
git pull origin main
python run_test.py  # Test the fix
```

---

### **B. New Feature (New Agent)**

**Local:**
```bash
cd D:\BuildfastwithAI\Capstone\TRAVAS-AI\main
# Create agents/annapurna_agent.py
# Create demo_annapurna.py
git add .
git commit -m "feat: Add Annapurna Food Agent"
git push origin main
```

**Cloned:**
```bash
cd ~/TRAVAS-AI
git pull origin main
ls agents/annapurna_agent.py  # Verify file exists
python demo_annapurna.py       # Test it
```

---

### **C. Documentation Update**

**Local:**
```bash
cd D:\BuildfastwithAI\Capstone\TRAVAS-AI\main
# Edit SANCHALAK_GUIDE.md
git add SANCHALAK_GUIDE.md
git commit -m "docs: Update Sanchalak documentation"
git push origin main
```

**Cloned:**
```bash
cd ~/TRAVAS-AI
git pull origin main
cat SANCHALAK_GUIDE.md  # Read the docs
```

---

### **D. Configuration Change**

**Local:**
```bash
cd D:\BuildfastwithAI\Capstone\TRAVAS-AI\main
# Edit requirements.txt or .env.example
git add .
git commit -m "chore: Update dependencies"
git push origin main
```

**Cloned:**
```bash
cd ~/TRAVAS-AI
git pull origin main
pip install -r requirements.txt  # Install updates
python run_test.py               # Test
```

---

## ✅ Testing Checklist

After pulling, always test:

```bash
# 1. Check files exist
ls agents/
ls tools/
ls models/

# 2. Run imports
python -c "from agents.atithi_agent import AtithiAgent; print('✅ Atithi OK')"
python -c "from agents.sanchalak_agent import SanchalakAgent; print('✅ Sanchalak OK')"

# 3. Run demos
python demo_atithi.py        # Demo 1
python demo_sanchalak.py     # Demo 2

# 4. Run tests
python run_test.py           # Full test suite

# 5. Check logs
ls logs/                      # Verify logging works
```

---

## 🐛 If Something Goes Wrong

### **Scenario 1: Pull Conflict**

```bash
cd ~/TRAVAS-AI

# See what's conflicting
git status

# Option A: Keep your changes
git pull --ours origin main

# Option B: Take their changes
git pull --theirs origin main

# Option C: Abort and try again
git merge --abort
git pull origin main
```

### **Scenario 2: Import Error**

```bash
cd ~/TRAVAS-AI

# Re-install dependencies
pip install -r requirements.txt

# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -name "*.pyc" -delete

# Try again
python run_test.py
```

### **Scenario 3: Forgot to Pull**

```bash
cd ~/TRAVAS-AI

# Check if behind
git status

# Pull latest
git pull origin main

# Compare versions
git log --oneline | head -3
```

---

## 📊 Status Commands

Check status anytime:

```bash
# See current branch and status
git status

# See recent commits
git log --oneline | head -5

# See what's different from GitHub
git diff origin/main

# See file changes
git diff agents/atithi_agent.py

# See branches
git branch -a

# See remote info
git remote -v
```

---

## 🔄 Typical Day Workflow

### **Morning: Start Work**

```bash
# Go to cloned repo
cd ~/TRAVAS-AI

# Pull latest changes
git pull origin main

# Check what's new
git log --oneline | head -3

# Install any new dependencies
pip install -r requirements.txt

# Test everything still works
python run_test.py
```

### **During Day: Make Changes**

```bash
# Work in local workspace
cd D:\BuildfastwithAI\Capstone\TRAVAS-AI\main

# Make changes (edit files)
# e.g., Add new feature to atithi_agent.py

# Test changes
python run_test.py

# When satisfied, push
git add .
git commit -m "feat: Add new feature"
git push origin main
```

### **Other Developers: Get Changes**

```bash
# They pull changes
cd ~/TRAVAS-AI
git pull origin main

# Test changes
python run_test.py

# Verify it works for them
python demo_atithi.py
```

---

## 📋 Commit Message Format

Keep commits clear:

```
feat:   New feature (New agent, new tool)
fix:    Bug fix (Fixed hotel search)
docs:   Documentation (Updated guides)
chore:  Maintenance (Updated dependencies)
test:   Add tests (New test scenarios)
```

**Examples:**
```
git commit -m "feat: Add Annapurna Food Agent"
git commit -m "fix: Fix search_hotels budget filter"
git commit -m "docs: Update SANCHALAK_GUIDE.md"
git commit -m "chore: Update requirements.txt"
git commit -m "test: Add restaurant filter tests"
```

---

## 🚀 Quick Commands (Copy-Paste Ready)

### **Push from Local**
```bash
cd D:\BuildfastwithAI\Capstone\TRAVAS-AI\main && git add . && git commit -m "feat: description" && git push origin main
```

### **Pull in Cloned**
```bash
cd ~/TRAVAS-AI && git pull origin main && echo "✅ Pulled successfully"
```

### **Full Test Suite**
```bash
cd ~/TRAVAS-AI && python run_test.py
```

### **Interactive Demo**
```bash
cd ~/TRAVAS-AI && python demo_sanchalak.py
```

### **Check Status**
```bash
cd ~/TRAVAS-AI && git status && git log --oneline | head -3
```

---

## 📈 Summary

| Action | Command | Where |
|--------|---------|-------|
| **Make changes** | Edit files | `D:\BuildfastwithAI\Capstone\TRAVAS-AI\main` |
| **Push to GitHub** | `git add . && git commit -m "..." && git push` | Local |
| **Pull from GitHub** | `git pull origin main` | `~/TRAVAS-AI` |
| **Test changes** | `python run_test.py` or `python demo_*.py` | `~/TRAVAS-AI` |
| **Check status** | `git status` | Anywhere |

---

**That's the workflow!** 🔄

For every change:
1. Push from local → GitHub
2. Pull in cloned → Your machine
3. Test → Verify it works

Simple and consistent! 🚀
