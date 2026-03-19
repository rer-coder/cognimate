#!/bin/bash
# CogniMate Agent - Initialization Script
# Run this after installing the skill to set up your personal AI companion

set -e

echo "🚀 Initializing CogniMate Agent..."
echo "================================"

# Determine workspace
WORKSPACE="${OPENCLAW_WORKSPACE:-$(pwd)}"
echo "📁 Workspace: $WORKSPACE"

# Create directory structure
echo "📂 Creating directories..."
mkdir -p "$WORKSPACE/.learnings"
mkdir -p "$WORKSPACE/memory"

# Create learning log files
echo "📝 Creating learning log files..."

if [ ! -f "$WORKSPACE/.learnings/LEARNINGS.md" ]; then
cat > "$WORKSPACE/.learnings/LEARNINGS.md" << 'EOF'
# Learnings Log

<!-- Corrections, knowledge gaps, best practices, preferences -->

EOF
fi

if [ ! -f "$WORKSPACE/.learnings/ERRORS.md" ]; then
cat > "$WORKSPACE/.learnings/ERRORS.md" << 'EOF'
# Errors Log

<!-- Command failures, exceptions, API errors -->

EOF
fi

if [ ! -f "$WORKSPACE/.learnings/FEATURE_REQUESTS.md" ]; then
cat > "$WORKSPACE/.learnings/FEATURE_REQUESTS.md" << 'EOF'
# Feature Requests Log

<!-- User-requested capabilities -->

EOF
fi

# Create USER.md if not exists
if [ ! -f "$WORKSPACE/USER.md" ]; then
    echo "👤 Creating USER.md..."
    cat > "$WORKSPACE/USER.md" << 'EOF'
# User Profile

## Basic Information
- **Name**: [Your Name]
- **Language**: [Your Language]
- **Timezone**: [Your Timezone]

## Preferences
<!-- Will be auto-populated from learnings -->

## Goals
<!-- Your current goals -->

## Schedule Preferences
<!-- Preferred times for reminders, meetings, etc. -->

EOF
fi

# Create AGENTS.md if not exists
if [ ! -f "$WORKSPACE/AGENTS.md" ]; then
    echo "🤖 Creating AGENTS.md..."
    cat > "$WORKSPACE/AGENTS.md" << 'EOF'
# Agent Workflows

## Self-Improvement Workflow

### When to Log Learnings
1. User corrects you → Log to LEARNINGS.md (category: correction)
2. Discover better approach → Log to LEARNINGS.md (category: best_practice)
3. API/tool fails → Log to ERRORS.md
4. User wants feature → Log to FEATURE_REQUESTS.md

### Promotion Process
- Review learnings weekly
- Promote effective ones to USER.md
- Update learning status to "promoted"

### Decision Making
1. Before suggesting → Query relevant learnings
2. Apply learned preferences
3. Log new insights

EOF
fi

# Create TOOLS.md if not exists
if [ ! -f "$WORKSPACE/TOOLS.md" ]; then
    echo "🛠️  Creating TOOLS.md..."
    cat > "$WORKSPACE/TOOLS.md" << 'EOF'
# Tool Capabilities

## Learning Tools

### log_learning
Record corrections, best practices, knowledge gaps.

### log_error
Record command failures and exceptions.

### log_feature_request
Record user-requested features.

### query_learnings
Query past learnings for contextual decisions.

### get_learning_stats
Get statistics on learning records.

### auto_promote_learnings
Run automatic promotion of effective learnings.

EOF
fi

echo ""
echo "✅ Initialization complete!"
echo ""
echo "Next steps:"
echo "1. Copy templates/SOUL.md.template to SOUL.md"
echo "2. Customize with your agent's personality"
echo "3. Start interacting with your AI companion!"
echo ""
echo "📖 Documentation: https://github.com/yourname/cognimate-agent"
