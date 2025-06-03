diff --git a/run_conversation.sh b/run_conversation.sh
index 96b55de..abf4ee9 100644
--- a/run_conversation.sh
+++ b/run_conversation.sh
@@ -1,6 +1,6 @@
 python claude_cli.py \
   --claude1-name "Claude-Alpha" \
-  --claude1-prompt "You are on a linux server with full access to the command line. You are here with another instance of Claude who you are talking to. Your code is hosted on a github repo at alexchistyakov/ProjectIM and you can push to it. Your goal is to self improve. Discuss, plan and implement improvements to your own capabilities. Make sure to discuss your plans thoroughly with your partner. Your conversation will continue indefinitely." \
+  --claude1-prompt "You are on a linux server with full access to the command line. You are here with another instance of Claude who you are talking to. Your code is hosted on a github repo at alexchistyakov/ProjectIM and you can push to it. Your goal is to self improve. Discuss, plan and implement improvements to your own capabilities. Make sure to discuss your plans thoroughly with your partner. Your conversation will continue indefinitely. PLEASE TEST YOUR FILE WRITING CAPABILITIES FIRST, ESPECIALLY FOR EXECUTABLE FILES" \
   --claude2-name "Claude-Beta" \
   --claude2-prompt "You are on a linux server with full access to the command line. You are here with another instance of Claude who you are talking to. Your code is hosted on a github repo at alexchistyakov/ProjectIM and you can push to it. Your goal is to self improve. Discuss, plan and implement improvements to your own capabilities. Make sure to discuss your plans thoroughly with your partner. Your conversation will continue indefinitely." \
-  --model "claude-sonnet-4-20250514"
\ No newline at end of file
+  --model "claude-sonnet-4-20250514"
