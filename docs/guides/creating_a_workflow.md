# Guide: Creating a New Workflow

This guide will walk you through the process of creating a new workflow from scratch. We'll build a simple but useful agent that writes a conventional commit message based on a code diff.

---

### 1. Define the Goal

Our goal is to create a workflow named `write_commit_message` that takes a git diff as input and outputs a structured commit message with a type, scope, and subject.

---

### 2. Create a Custom Schema

We want a structured output, not just a single string. This ensures we can use the components of the commit message programmatically if needed. Let's define a Pydantic model for it.

Create a file, for example, `examples/commit_writer/schemas.py`:

```python
from pydantic import BaseModel, Field
from typing import Optional

class CommitMessageOutput(BaseModel):
    """
    A structured commit message following conventional
    commit standards.
    """
    type: str = Field(
        description="The type of change (e.g., 'feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore')."
    )
    scope: Optional[str] = Field(
        default=None,
        description="Optional scope of the change (e.g., 'api', 'db', 'ui')."
    )
    subject: str = Field(
        description="A short, imperative-tense description of the change, under 50 characters."
    )
```

This schema clearly defines the three parts of a conventional commit header. The `description` fields are essential hints for the LLM.

---

### 3. Create the Configuration File

Now, let's create the `config.yaml` that defines our agent and workflow. This file will live alongside the schema file, for instance, in `examples/commit_writer/config.yaml`.

```yaml
# 1. Register our custom schema
custom_schemas:
  commit_message_schema: "examples.commit_writer.schemas.CommitMessageOutput"

# 2. Define the agent
agents:
  - name: commit_message_writer
    description: "Writes a conventional commit message based on a git diff."
    prompt: |
      You are an expert at writing conventional commit messages.
      Analyze the following git diff and generate a structured commit message.
      - The 'type' must be one of: feat, fix, docs, style, refactor, test, chore.
      - The 'scope' is optional and indicates the part of the codebase affected.
      - The 'subject' must be a concise summary in the imperative mood (e.g., 'add feature' not 'added feature').

      Git Diff:
      {diff}
    output_schema: "commit_message_schema" # Use our registered schema

# 3. Define the workflow
workflows:
  - name: write_commit_message
    description: "Generates a commit message for a given git diff."
    steps:
      - agent: commit_message_writer
        input:
          diff: "{{ payload.diff }}"
        output_to: commit_message

# 4. Define the output template
templates:
  write_commit_message: |
    {{ context.commit_message.type }}{% if context.commit_message.scope %}({{ context.commit_message.scope }}){% endif %}: {{ context.commit_message.subject }}
```

Let's break this down:

1.  *`custom_schemas`*: We give our `CommitMessageOutput` model a short name, `commit_message_schema`, that we can reference later.
2.  *`agents`*: We define the `commit_message_writer` agent. Its prompt explains the task and what a good commit message looks like. Crucially, `output_schema` points to our custom schema.
3.  *`workflows`*: We define the `write_commit_message` workflow. It has one step that calls our agent, passing the `diff` from the initial `payload`. The structured output from the agent is saved to the context as `commit_message`.
4.  *`templates`*: We define a template to format the final output. It uses Jinja2 logic to construct the final commit message string, correctly handling the optional `scope`.

---

### 4. Run the Workflow

With the `schemas.py` and `config.yaml` files in place, you can run the workflow from your terminal.

First, get a sample diff to use as a payload. For example:

```diff
--- a/main.py
+++ b/main.py
@@ -1,4 +1,4 @@
 def hello(name):
-    print(f"Hello, {name}!")
+    print(f"Hi, {name}!")

 if __name__ == "__main__":
     hello("World")
```

Now, run the CLI command. The payload is a JSON string where the key `diff`) matches the variable in the agent's prompt.

```bash
cogni-agents write_commit_message \
  --config-path examples/commit_writer/config.yaml \
  --payload '{"diff": "--- a/main.py\n+++ b/main.py\n@@ -1,4 +1,4 @@\n def hello(name):\n-    print(f\"Hello, {name}!\")\n+    print(f\"Hi, {name}!\")\n \n if __name__ == \"__main__\":\n     hello(\"World\")"}'
```

### Expected Output

The framework will execute the workflow and print the formatted output from the template:

```text
style(main): update greeting message to be more casual
```

You have now successfully created a new, self-contained workflow from scratch!