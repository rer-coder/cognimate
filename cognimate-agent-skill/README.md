# CogniMate Agent

A universal skill that transforms OpenClaw into a personal AI companion with self-learning capabilities.

## 🎯 What You Get

An AI companion that:
- 🧠 **Learns from every interaction** - Remembers corrections and preferences
- 📅 **Manages your life** - Schedules, goals, reminders
- 💝 **Adapts to you** - Emotional support tailored to your needs
- 📈 **Self-improves** - Gets better over time through learning

## 🚀 Quick Start

```bash
# Install the skill
clawhub install cognimate-agent

# Or manually
git clone https://github.com/yourname/cognimate-agent.git \
  ~/.openclaw/skills/cognimate-agent

# Initialize your agent
cd ~/.openclaw/skills/cognimate-agent
./scripts/init.sh

# Customize personality
cp templates/SOUL.md.template SOUL.md
# Edit SOUL.md with your agent's personality
```

## 📁 Structure

```
cognimate-agent/
├── SKILL.md                    # Skill documentation
├── core/                       # Core modules
│   ├── learning_logger.py     # Learning record system
│   ├── decision_helper.py     # Contextual query
│   └── promotion.py           # Auto-promotion
├── templates/                  # Template files
│   ├── SOUL.md.template       # Personality template
│   └── ...
└── scripts/
    └── init.sh                # Initialization script
```

## 💡 Usage Examples

### 1. Daily Interaction

```
You: "What do I have today?"
Agent: Shows schedule with personalized insights from past learnings

You: "I'm tired today"
Agent: Adapts response based on what helped you before
```

### 2. Learning in Action

```
You: "Actually, I prefer evening workouts"
→ Agent logs: "User prefers evening over morning workouts"
→ Updates USER.md
→ Future suggestions respect this preference
```

### 3. Contextual Decisions

```
You: "I'm not feeling great, should I skip my run?"
Agent: [Queries learnings] 
      "Based on previous similar situations, you prefer light walks 
       when tired. Would you like me to adjust today's plan?"
```

## ⚙️ How It Works

### Learning Flow

```
Interaction
    ↓
Trigger detected?
├── Correction → Log to LEARNINGS.md
├── Error → Log to ERRORS.md
└── Feature request → Log to FEATURE_REQUESTS.md
    ↓
Regular review
    ↓
Effective learnings → Promote to USER.md
    ↓
Applied in future decisions
```

### Decision Flow

```
Before making suggestion
    ↓
Query relevant learnings
    ↓
Apply learned preferences
    ↓
Generate personalized response
```

## 🎨 Customization

### Personality (SOUL.md)

Edit `SOUL.md` to define your agent's:
- Name and identity
- Communication style
- Core values
- Capabilities

### Learning Categories

Customize what to track:
- `correction` - User corrections
- `preference` - User preferences
- `best_practice` - Effective strategies
- `habit` - Behavioral patterns

### Promotion Rules

Configure thresholds:
```python
thresholds = {
    "min_priority": "medium",
    "max_age_days": 30,
    "min_occurrences": 2
}
```

## 🔧 API Reference

### Learning Functions

```python
# Log a learning
log_learning({
    "category": "preference",
    "summary": "User prefers X over Y",
    "suggested_action": "Apply X in future"
})

# Query before decision
learnings = query_relevant_learnings("reminder time", area="schedule")

# Auto-promote
auto_promote(dry_run=True)  # Preview
auto_promote(dry_run=False) # Execute
```

## 🤝 Integration

### Recommended Skills

- **tavily-search** - Real-time web search
- **weather** - Local weather
- **todo** - Task management

### Compatible Agents

- OpenClaw
- Claude Code (with adaptations)
- GitHub Copilot (with manual integration)

## 📊 Learning Stats

Check your agent's learning progress:

```bash
curl -X POST http://localhost:8000/tools/get_learning_stats
```

Returns:
```json
{
  "learnings": 15,
  "errors": 3,
  "features": 5,
  "total": 23
}
```

## 📝 Best Practices

1. **Review learnings weekly** - Check `.learnings/LEARNINGS.md`
2. **Promote effective ones** - Run auto-promotion regularly
3. **Keep SOUL.md updated** - Reflect personality evolution
4. **Log everything** - The more data, the better the agent

## 🐛 Troubleshooting

### Check Learning Logs
```bash
cat ~/.openclaw/workspace/.learnings/LEARNINGS.md
```

### Reset Learning
```bash
# Backup first
cp -r ~/.openclaw/workspace/.learnings \
  ~/.openclaw/workspace/.learnings.backup

# Reset
rm ~/.openclaw/workspace/.learnings/*.md
```

## 📄 License

MIT License - Fork and customize for your needs!

## 🙏 Credits

Inspired by the original CogniMate personal assistant concept.

---

**Ready to create your own AI companion?** Install cognimate-agent and start the journey! 🚀
