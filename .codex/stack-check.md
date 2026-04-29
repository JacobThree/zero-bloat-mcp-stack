# Stack Smoke Check

- rtk --version:
  success
  output: rtk 0.37.2

- n2-qln --help:
  success

- context-mode --help:
  success
  output: Context Mode MCP server v1.0.103 running on stdio
  output: Detected runtimes:
  output:   JavaScript: /opt/homebrew/Cellar/node/25.9.0_1/bin/node (v25.9.0)

- python -m graphify --help:
  success
  output: Usage: graphify <command>
  output: 
  output: Commands:
