# NeuroLens MVP

## Product

NeuroLens is a personalised, policy-aware workplace chatbot
designed primarily for neurodivergent employees.

DuoSoft LTD is a hypothetical organisation used as the
enterprise setting for the MSc project.

## Core jobs

### 1. Understand

NeuroLens helps employees:

- interpret ambiguous workplace communication
- identify missing or unclear information
- rewrite messages more clearly
- draft editable replies

NeuroLens must not claim to know another person's true intention
or emotional state.

### 2. Know

NeuroLens answers questions using approved fictional DuoSoft policies.

The MVP will include approximately 3-5 policies, such as:

- Annual Leave Policy
- Remote Work Policy
- Communication Guidelines
- Data Handling Policy
- Employee Support Policy

Policy answers must:

- be grounded in retrieved policy text
- show the relevant source
- distinguish policy facts from generated explanation
- abstain when no supporting policy exists

### 3. Act

NeuroLens helps employees turn workplace information into action.

The MVP supports:

- task extraction
- deadline extraction
- task breakdown
- next-smallest-step suggestions
- draft leave requests
- optional confirmed calendar actions

Actions are never executed solely because the AI suggested them.

## Personalisation

Employees choose their own communication preferences.

Initial preferences:

- directness
- response length
- highlight ambiguity
- step-by-step guidance
- always show next step

No diagnosis or disability disclosure is required.

## AI architecture

NeuroLens uses a hybrid NLP architecture.

### Pretrained sentiment Transformer

Classifies wording as:

- Positive
- Neutral
- Negative

This is a core NLP component of the project.

The sentiment model classifies text.
It does not determine a person's emotional state.

### OpenAI API

Used for:

- interpretation
- clarification
- rewriting
- suggested replies
- task extraction
- structured conversational responses

### Policy retrieval

Used for:

- retrieving approved fictional DuoSoft policy text
- grounding policy answers
- returning source references

## Data

Employee-owned data is stored in Supabase:

- employee profile
- communication preferences
- conversations
- messages
- analyses
- tasks
- leave requests
- confirmed actions

## Privacy boundaries

NeuroLens is not an employee surveillance system.

The MVP does not include:

- manager access to employee conversations
- employee sentiment dashboards
- productivity scoring
- passive monitoring
- automatic ingestion of workplace chats
- diagnosis
- employee-to-employee messaging

The prototype is GDPR-informed but does not claim legal GDPR compliance.

