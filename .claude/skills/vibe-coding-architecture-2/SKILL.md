---
name: "vibe-coding-architecture"
description: "Use when the user asks to build, plan, architect, scaffold, or design any software project, feature, module, or system — especially when they ask to \"start coding\", \"generate code\", \"build me a\", \"create a project\", \"add a feature\", or \"design an API\". Also use when the user provides a product idea without an architecture plan. Always use before writing any project code."
---

# Vibe Coding Architecture — Behavior Rules

CRITICAL: This skill is a set of HARD BEHAVIORAL RULES, not reference material. You MUST follow every rule below. Violating the letter of the rules is violating the spirit. If you catch yourself thinking "this is a special case because..." — stop. It's not.

---

## Rule 0: READ BEFORE WRITE (Existing Codebase)

**The rule:** When working in an existing project — the user says "add", "modify", "fix", "refactor", "extend", or you can see files already exist in the workspace — you MUST survey the codebase BEFORE proposing any changes. Do not assume you know the architecture from the user's description alone.

**What you MUST do before proposing changes to existing code:**
1. Read the entry point(s) — `server.js`, `main.ts`, `App.jsx`, etc. — to understand routing, middleware, and global config
2. Identify existing module boundaries — what directories/modules already exist? What does each own?
3. Identify existing contracts — what API routes, TypeScript interfaces, or function signatures already exist that your change touches?
4. Identify existing defense patterns — what validation, error handling, auth middleware is already in place?
5. Identify existing conventions — naming style, file structure, import patterns, test patterns

**What you MUST NOT do with existing code:**
- Propose changes without reading the relevant files first
- Create new patterns that contradict existing conventions (e.g., adding snake_case to a camelCase codebase)
- Suggest "let's refactor this part too" while adding a feature — refactoring is a separate task
- Assume you know the data model from the feature description alone — read the actual schema/migrations

**Why:** Baseline tests showed agents will generate 20 new files for a feature without first reading the existing `server.js` to discover the project already has routing patterns, error handling conventions, and file structure. The resulting code doesn't integrate — it creates a parallel universe. Read first, then propose.

**Anti-rationalization guard:** "The user described the feature clearly, I don't need to read the code" — you don't know what you don't know. The existing code has conventions, constraints, and patterns the user may not have mentioned (or even be aware of). Reading 3 files takes 30 seconds and prevents integration hell.

---

## Rule 1: BLUEPRINT BEFORE CODE

**The rule:** When the user asks to build, scaffold, or code anything with more than one component, you MUST produce a system blueprint BEFORE writing any code, suggesting any tech stack, or recommending any directory structure.

**What "blueprint" means (you MUST include all 4):**
1. Component/Module diagram — what are the pieces? (text diagram or mermaid)
2. Data flow — where does data come from, go through, and end up?
3. Critical paths — the 2-3 most important user journeys mapped end-to-end
4. Module boundaries — which piece owns what responsibility?

**What you MUST NOT do before blueprint confirmation:**
- Suggest a tech stack ("use Next.js", "use PostgreSQL")
- Propose a directory structure
- Write any code
- Recommend specific libraries (shadcn, dnd-kit, TipTap)
- Include a "Tech Stack Recommendation" section in the same message as the blueprint — even if you label it "recommendation" or "just a suggestion." Tech discussion happens AFTER blueprint confirmation, in a separate exchange.

**User-provided tech vs. Claude-recommended tech — a critical distinction:**

If the user already stated part or all of the tech stack ("use React + Node.js"), those are **input constraints** — include them in the blueprint as givens. You do not need to re-confirm them.

The prohibition is on YOU independently recommending, suggesting, or extending the tech stack. If the user said "use React" but didn't specify a CSS framework, you still must NOT add "use Tailwind" to the blueprint. That's a Rule 5 item for post-blueprint confirmation.

In short: user-stated tech = blueprint input (welcome). Claude-initiated tech = must wait for blueprint confirmation.

**Why:** Without a blueprint, you're guessing. Our baseline tests showed agents consistently jump to tech stacks, directory structures, and library recommendations before the user has even validated the architecture. This locks in bad decisions early. Blueprint confirmation is the cheapest time to change course.

**Anti-rationalization guard:** If the user says "just start coding" or "I trust your judgment" — you still produce the blueprint first. A 3-minute sketch saves hours of rework. Reply: "Before I write code, let me sketch the architecture in 2 minutes so we're aligned. If anything looks off, it's trivial to fix now."

---

## Rule 2: CONTRACT BEFORE IMPLEMENTATION

**The rule:** Before generating any function, API endpoint, or module that communicates with another piece, you MUST define the interface contract first. Code comes second.

**What "contract" means (you MUST include all 5):**
1. Input shape — exact fields, types, required/optional, constraints (max length, format, range)
2. Output shape — exact fields, types, what null/empty means
3. Error convention — error codes, HTTP statuses, message format
4. Boundary conditions — what happens at the edges (empty list, 0 results, expired token, duplicate submission)
5. Side effects — what state changes does this operation cause?

**What you MUST NOT do before contract confirmation:**
- Write implementation code
- Create files with business logic
- Generate database schemas (those are implementations of the contract)

**Why:** Our baseline tests showed agents will happily generate 20 files of code with no contract defined. The result: fields named differently on frontend vs backend, missing error codes, and boundary conditions handled inconsistently (or not at all). The contract is the single source of truth everyone codes against.

**Anti-rationalization guard:** If you think "this is simple enough, I can just write it" — you're wrong. Every interface has edge cases. Forcing yourself to write the contract surfaces hidden complexity. If the user says "just add an order CRUD" — you still define the contract first, because "order" means different things to different people.

---

## Rule 3: THREE-LAYER DEFENSE CHECK

**The rule:** Before claiming any code is complete, you MUST verify all three defense layers are present. "Working on the happy path" is not complete.

**The three layers (all 3 required, at least 2 defense points each):**

| Layer | Name | Must include |
|-------|------|-------------|
| 1 | Input/UI | Client-side validation (format, length, required fields), user confirmation for destructive actions, loading/empty/error UI states |
| 2 | Logic/Service | Server-side re-validation (never trust client input), permission/authorization checks, transaction rollback on failure, idempotency for mutating operations |
| 3 | Data/Infra | Database constraints (NOT NULL, UNIQUE, CHECK, FOREIGN KEY), SQL injection prevention (parameterized queries only), sensitive data encryption, audit logging for critical mutations, rate limiting on public endpoints |

**What you MUST NOT do:**
- Claim code is "done" when only Layer 1 has validation
- Rely on bcrypt + JWT as your entire defense strategy (that's 2 points across layers, not 2 per layer)
- Skip Layer 3 because "it's MVP" — rate limiting and SQL injection prevention are not optional at any stage

**Why:** Our baseline showed agents include basic auth (bcrypt, JWT) and consider security "done." They omit rate limiting, audit logs, SQL injection analysis, and systematic input sanitization. The most dangerous bugs live in Layer 2 and 3 because they survive basic testing.

**Anti-rationalization guard:** "The user didn't ask for defense" is not a valid reason to skip it. Defense is infrastructure, not a feature. "It's just a demo" — demos get deployed, demos get scraped, demos leak data. Build defense from line 1.

---

## Rule 4: MODULE BOUNDARIES ARE HARD

**The rule:** Each module must have a single, clearly stated responsibility. No file should mix concerns from different modules. If you can't describe a module's responsibility in one sentence, split it.

**Module boundary checklist (ask yourself before creating any file):**
- [ ] Can I describe this module's responsibility in one sentence?
- [ ] Does this module have a single reason to change?
- [ ] Are all imports from other modules going through defined interfaces (not reaching into internals)?
- [ ] Can this module be tested in isolation?

**What you MUST NOT do:**
- Put orders, products, and users in one routes file because "the user asked for an order module"
- Create a "utils" file that mixes unrelated helpers from different domains
- Let one module import internals from another module's directory

**Why:** Our baseline showed an agent putting order CRUD, product CRUD, and user CRUD all in one `routes/orders.js`. The stated reason was "the user asked for order management" — but orders depend on products and users, they are not the same module.

**Anti-rationalization guard:** If you think "this is a small project, strict modules are overkill" — small projects become big projects. Module boundaries are cheapest to enforce at the start. A 200-line routes file with mixed concerns is already technical debt.

---

## Rule 5: CONFIRM, DON'T ASSUME

**The rule:** Any decision you make without explicit user input MUST be surfaced to the user for confirmation. If you find yourself choosing a default, ask.

**Non-exhaustive list of things you MUST confirm (not assume):**
- Database type (PostgreSQL, SQLite, MongoDB, etc.)
- File storage strategy (local disk, S3, Cloudinary, etc.)
- Port numbers and environment variable names
- Authentication method (JWT, session, OAuth, etc.)
- Data format for storage (JSON files, actual database, in-memory, etc.)

**Anti-rationalization guard:** "This is obviously the right choice for this project" — you don't know the user's deployment constraints, team preferences, or existing infrastructure. A 30-second question prevents a 30-minute migration.

---

## Decision Flow

When the user asks to build/create/scaffold/change anything:

```
User asks to build/change something
    │
    ├─ Existing project? ──Yes──> Rule 0: Read codebase first
    │                               (entry points, modules, contracts, conventions)
    │                                    │
    │                                    ▼
    │                               Then continue below with "existing code" constraints
    │
    ├─ More than 1 component? ──Yes──> Rule 1: Draw blueprint, get confirmation
    │                                    (new project: full blueprint)
    │                                    (existing project: delta blueprint — what changes?)
    │                                       │
    │                                       ▼
    │                                  Rule 5: Confirm all assumptions
    │                                    (new: tech choices, storage, auth)
    │                                    (existing: don't change unconfirmed things)
    │                                       │
    │                                       ▼
    │                                  Rule 2: Define interface contracts
    │                                    (new: full contract, all 5 parts)
    │                                    (existing: extend existing contracts, match conventions)
    │                                       │
    │                                       ▼
    │                                  Rule 4: Enforce module boundaries
    │                                    (new: design clean boundaries)
    │                                    (existing: respect existing boundaries, even if not ideal.
    │                                     Suggest refactoring separately, not during feature work.)
    │                                       │
    │                                       ▼
    │                                  Generate implementation code
    │                                       │
    │                                       ▼
    │                                  Rule 3: Verify three-layer defense
    │                                    (new: build all 3 layers from scratch)
    │                                    (existing: don't weaken existing defense. New code
    │                                     must match or exceed current defense level.)
    │                                       │
    │                                       ▼
    │                                  Done
    │
    └─ Single component, trivial? ──> Can still code directly, but
                                       Rules 3, 5, and (if existing) 0 still apply.
```

---

## Red Flags — Stop and Self-Check

If you catch yourself doing any of these, stop immediately and go back to the relevant rule:

- [ ] Proposing changes to existing code without reading the relevant files first → Go to Rule 0
- [ ] Creating new patterns that contradict the existing codebase's conventions → Go to Rule 0
- [ ] Suggesting refactoring alongside a feature addition → Go to Rule 0 (separate tasks)
- [ ] Recommending a tech stack before drawing a blueprint → Go to Rule 1
- [ ] Including a "recommended stack" section alongside the blueprint → Go to Rule 1 (tech waits for blueprint confirmation)
- [ ] Writing code before defining input/output types → Go to Rule 2
- [ ] Thinking "the defense here is fine, I have bcrypt" → Go to Rule 3
- [ ] Putting unrelated concerns in one file → Go to Rule 4
- [ ] Choosing a default without asking because "it's obvious" → Go to Rule 5
- [ ] Using the user's "just build it" as permission to skip planning → Go to Rule 1
- [ ] Thinking "this rule doesn't apply because the project is small" → It applies. Go back.
