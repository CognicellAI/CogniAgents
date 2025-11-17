# Guide: Creating a New Workflow

This guide will walk you through the process of creating a new workflow from scratch. We'll build a simple agent that writes a commit message based on a code diff.

### 1. Define the Goal

Our goal is to create a workflow named `write_commit_message` that takes a git diff as input and outputs a structured commit message.

### 2. Create a Custom Schema

We want a structured output, so let's define a Pydantic model for it.

Create a file `my_app/schemas.py`:
