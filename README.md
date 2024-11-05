# Sniff AI

Sniff AI is an AI-powered fragrance creation platform that translates poetic and descriptive text into custom fragrance compositions. This project combines generative AI with a curated fragrance database to inspire and generate scent profiles, showcasing both Product Management and AI/ML engineering capabilities.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Project Phases & Progress](#project-phases--progress)
- [Installation](#installation)
- [Usage](#usage)
- [Future Enhancements](#future-enhancements)

---

## Project Overview

Sniff AI generates custom fragrance compositions based on user-provided descriptions, ranging from simple phrases to poetic imagery. The platform leverages a dataset of existing fragrances for model training and reference, creating unique blends that align with user input.

---

## Key Features

- **Text-to-Fragrance Generation**: Transform descriptive language into a unique fragrance profile.
- **Fragrance Database**: Access to a searchable database of existing fragrances with detailed fragrance notes, scent families, and additional information.
- **Customizable Interface**: User-friendly UI for inputting descriptions, selecting preferred notes, and viewing generated fragrance compositions.
- **Feedback System**: A mechanism for users to rate generated fragrances, aiding in model refinement.

---

## Tech Stack

- **Backend**: Python, Flask or Django
- **Frontend**: React or Vue.js
- **Database**: PostgreSQL with Elasticsearch for fast search
- **Modeling**: Generative AI (e.g., GPT or custom transformer models) and NLP

---

## Project Phases & Progress

### Phase 1: Research and Data Collection
- [ ] **Gather fragrance data** from online databases and public sources
- [ ] **Curate dataset** of fragrance notes, descriptions, and scent families
- [ ] **Compile paired data** of poetic descriptions and fragrance compositions for initial training

### Phase 2: Initial Model Development
- [ ] **Fine-tune language model** (GPT, BERT, or similar) on paired text-fragrance data
- [ ] **Train fragrance composition model** to create blends from semantic interpretations of descriptions
- [ ] **Evaluate model outputs** to ensure relevance and accuracy using similarity scores

### Phase 3: Building the Database
- [ ] **Set up relational database** (PostgreSQL) for storing fragrance data
- [ ] **Integrate Elasticsearch** for efficient fragrance search
- [ ] **Populate database** with curated fragrance data

### Phase 4: User Interface and Experience
- [ ] **Design user interface** mockups for text input and fragrance output display
- [ ] **Implement frontend** in React or Vue.js
- [ ] **Integrate model with UI** for real-time or asynchronous fragrance generation

### Phase 5: Model Refinement
- [ ] **Establish user feedback loops** allowing users to rate or tweak generated fragrances
- [ ] **Integrate feedback mechanism** to refine model outputs based on user interactions
- [ ] **Iterate on model improvements** based on feedback and testing

---

## Installation

*Instructions for setting up the project locally will go here.*

---

## Usage

*Instructions for using Sniff AI will go here, including how to input descriptions, select fragrance notes, and view outputs.*

---

## Future Enhancements

- [ ] **Additional Input Customization**: Allow users to select fragrance intensity, season, or occasion.
- [ ] **Improved Fragrance Matching**: Refine similarity scoring for more precise fragrance outputs.
- [ ] **User Accounts and Saved Fragrances**: Enable users to save generated compositions to their profiles.
- [ ] **Mobile Version**: Develop a responsive mobile version of the platform.

---

Feel free to contribute, suggest features, or reach out with feedback. This project is in progress, and any input is appreciated!

---

