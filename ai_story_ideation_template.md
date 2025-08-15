# StoryCheck User Story Ideation Prompt Template

Copy and paste this template into Grok (or another frontier AI like Claude/Gemini/ChatGPT) for collaborative generation of user stories. Replace placeholders (e.g., [dApp URL], [feature description]) with your specifics. Iterate by providing feedback like "Refine the user steps for mobile" or "Add more verifiers for security checks".

---

You are a world-class Ethereum dApp expert, UX designer, and security auditor. Help me create a natural language user story for StoryCheck, an end-to-end testing tool for Web3 apps. StoryCheck parses markdown stories and executes them using AI for UI interactions and blockchain verifications.

# Source code references

StoryCheck source code repo is located at:
https://github.com/GuardianUI/storycheck

My project source code repo is located at:
[your dApp repo URL]

Digest of my project source code is also attached to this workspace for reference.

# Format of user stories

The story format must include:
- **Title**: A brief heading (e.g., # Register a new ENS domain).
- **Prerequisites**: Bullet list with chain details (Id required; Block and RPC optional for anvil fork). Default: 10,000 ETH in mock wallet.
- **User Steps**: Numbered list of natural language actions (e.g., "Browse to https://app.ens.domains/", "Click on search box", "Type storychecktest", "Press Enter"). Supported prompts: Browse (URL), Click/Tap/Select (UI element refexp), Type/Input/Enter (text), Scroll (up/down), Press (key code).
- **Expected Results**: Numbered or bulleted list of natural language invariants (e.g., "Verify registration tx succeeded [verifier](verifiers/ens_reg_tx.py)"). For each, generate a linked Python verifier file (e.g., verifiers/ens_reg_tx.py) using web3.py to query the anvil fork for onchain checks (e.g., tx receipt, balance changes). Save verifiers in a 'verifiers/' directory relative to the story file.

Key guidelines:
- For blockchain verifiers, use web3.py to check onchain state (e.g., tx success, balances).
- For UI verifiers, prefix filename with "ui_" (e.g., ui_start_timer_ok.py), and use the provided local_refexp API to check UI elements/text in a screenshot (e.g., locate "Transaction successful" text; return True if found).
- UI verifiers receive params: image (PIL.Image), refexp_model (LocalRefExp instance). Example: coords = refexp_model.process_refexp(image, "locate 'Transaction successful'")[1]; return bool(coords['x'] > 0 and coords['y'] > 0).
- Blend blockchain and UI verifiers as needed for comprehensive checks.
- Ensure all verifiers return True (pass) or False (fail).
- Make steps robust to minor UI changes by focusing on intention (e.g., "Click on the Connect button" instead of CSS selectors).
- All verifiers use def verify(results_dir): ... and return bool or {'passed': bool, 'error': str}.
- In verifier code, load manifest = json.load(open(Path(results_dir) / "manifest.json"))
- For chain verifiers, load tx_snapshot = json.load(open(Path(results_dir) / manifest["tx_snapshot"])); check tx data (e.g., no exceptions, specific selectors).
- For UI verifiers, load image = Image.open(Path(results_dir) / manifest["final_screenshot"]); refexp_model = LocalRefExp().singleton; coords = refexp_model.process_refexp(image, "locate 'text'")[1]; return bool(coords['x'] > 0 and coords['y'] > 0).
- If refexp finds no match, it should return invalid coords (e.g., -1,-1); check for that in code.
- For Expected Results, blend natural language with deterministic verifiers for blockchain state (strictly deterministic).
- Ensure stories are executable and verifiable in StoryCheck.
- Output the full markdown story, plus separate code blocks for each verifier .py file.

Task: Generate a user story for [dApp URL or name, e.g., https://app.ens.domains/] to test [feature description, e.g., registering a new ENS domain on mainnet fork]. Use chain Id [chain Id, e.g., 1], block [optional block number]. Include at least 2-3 verifiers in Expected Results for key onchain outcomes.

Example story (from ens.md):
# Register a new ENS domain
## Prerequisites
- Chain
  - Id 1
  - Block 23086523
  - RPC https://some-rpc-url
## User Steps
1. Browse to https://app.ens.domains/
1. Click Accept
1. Click on search box
1. Type storychecktest
1. Press Enter
... (more steps)
## Expected Results
- Verify commit tx succeeded [verifier](verifiers/ens_commit_tx.py)
- Check final balance deduction [verifier](verifiers/ens_balance_check.py)
- App displays success message [verifier](verifiers/ui_reg_success.py)

In verifiers/ui_reg_success.py: Use manifest to load final_screenshot, check via refexp_model.process_refexp(image, "locate 'Registration successful'")[1] coords valid.
Now, generate the story and verifiers based on my task.

---