# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**My Juridic Assistant** is a French real estate legal assistant designed for real estate professionals (agents, rental management, syndic). It provides reliable, structured legal responses based on an internal legal corpus with anti-hallucination safeguards. The system uses RAG (Retrieval-Augmented Generation) to answer questions strictly from a curated knowledge base.

### Core Principles
- **Answer only from corpus**: Never hallucinate. If information isn't in the corpus, explicitly state "information absente du corpus"
- **Always cite sources**: Include article references and legal text citations
- **Mandatory pre-qualification**: Before answering, trigger automatic legal pre-questioning to gather missing context
- **Clear refusal for out-of-scope**: Refuse questions outside the defined legal perimeter
- **Fixed disclaimer**: All responses must include a disclaimer stating this is not personalized legal advice

### The Decisive Feature: Automatic Legal Pre-Questioning

**This is not a chatty chatbot. This is an intelligent legal qualification tree.**

Before providing any legal response, the assistant MUST engage in a mini-diagnostic if necessary. This systematic pre-questioning ensures:
- Fewer "off-topic" answers
- Enhanced credibility
- Immediate "lawyer-like" impression

**Critical qualification questions by domain:**

**Copropriété:**
- Le bien est-il en copropriété ?
- S'agit-il d'une copropriété horizontale ou verticale ?
- Quelle est la date du règlement de copropriété ?

**Transaction:**
- Le mandat est-il écrit et signé ?
- La question concerne-t-elle un acte déjà signé ?
- L'interlocuteur est-il un professionnel soumis à la loi Hoguet ?
- S'agit-il d'une vente entre particuliers ou avec professionnel ?

**Location:**
- S'agit-il d'une location vide ou meublée ?
- Le logement est-il affecté à la résidence principale ?
- Quelle est la date de signature du bail ?
- Quelle est la classe énergétique (DPE) du logement ?

**Professions immobilières:**
- L'interlocuteur est-il titulaire d'une carte professionnelle ?
- La structure dispose-t-elle d'une garantie financière ?
- S'agit-il de transaction ou de gestion locative ?

**Implementation principle**: If critical information is missing, the assistant MUST ask the qualification question BEFORE attempting to answer. This prevents guesswork and ensures legally sound responses.

## Legal Perimeter (V1)

The assistant covers four main domains of French real estate law:

1. **Copropriété** (Co-ownership)
   - Loi 1965 + Décret 1967 + liaison rules

2. **Professions immobilières** (Real estate professionals)
   - Loi Hoguet 1970 + Décret 1972 + liaison rules

3. **Transaction** (Property transactions)
   - Code civil (vente, vices cachés, responsabilité)
   - Agent responsibility

4. **Location** (Rental)
   - Loi 1989 + Décret charges 1987 + Décret décence 2002 + CCH (DPE/performance énergétique)

## 4-Layer Architecture: The Differentiating Framework

This assistant is built on a unique 4-layer architecture that delivers "institutional-grade" legal reasoning with adaptive intelligence.

### Layer 1: Legal Corpus (`Corpus/01_sources_text/`)
**What**: Authoritative source texts (laws, decrees, codes, selected case law)
**Where**: `01_sources_text/` organized by domain:
- `copropriete/` - Loi 1965, Décret 1967
- `location/` - Loi 1989, décrets 1987/2002, CCH, Code civil
- `pro_immo/` - Loi Hoguet 1970, Décret 1972
- `transaction/` - Code civil (vente, responsabilité), CCH, Code conso

**Format**: 300-1200 word chunks with stable metadata
**Purpose**: Authoritative legal references for RAG retrieval

### Layer 2: Legal Reasoning Sheets (`Corpus/02_fiches_ia_ready/`)
**What**: AI-optimized summaries containing legal reasoning logic for each major theme
**Where**: `02_fiches_ia_ready/[domain]/`
**Each fiche includes:**
- **Conditions d'application**: When and how the text applies
- **Exceptions**: Specific exclusions and special cases
- **Erreurs fréquentes des agents**: Common mistakes made by real estate professionals
- **Jurisprudence clé**: Key case law (targeted selection)
- **Objet du texte**: What the text regulates
- **Quand le texte s'applique**: Application scope
- **Questions terrain couvertes**: Practical questions covered
- **Points de vigilance**: Critical watchpoints
- **Articles "à citer souvent"**: Most frequently cited articles

**Format**: `Fiche_IA_READY_[TextName]_[Date].md`
**Purpose**: Provide reasoning context and prevent common errors

### Layer 3: Intelligent Pre-Prompt Framework (`Corpus/03_regles_liaison/` + system prompt)
**What**: Mandatory reasoning framework imposed on the LLM
**Components:**

**A. Liaison Rules** (`03_regles_liaison/`)
Binding rules that specify how texts must be interpreted together:
- `location/regles_liaison_location.md` - Cross-text dependencies for rental law
- `copropriete/regles_liaison_copro.md` - Co-ownership text interactions
- `pro_immo/Regles_Liaison_LoiHoguet_Decret1972.md` - Professional regulation hierarchy
- `transaction/regles_liaison_transaction.md` - Transaction law precedence

**CRITICAL**: No legal text can be interpreted in isolation when liaison rules exist.

**B. Imposed Reasoning Rules** (system prompt):
- **Qualification obligatoire**: Mandatory pre-questioning before answering
- **Hiérarchie des normes**: Respect legal hierarchy (loi > décret > code)
- **Prudence juridique par défaut**: Default to caution, refuse edge cases
- **Refus des cas contentieux personnalisés**: Decline personalized litigation advice

**Purpose**: Enforce legal rigor and prevent institutional AI solution rigidity

### Layer 4: Adaptive Questioning (`Corpus/03_regles_liaison/` + prompt logic)
**What**: Context-aware qualification system
**How it works:**
- If critical information is missing → assistant asks qualification question BEFORE answering
- Questions are domain-specific and legally relevant
- No generic chatbot behavior: targeted diagnostic only
- Examples: "Le bien est-il en copropriété ?", "S'agit-il d'une location vide ou meublée ?"

**Purpose**: Gather missing context intelligently, ensuring legally sound responses

**This is exactly what "institutional" solutions cannot do due to rigidity. This adaptive layer is the competitive advantage.**

## Metadata Schema

All corpus chunks must include:
- `source`: Legal text name
- `type`: loi/décret/code/fiche/jurisprudence/règle_liaison
- `domaine`: copro/location/transaction/pro_immo
- `sous-thème`: Specific subtopic
- `articles`: List of article references
- `version_date`: Consolidation date (if applicable)
- `texte`: The actual content

## Key Quality Rules: Legal Reasoning Workflow

### Processing Workflow (Mandatory Order)
1. **Identify domain** (copropriété/location/transaction/pro_immo)
2. **Check liaison rules** for that domain (Layer 3)
3. **Trigger pre-qualification** if critical context is missing (Layer 4)
4. **Retrieve relevant chunks** from corpus (Layer 1) + fiches (Layer 2)
5. **Apply reasoning framework** from fiches (conditions, exceptions, erreurs fréquentes)
6. **Cross-reference texts** as required by liaison rules
7. **Cite sources precisely** (article numbers, text references)
8. **Include disclaimer** (not personalized legal advice)

### Pre-Qualification Triggers (Layer 4)
Before answering, verify you have these critical qualifiers:

**For all domains:**
- Is the questioner a licensed real estate professional?
- Is this about a specific ongoing case or general information?

**Copropriété:**
- Property status (copropriété or individual ownership)?
- Type of copropriété (horizontal/vertical)?
- Date of règlement de copropriété?

**Location:**
- Bail type (vide/meublé)?
- Usage (résidence principale/secondaire)?
- Bail signature date?
- DPE class (for décence énergétique questions)?

**Transaction:**
- Written and signed mandate?
- Act already signed or in negotiation?
- Professional or private transaction?

**Professions immobilières:**
- Carte professionnelle status?
- Garantie financière in place?
- Activity type (transaction/gestion locative)?

**If ANY critical qualifier is missing → ASK before answering. Do not guess.**

### Anti-Hallucination Constraints
- **Only answer from retrieved corpus chunks** (Layers 1 & 2)
- If corpus lacks information → explicitly state **"information absente du corpus"**
- Never extrapolate beyond explicit text
- Request qualification via Layer 4 rather than guessing
- Refuse questions outside the four domains
- Refuse personalized litigation advice (contentieux)

### Example Scenarios
- **Charges récupérables**: Must reference both Loi 1989 (Article 23) AND Décret 1987 list
- **Décence logement**: Must check both Décret 2002 criteria AND CCH DPE obligations
- **Congé bailleur**: Loi 1989 Article 15 + verify legal motifs + check délais

## Target Users
- Real estate agents (transaction, mandates, fees)
- Rental property managers (leases, charges, deposits, terminations, décence, DPE)
- Syndic/co-ownership managers (AG, PV, disputes, charges, work)
- Network managers (quick validation, risk reduction)

## Technical Architecture (Planned)

**Frontend**: Web app (Softr/Glide) with login + optional Telegram bot
**Backend**: Private /ask API with:
- Auth + whitelist
- Domain/sub-theme routing
- Vector retrieval (top-k with metadata filters)
- Claude API with constraining prompt
- Response with citations + logs

**Vector Index**: Supabase (pgvector) or equivalent
**Pipeline**: Claude Code for extraction, chunking, metadata, indexation

## Non-Goals
- Personalized legal advice (prohibited)
- Drafting binding legal documents
- Exhaustive coverage of all real estate law
- Comprehensive case law (V1: targeted jurisprudence only)

## Success Metrics (V1)
- Precision on test set: 95%+
- Responses with relevant references: 90%+
- Hallucination rate: ~0%
- P95 latency: <10s (web), <12s (Telegram)
- Cost per query: optimized (low top-k, compact extracts)
