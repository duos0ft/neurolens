# Developing NeuroLens

This guide covers everything you need to get NeuroLens running locally and contribute to the project.

For a general overview of the project, see [README.md](README.md).

## Tech stack

NeuroLens is built with:

- **Backend:** Python, FastAPI, Pydantic, uv, Ruff, pytest
- **Frontend:** React, TypeScript, Tailwind CSS, Rspack, Yarn
- **Auth & data:** Supabase Auth and Supabase PostgreSQL with Row Level Security
- **AI:** a pretrained sentiment analysis Transformer and the OpenAI API

## Prerequisites

Before getting started, make sure you have:

- [uv](https://docs.astral.sh/uv/)
- Node.js
- [Yarn](https://yarnpkg.com/)
- access to the NeuroLens Supabase project
- an OpenAI API key

---

## Backend setup

From the backend directory, install the dependencies:

```bash
uv sync
```

Then start the API:

```bash
uv run uvicorn app.main:app --reload
```

You can check that everything is running here:

- Health check: `http://127.0.0.1:8000/health`
- API docs: `http://127.0.0.1:8000/docs`

### Useful backend commands

| Task                          | Command                                |
|-------------------------------|----------------------------------------|
| Install dependencies          | `uv sync`                              |
| Add a dependency              | `uv add <package>`                     |
| Add a development dependency  | `uv add --dev <package>`               |
| Run the API                   | `uv run uvicorn app.main:app --reload` |
| Run tests                     | `uv run pytest`                        |
| Format code                   | `uv run ruff format .`                 |
| Run lint checks               | `uv run ruff check .`                  |
| Fix lint issues automatically | `uv run ruff check . --fix`            |

Before opening a pull request, make sure formatting, linting and tests all pass.

---

## Environment variables

Create a `.env` file in the backend directory:

```env
APP_ENV=

SUPABASE_URL=
SUPABASE_PUBLISHABLE_KEY=
SUPABASE_SECRET_KEY=

OPENAI_API_KEY=
OPENAI_MODEL=
```

Never commit this file.

`SUPABASE_SECRET_KEY` and `OPENAI_API_KEY` are backend-only secrets. They must never be exposed to the frontend.

The frontend should only use:

- the Supabase URL
- the Supabase publishable key

---

## Frontend setup

From the frontend directory:

```bash
yarn install
yarn dev
```

`yarn dev` starts the local Rspack development server.

---

## Styling convention

To keep components readable, Tailwind classes live in a separate styles file next to the component instead of directly
inside the JSX.

For example:

```text
components/
  Input.tsx
  Input.styles.ts
```

```ts
// Input.styles.ts

export const inputStyles = {
    base: "w-full rounded-md border px-3 py-2 text-base",
    error: "border-red-500",
};
```

```tsx
// Input.tsx

import {inputStyles} from "./Input.styles";

export function Input({hasError, ...props}: InputProps) {
    return (
        <input
            className={`${inputStyles.base} ${hasError ? inputStyles.error : ""}`}
            {...props}
        />
    );
}
```

This keeps the component markup clean while still letting us use Tailwind normally.

---

# Git workflow

We use feature branches and pull requests. Changes should only reach `master` through a reviewed PR.

The basic workflow is:

1. update `master`
2. create a branch for your task
3. make your changes
4. commit them in small, focused commits
5. run the relevant checks
6. push your branch
7. open a pull request
8. respond to review feedback
9. merge once approved

A few important rules:

- Don't commit or push directly to `master`.
- Use one branch per task.
- Always branch from an up-to-date `master`.
- Run the relevant checks before pushing.
- Don't use `git push --force` unless the Tech Lead specifically asks you to.
- Never commit `.env` files, API keys or other secrets.
- If Git gets into a state you don't understand, stop and ask before trying random commands.

---

## 1. Start a new branch

First, make sure your local `master` is up to date:

```bash
git checkout master
git pull
```

Then create a branch for your task:

```bash
git checkout -b feat/preferences-form
```

Branch names should use one of these prefixes:

| Prefix      | Use for                                      | Example                     |
|-------------|----------------------------------------------|-----------------------------|
| `feat/`     | New feature                                  | `feat/conversation-list`    |
| `fix/`      | Bug fix                                      | `fix/login-error-message`   |
| `docs/`     | Documentation                                | `docs/update-readme`        |
| `test/`     | Tests only                                   | `test/preferences-endpoint` |
| `refactor/` | Code cleanup with no behaviour change        | `refactor/chat-service`     |
| `chore/`    | Tooling, configuration or dependency changes | `chore/update-ruff`         |

Keep the rest of the branch name short and descriptive.

---

## 2. Make focused commits

Before committing, check what has changed:

```bash
git status
git diff
```

Add only the files that belong to the change:

```bash
git add frontend/src/components/Input.tsx frontend/src/components/Input.styles.ts
```

Then commit:

```bash
git commit -m "feat(ui): add reusable Input component"
```

Try to keep commits small enough that someone reviewing them can quickly understand what changed.

Avoid using:

```bash
git add .
```

without checking `git status` first. This helps prevent accidentally committing `.env` files, generated files or
unrelated changes.

### Commit messages

Use a clear prefix that describes the type of change:

```text
feat(api): add endpoint to save communication preferences
fix(auth): reject expired access tokens
test(rls): check employee B cannot read employee A's conversations
docs: add frontend setup to DEVELOP.md
```

Common prefixes are:

`feat:`, `fix:`, `test:`, `docs:`, `refactor:` and `chore:`.

---

## 3. Check your work

For backend changes, run:

```bash
uv run ruff format .
uv run ruff check .
uv run pytest
```

For frontend changes, run:

```bash
yarn format
yarn lint
```

and check the affected screens in the browser.


---

## 4. Push your branch

The first time you push a new branch:

```bash
git push -u origin feat/preferences-form
```

After that:

```bash
git push
```

---

## 5. Open a pull request

Open a pull request from your branch into `master`.

The PR description should explain:

- **What** changed
- **Why** it changed, ideally with a link to the task or story
- **How to test it**
- **Screenshots**, if the UI changed

Try to keep PRs focused. If one PR starts touching a large number of unrelated files, it may be better to split the work
into separate tasks.

Changes involving the following areas should always be reviewed:

- authentication
- database tables
- Row Level Security policies
- secret handling
- AI prompts
- AI response schemas

---

## 6. Respond to review feedback

If the reviewer asks for changes, keep working on the same branch.

For example:

```bash
git add <changed files>
git commit -m "fix(ui): address review comments on Input"
git push
```

The existing pull request will update automatically.

There is no need to open another PR.

---

## 7. Merge and clean up

Once the PR is approved and all checks pass, the reviewer or Tech Lead can merge it.

After it has been merged:

```bash
git checkout master
git pull
git branch -d feat/preferences-form
```

Your local `master` is now ready for the next task.

---

## Keeping your branch up to date

If `master` changes while you're working, merge the latest changes into your branch:

```bash
git checkout master
git pull

git checkout feat/preferences-form
git merge master
```

After the merge, run the relevant checks again before pushing.

---

## Merge conflicts

If Git reports a merge conflict, start by checking which files are affected:

```bash
git status
```

Open each conflicted file and look for markers like:

```text
<<<<<<<
=======
>>>>>>>
```

Choose the correct version of the code, remove the markers, then add the resolved files:

```bash
git add <fixed files>
git commit
```

Run your checks again before pushing.

If you're unsure which version should be kept, ask before resolving it.

You can safely cancel an unfinished merge with:

```bash
git merge --abort
```

---

## Common situations

### I made changes on `master`, but I haven't committed yet

Create a branch immediately:

```bash
git checkout -b feat/my-change
```

Your uncommitted changes will move with you, so you can continue working normally.

### I committed directly to `master`, but I haven't pushed

You can still checkout a new branch and push there.

### I accidentally committed a `.env` file or secret

Let me know, even if the commit hasn't been pushed.

Any exposed credential should be treated as compromised and rotated.

### I don't know what state my repository is in

Start with:

```bash
git status
```
