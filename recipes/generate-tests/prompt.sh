SAMPLE_INPUT=$(cat src/gpt_review/_github.py)
SAMPLE_OUTPUT=$(cat tests/test_github.py)
INPUT=$(cat src/gpt_review/_devops.py)

PROMPT="create tests for the NEW code"

gpt ask \
    --output tsv \
    --max-tokens 8000 \
    "
# SAMPLE
## Request
\`\`\`python
$SAMPLE_INPUT
\`\`\`
## Response
\`\`\`python
$SAMPLE_OUTPUT
\`\`\`

NEW:
## Request
\`\`\`python
$INPUT
\`\`\`

$PROMPT
"
