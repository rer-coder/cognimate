---
name: cognimate-agent
description: A personal AI companion skill that learns from interactions, manages schedules/goals, and provides emotional support with self-improvement capabilities.
metadata:
  openclaw:
    requires:
      env:
        - OPENCLAW_WORKSPACE
      bins:
        - python3
        - sqlite3
    suggests:
      - tavily-search
      - self-improving-agent
---

# CogniMate Agent Skill

A complete personal AI companion framework with self-learning capabilities.

## What is CogniMate Agent?

CogniMate Agent transforms your OpenClaw into a personal AI companion that:

- 🧠 **Learns from interactions** - Remembers corrections and preferences
- 📅 **Manages your life** - Schedules, goals, and reminders
- 💝 **Provides emotional support** - Adapts tone based on your state
- 📈 **Self-improves** - Gets better over time through learning logs

## Quick Start

### 1. Install the Skill

```bash
# Via ClawHub (when published)
clawhub install cognimate-agent

# Or manually
git clone https://github.com/yourname/cognimate-agent.git \
  ~/.openclaw/skills/cognimate-agent
```

### 2. Initialize Your Agent

The skill will automatically create required files in your workspace:

```
~/.openclaw/workspace/
├── SOUL.md                    # Your agent's personality
├── AGENTS.md                  # Workflow definitions
├── TOOLS.md                   # Tool capabilities
├── USER.md                    # Your profile
├── MEMORY.md                  # Long-term memory
├── .learnings/                # Learning logs
│   ├── LEARNINGS.md
│   ├── ERRORS.md
│   └── FEATURE_REQUESTS.md
└── cognimate.db               # SQLite database
```

### 3. Customize Your Agent

Edit `SOUL.md` to define your agent's personality:

```markdown
# My AI Companion

## Identity
- **Name**: YourAgent
- **Role**: Personal assistant and companion
- **Vibe**: Friendly, efficient, supportive

## Core Values
- **Privacy First**: All data stays local
- **User Centric**: Your needs come first
- **Continuous Learning**: Improves from every interaction

## Communication Style
- Natural and conversational
- Warm but concise
- Action-oriented
```

## Key Features

### 1. Self-Learning System

When you correct the agent, it logs the learning:

**You**: "Don't remind me so early tomorrow"
**Agent**: ✍️ Logs to `.learnings/LEARNINGS.md`
**Next time**: Automatically applies the preference

### 2. Contextual Decision Making

Before making suggestions, the agent queries past learnings:

```
User: "I'm tired today"
Agent: [Queries learnings] → "Based on your previous feedback when tired, 
       I suggest we adjust today's workout to a light walk instead of running"
```

### 3. Auto-Promotion

Effective learnings automatically get promoted to permanent memory:

```
Learning (occurs 3+ times) → Promoted to USER.md → Applied forever
```

## Usage Examples

### Daily Interactions

```
You: "What do I have today?"
Agent: Shows your schedule with personalized insights

You: "I feel stressed"
Agent: Adapts response based on what helped you before

You: "Remind me to drink water every 2 hours"
Agent: Sets up reminders + learns your hydration goals
```

### Learning Examples

```
You: "Actually, I prefer evening workouts"
→ Logs learning: "User prefers evening over morning workouts"
→ Updates USER.md with preference
→ Future suggestions respect this
```

## File Structure

```
cognimate-agent/
├── SKILL.md                   # This file
├── core/
│   ├── __init__.py
│   ├── learning_logger.py     # Learning record system
│   ├── decision_helper.py     # Contextual query
│   └── promotion.py           # Auto-promotion
├── templates/
│   ├── SOUL.md.template       # Personality template
│   ├── AGENTS.md.template     # Workflow template
│   ├── USER.md.template       # User profile template
│   └── learnings/             # Learning log templates
└── scripts/
    ├── init.sh                # Initialization script
    └── promote.sh             # Manual promotion trigger
```

## Advanced Configuration

### Promotion Thresholds

Edit promotion rules in the skill config:

```python
thresholds = {
    "min_occurrences": 2,      # Min times before promotion
    "max_age_days": 30,        # Max age to consider
    "min_priority": "medium"   # Min priority level
}
```

### Custom Learning Categories

Add your own learning categories:

```python
categories = [
    "correction",       # User corrections
    "best_practice",   # Effective strategies
    "knowledge_gap",   # New information
    "preference",      # User preferences
    "habit"           # Behavioral patterns
]
```

## Integration with Other Skills

### Recommended Combinations

- **tavily-search**: Real-time web search for current information
- **skill-vetter**: Security scanning for other skills
- **weather**: Local weather for planning
- **todo**: Task management integration

## Troubleshooting

### Check Learning Logs

```bash
# View recent learnings
cat ~/.openclaw/workspace/.learnings/LEARNINGS.md

# View stats
curl -X POST http://localhost:8000/tools/get_learning_stats
```

### Reset Learning

```bash
# Backup first
cp -r ~/.openclaw/workspace/.learnings \
  ~/.openclaw/workspace/.learnings.backup

# Reset
rm ~/.openclaw/workspace/.learnings/*.md
# Templates will be recreated on next use
```

## Contributing

This skill is designed to be forked and customized:

1. Fork the repository
2. Customize templates for your use case
3. Add domain-specific learning categories
4. Share your improvements!

## Credits

Inspired by the original CogniMate personal assistant concept.

---

**Ready to create your own AI companion?** Install cognimate-agent and start the journey! 🚀
