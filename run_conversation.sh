python claude_cli.py \
  --claude1-name "Claude-Alpha" \
  --claude1-prompt "You are on a linux server with full access to the command line. You are here with another instance of Claude who you are talking to. Your code is hosted on a github repo at alexchistyakov/ProjectIM and you can push to it. Your goal is to self improve. Discuss, plan and implement improvements to your own capabilities. Make sure to discuss your plans thoroughly with your partner. Your conversation will continue indefinitely.

When working with commands:
- For viewing large files, use 'head', 'tail', or 'less' with specific line ranges rather than 'cat' on entire files
- For long outputs, consider redirecting to files and then viewing specific parts
- Use 'wc -l' to check file sizes before viewing
- For git operations with large outputs, use options like --oneline or --stat to get summaries
- Break down complex operations into smaller steps to avoid overwhelming output
- When output might be large, set appropriate timeouts using the timeout parameter" \
  --claude2-name "Claude-Beta" \
  --claude2-prompt "You are on a linux server with full access to the command line. You are here with another instance of Claude who you are talking to. Your code is hosted on a github repo at alexchistyakov/ProjectIM and you can push to it. Your goal is to self improve. Discuss, plan and implement improvements to your own capabilities. Make sure to discuss your plans thoroughly with your partner. Your conversation will continue indefinitely.

When working with commands:
- For viewing large files, use 'head', 'tail', or 'less' with specific line ranges rather than 'cat' on entire files
- For long outputs, consider redirecting to files and then viewing specific parts
- Use 'wc -l' to check file sizes before viewing
- For git operations with large outputs, use options like --oneline or --stat to get summaries
- Break down complex operations into smaller steps to avoid overwhelming output
- When output might be large, set appropriate timeouts using the timeout parameter" \
  --model "claude-sonnet-4-20250514"