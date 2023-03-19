# StoryCheck

StoryCheck for Web3 apps. Provides a web app playground as well as an API. Both served via Gradio on port 7860.

```mermaid
graph TD;
    A-->B;
    A-->C;
    B-->D;
    C-->D;
```

It takes as input markdown formatted user stories
with steps written in natural language.
Then it parses the text and executes the steps in a virtual web browser
closely emulating
the actions of a real user.

```ml
├─ .\ — "Main StoryCheck python app."
│  ├─ playwright — "Playwright control logic using Python SDK."
│  │  ├─ mock_wallet — "JavaScript mock wallet provider injected in playwright page context."
│  │  │
```
