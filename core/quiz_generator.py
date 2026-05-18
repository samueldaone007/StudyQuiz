"""
Smart Quiz Generation Module
Generates meaningful quiz questions from study materials using NLP techniques.
"""
import re
import json
import random
from typing import List, Dict, Tuple, Optional
from collections import Counter


class SmartQuizGenerator:
    """Generates intelligent quiz questions from text content."""
    
    # Question templates for different types
    QUESTION_TEMPLATES = {
        'definition': [
            "What is {concept}?",
            "Define '{concept}'.",
            "Explain what '{concept}' means based on the material.",
        ],
        'purpose': [
            "What is the purpose of {concept}?",
            "Why is '{concept}' important?",
            "What role does '{concept}' play?",
        ],
        'identification': [
            "Which of the following describes {concept}?",
            "Identify the correct statement about '{concept}'.",
            "Select the best answer about '{concept}'.",
        ],
        'application': [
            "How is {concept} used?",
            "In what context would you use '{concept}'?",
        ],
        'list': [
            "Which of the following is {concept}?",
            "Select {concept} from the options below.",
        ]
    }
    
    # Words to ignore as concepts
    IGNORE_WORDS = {
        'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was',
        'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new',
        'now', 'old', 'see', 'two', 'who', 'did', 'she', 'use', 'way', 'many', 'oil', 'sit',
        'set', 'run', 'eat', 'far', 'sea', 'eye', 'ago', 'off', 'too', 'any', 'say', 'man',
        'try', 'ask', 'end', 'why', 'let', 'put', 'own', 'tell', 'very', 'when', 'much',
        'would', 'there', 'their', 'what', 'said', 'each', 'which', 'will', 'about', 'could',
        'other', 'after', 'first', 'never', 'these', 'think', 'where', 'being', 'every',
        'great', 'might', 'shall', 'still', 'those', 'while', 'this', 'that', 'with', 'have',
        'from', 'they', 'been', 'were', 'said', 'time', 'than', 'them', 'into', 'just',
        'like', 'over', 'also', 'back', 'only', 'know', 'take', 'year', 'good', 'some',
        'come', 'make', 'well', 'look', 'down', 'most', 'long', 'last', 'find', 'give',
        'does', 'made', 'part', 'such', 'keep', 'call', 'came', 'need', 'feel', 'seem',
        'turn', 'hand', 'high', 'sure', 'upon', 'head', 'help', 'home', 'side', 'move',
        'both', 'five', 'once', 'same', 'must', 'name', 'left', 'done', 'open', 'case',
        'show', 'live', 'play', 'went', 'told', 'seen', 'hear', 'talk', 'soon', 'read',
        'stop', 'face', 'fact', 'land', 'line', 'kind', 'next', 'word',
        # Section headers and category labels
        'skills', 'tools', 'technologies', 'projects', 'education', 'experience',
        'relevant', 'coursework', 'languages', 'programming', 'other', 'soft',
        'personal', 'professional', 'technical', 'summary', 'objective', 'profile',
        'contact', 'references', 'interests', 'hobbies', 'achievements', 'awards',
        'certifications', 'publications', 'conferences', 'workshops', 'trainings',
        # Common action words that shouldn't be concepts
        'developed', 'used', 'worked', 'tasked', 'daily', 'basis', 'along', 'student',
        'school', 'outcome', 'accuracy', 'expected', 'graduation', 'following', 'based',
        'select', 'correct', 'best', 'describes', 'options', 'answer', 'context',
        'would', 'material', 'study', 'content', 'information', 'document', 'achieved',
        'completed', 'implemented', 'created', 'designed', 'managed', 'led', 'conducted',
        'performed', 'assisted', 'helped', 'supported', 'responsible', 'involved'
    }
    
    def __init__(self, text: str):
        self.text = text
        self.sentences = self._split_sentences(text)
        self.lines = [l.strip() for l in text.split('\n') if l.strip()]
        
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Handle abbreviations
        text = re.sub(r'(?<!\w)(Mr|Mrs|Dr|Prof|Inc|Ltd|Jr|Sr|vs|Vol|vol|pp|et al)\.', r'\1<DOT>', text)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.replace('<DOT>', '.').strip() for s in sentences if len(s.strip()) > 15]
        return sentences
    
    def _is_likely_header(self, text: str) -> bool:
        """Check if text is likely a section header or category label."""
        text_upper = text.upper()
        text_clean = text_upper.replace('&', ' ').replace('AND', ' ')
        words = text_clean.split()
        
        headers = {'SKILLS', 'PROJECTS', 'EDUCATION', 'EXPERIENCE', 'SUMMARY', 'OBJECTIVE',
                   'PROFILE', 'CONTACT', 'REFERENCES', 'ACHIEVEMENTS', 'CERTIFICATIONS',
                   'PUBLICATIONS', 'LANGUAGES', 'TOOLS', 'TECHNOLOGIES', 'COURSEWORK',
                   'PROGRAMMING', 'OTHER', 'SOFT', 'PERSONAL', 'PROFESSIONAL', 'TECHNICAL',
                   'AI', 'ML', 'RELEVANT'}
        
        # Check if any word in text is a header
        for word in words:
            if word in headers or word.rstrip(':') in headers or word.rstrip('S') in headers:
                return True
        
        # Check exact match
        if text_upper in headers or text_upper.rstrip(':') in headers:
            return True
            
        return False
    
    def _extract_key_concepts(self, num_concepts: int = 20) -> List[Tuple[str, str, float]]:
        """
        Extract key concepts with their context and importance scores.
        Returns list of (concept, context_sentence, score) tuples.
        """
        concepts = []
        
        # Pattern 1: Extract from "Category: Value" patterns (highest priority)
        category_pattern = r'^([A-Za-z\s&]+):\s*(.+)$'
        for line in self.lines:
            match = re.match(category_pattern, line)
            if match:
                category = match.group(1).strip()
                value = match.group(2).strip()
                
                # Skip if category is a header
                if self._is_likely_header(category):
                    # Extract items from value (comma-separated)
                    items = [i.strip() for i in re.split(r',|;', value)]
                    for item in items:
                        # Clean up the item
                        item = re.sub(r'^(?:and|or)\s+', '', item, flags=re.IGNORECASE).strip()
                        if len(item) > 2 and not self._should_ignore(item):
                            # Extract just the key term
                            key_term = self._extract_key_term(item)
                            if key_term and not self._should_ignore(key_term):
                                context = f"{category}: {item}"
                                concepts.append((key_term, context, 2.5))
        
        # Pattern 2: Extract from list items (bullet points, dashes)
        list_pattern = r'^[\s]*[•\-\*]\s*(.+)$'
        for line in self.lines:
            match = re.match(list_pattern, line, re.MULTILINE)
            if match:
                item = match.group(1).strip()
                # Skip if it looks like a header
                if self._is_likely_header(item):
                    continue
                # Extract key terms from list item
                key_term = self._extract_key_term(item)
                if key_term and not self._should_ignore(key_term):
                    concepts.append((key_term, item, 2.0))
        
        # Pattern 3: Extract technical terms with context
        tech_patterns = [
            # Library/Tool with description
            r'\b(Pandas|NumPy|Scikit-learn|TensorFlow|Matplotlib|Streamlit|RandomForestClassifier)\b',
            # Programming languages
            r'\b(Python|Java|JavaScript|C\+\+|C#|Ruby|Go|Rust|Swift|Kotlin)\b',
            # Tools
            r'\b(Git|GitHub|VS Code|Jupyter|Colab|Docker|Kubernetes)\b',
        ]
        
        for pattern in tech_patterns:
            for sentence in self.sentences:
                matches = re.findall(pattern, sentence, re.IGNORECASE)
                for match in matches:
                    if not self._should_ignore(match):
                        # Find the best context for this term
                        concepts.append((match, sentence, 2.0))
        
        # Pattern 4: Extract capitalized phrases that are likely proper nouns
        np_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\b'
        for sentence in self.sentences:
            matches = re.findall(np_pattern, sentence)
            for match in matches:
                if len(match) > 3 and not self._should_ignore(match):
                    # Check if it's in a meaningful context
                    if any(indicator in sentence.lower() for indicator in 
                           ['used', 'developed', 'created', 'implemented', 'built', 'designed', 'project']):
                        concepts.append((match, sentence, 1.5))
        
        # Remove duplicates and keep highest score
        seen = {}
        for concept, context, score in concepts:
            key = concept.lower()
            if key not in seen or seen[key][2] < score:
                seen[key] = (concept, context, score)
        
        # Sort by score and return top concepts
        unique_concepts = list(seen.values())
        unique_concepts.sort(key=lambda x: x[2], reverse=True)
        
        return unique_concepts[:num_concepts]
    
    def _extract_key_term(self, text: str) -> Optional[str]:
        """Extract the key term from a list item or phrase."""
        # Remove common prefixes
        text = re.sub(r'^(?:used|developed|created|implemented|built|worked with|tools?|technologies?)\s+', '', text, flags=re.IGNORECASE)
        
        # Extract first meaningful phrase
        words = text.split()
        if not words:
            return None
        
        # Take up to 3 words that form a meaningful term
        term_words = []
        for word in words[:4]:
            clean_word = re.sub(r'[^\w\-]', '', word)
            if clean_word and len(clean_word) > 1:
                term_words.append(clean_word)
        
        if term_words:
            return ' '.join(term_words)
        return None
    
    def _should_ignore(self, phrase: str) -> bool:
        """Check if phrase should be ignored."""
        phrase_lower = phrase.lower()
        
        # Check ignore list
        if phrase_lower in self.IGNORE_WORDS:
            return True
        
        # Check if it's just numbers or symbols
        if re.match(r'^[\d\W]+$', phrase):
            return True
        
        # Check if too short
        if len(phrase) < 3:
            return True
        
        # Check if it's just a single common word
        words = phrase_lower.split()
        if len(words) == 1 and words[0] in self.IGNORE_WORDS:
            return True
        
        return False
    
    def _get_related_concepts(self, concept: str, all_concepts: List[str], num: int = 3) -> List[str]:
        """Get related concepts for distractors."""
        concept_lower = concept.lower()
        
        # Categorize concepts
        categories = {
            'programming': ['python', 'java', 'javascript', 'c++', 'programming', 'code', 'language'],
            'ml_ai': ['machine learning', 'ai', 'tensorflow', 'scikit', 'neural', 'model', 'algorithm', 'prediction', 'classifier'],
            'data': ['pandas', 'numpy', 'data', 'analysis', 'statistics', 'probability'],
            'tools': ['git', 'github', 'vscode', 'jupyter', 'colab', 'notebook', 'tool'],
            'viz': ['matplotlib', 'plot', 'visualization', 'chart', 'graph'],
            'web': ['streamlit', 'web', 'app', 'application', 'interface'],
            'soft_skills': ['communication', 'teamwork', 'problem solving', 'time management', 'adaptability']
        }
        
        # Find which category the concept belongs to
        concept_category = None
        for cat, keywords in categories.items():
            if any(kw in concept_lower for kw in keywords):
                concept_category = cat
                break
        
        # Get distractors from same category
        distractors = []
        if concept_category:
            for c in all_concepts:
                c_lower = c.lower()
                if c_lower != concept_lower:
                    for kw in categories[concept_category]:
                        if kw in c_lower:
                            distractors.append(c)
                            break
        
        # If not enough, add other concepts
        if len(distractors) < num:
            for c in all_concepts:
                if c.lower() != concept_lower and c not in distractors:
                    distractors.append(c)
                if len(distractors) >= num:
                    break
        
        return distractors[:num]
    
    def _get_concept_category(self, concept: str) -> str:
        """Get the category of a concept."""
        concept_lower = concept.lower()
        
        if any(lang in concept_lower for lang in ['python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'go', 'php']):
            return 'programming_language'
        elif any(tool in concept_lower for tool in ['git', 'github', 'vscode', 'jupyter', 'colab', 'notebook']):
            return 'tool'
        elif any(lib in concept_lower for lib in ['pandas', 'numpy', 'matplotlib', 'streamlit', 'scikit', 'tensorflow']):
            return 'library'
        elif any(ml in concept_lower for ml in ['machine learning', 'ai', 'algorithm', 'model', 'classifier', 'neural']):
            return 'ml_ai'
        elif any(data in concept_lower for data in ['data', 'database', 'sql']):
            return 'data'
        else:
            return 'other'
    
    def _generate_question_text(self, concept: str, context: str, question_type: str = 'MCQ') -> str:
        """Generate appropriate question text based on concept and context."""
        concept_lower = concept.lower()
        context_lower = context.lower()
        category = self._get_concept_category(concept)
        
        # Programming language question
        if category == 'programming_language':
            templates = [
                f"Which of the following is a programming language mentioned in the material?",
                f"Select a programming language from the options:",
                f"Which programming language is listed in the skills section?"
            ]
            return random.choice(templates)
        
        # Tool/Technology question
        elif category == 'tool':
            templates = [
                f"Which tool/technology is mentioned in the material?",
                f"Select a development tool from the options:",
                f"Which of the following tools is listed?"
            ]
            return random.choice(templates)
        
        # Library/Framework question
        elif category == 'library':
            templates = [
                f"Which library/framework is mentioned in the material?",
                f"Select a Python library from the options:",
                f"Which of the following is a library used?"
            ]
            return random.choice(templates)
        
        # ML/AI question
        elif category == 'ml_ai':
            templates = [
                f"Which machine learning/AI concept is mentioned?",
                f"Select an AI/ML term from the options:",
                f"Which of the following relates to machine learning?"
            ]
            return random.choice(templates)
        
        # Project question
        elif 'project' in context_lower:
            templates = [
                f"What was involved in the {concept} project?",
                f"In the {concept} project, what was used/achieved?",
                f"Which technology was used in the {concept} project?"
            ]
            return random.choice(templates)
        
        # Default question
        else:
            templates = [
                f"Which of the following is mentioned in the material?",
                f"Select the correct answer about '{concept}':",
                f"What is '{concept}' in the context of the material?"
            ]
            return random.choice(templates)
    
    def _generate_distractor_options(self, concept: str, all_concepts: List[str]) -> List[str]:
        """Generate meaningful distractor options from the same category."""
        concept_category = self._get_concept_category(concept)
        concept_lower = concept.lower()
        
        # Get concepts from the same category (excluding the correct answer)
        same_category = []
        for c in all_concepts:
            if c.lower() != concept_lower and self._get_concept_category(c) == concept_category:
                same_category.append(c)
        
        # If we have enough from the same category, use them
        if len(same_category) >= 3:
            return same_category[:3]
        
        # Otherwise, add concepts from other categories
        distractors = same_category[:]
        for c in all_concepts:
            if c.lower() != concept_lower and c not in distractors:
                distractors.append(c)
            if len(distractors) >= 3:
                break
        
        # If still not enough, add generic options based on category
        while len(distractors) < 3:
            if concept_category == 'programming_language':
                generic = ['C#', 'Ruby', 'PHP', 'Swift', 'Go', 'Rust']
            elif concept_category == 'tool':
                generic = ['Docker', 'Kubernetes', 'AWS', 'Azure', 'Postman', 'Slack']
            elif concept_category == 'library':
                generic = ['Keras', 'PyTorch', 'Seaborn', 'Plotly', 'Flask', 'Django']
            elif concept_category == 'ml_ai':
                generic = ['Deep Learning', 'NLP', 'Computer Vision', 'Reinforcement Learning']
            else:
                generic = ['HTML', 'CSS', 'SQL', 'NoSQL', 'API', 'Cloud']
            
            for g in generic:
                if g.lower() != concept_lower and g not in distractors:
                    distractors.append(g)
                if len(distractors) >= 3:
                    break
        
        return distractors[:3]
    
    def generate_mcq_question(self, concept: str, context: str, all_concepts: List[str]) -> Dict:
        """Generate a multiple choice question."""
        question_text = self._generate_question_text(concept, context, 'MCQ')
        
        # Generate options
        correct_answer = concept
        distractors = self._generate_distractor_options(concept, all_concepts)
        
        # Create options list
        options = [correct_answer] + distractors[:3]
        random.shuffle(options)
        
        # Create explanation
        explanation = f"'{concept}' is mentioned in the material: {context[:200]}..."
        
        return {
            'question_text': question_text,
            'question_type': 'MCQ',
            'options': json.dumps(options),
            'correct_answer': correct_answer,
            'explanation': explanation
        }
    
    def generate_tf_question(self, concept: str, context: str, all_concepts: List[str]) -> Dict:
        """Generate a true/false question with meaningful statements."""
        is_true = random.choice([True, False])
        category = self._get_concept_category(concept)
        concept_lower = concept.lower()
        
        # Create category-based statements
        if category == 'programming_language':
            true_templates = [
                f"{concept} is listed as a programming language in the skills section.",
                f"The material mentions {concept} as one of the programming languages.",
                f"{concept} is included in the list of programming languages."
            ]
            false_templates = [
                f"{concept} is a database management system mentioned in the material.",
                f"The material lists {concept} as a development tool, not a programming language.",
                f"{concept} is an operating system mentioned in the skills section."
            ]
        elif category == 'tool':
            true_templates = [
                f"{concept} is mentioned as a tool/technology in the material.",
                f"The skills section includes {concept} as a development tool.",
                f"{concept} is listed under Tools & Technologies."
            ]
            false_templates = [
                f"{concept} is a programming language mentioned in the material.",
                f"The material lists {concept} as a Python library.",
                f"{concept} is described as a machine learning algorithm."
            ]
        elif category == 'library':
            true_templates = [
                f"{concept} is mentioned as a library in the material.",
                f"The skills section includes {concept} as a Python library.",
                f"{concept} is listed under AI/ML tools."
            ]
            false_templates = [
                f"{concept} is a programming language mentioned in the material.",
                f"The material lists {concept} as a development tool.",
                f"{concept} is described as an operating system."
            ]
        elif category == 'ml_ai':
            true_templates = [
                f"{concept} is mentioned in the AI/ML section of the material.",
                f"The material includes {concept} as a machine learning concept.",
                f"{concept} is listed under AI/ML skills."
            ]
            false_templates = [
                f"{concept} is a programming language mentioned in the material.",
                f"The material describes {concept} as a web development framework.",
                f"{concept} is listed as a database system."
            ]
        else:
            true_templates = [
                f"{concept} is mentioned in the material.",
                f"The skills section includes {concept}.",
                f"{concept} appears in the list of skills."
            ]
            false_templates = [
                f"{concept} is not mentioned anywhere in the material.",
                f"The material explicitly excludes {concept} from the skills list.",
                f"{concept} is described as unrelated to the content."
            ]
        
        if is_true:
            question_text = f"True or False: {random.choice(true_templates)}"
            correct_answer = 'True'
            explanation = f"This is True. {random.choice(true_templates)}"
        else:
            question_text = f"True or False: {random.choice(false_templates)}"
            correct_answer = 'False'
            explanation = f"This is False. {concept} is actually mentioned as {category.replace('_', ' ')}."
        
        return {
            'question_text': question_text,
            'question_type': 'TF',
            'options': json.dumps(['True', 'False']),
            'correct_answer': correct_answer,
            'explanation': explanation
        }
    
    def generate_short_answer_question(self, concept: str, context: str) -> Dict:
        """Generate a short answer question."""
        category = self._get_concept_category(concept)
        
        # Category-specific question templates
        if category == 'programming_language':
            templates = [
                f"Name one programming language mentioned in the skills section.",
                f"List a programming language that the person is skilled in.",
                f"What programming language is mentioned in the material?"
            ]
        elif category == 'tool':
            templates = [
                f"Name one development tool mentioned in the material.",
                f"What tool or technology is listed in the skills section?",
                f"List a tool that the person uses."
            ]
        elif category == 'library':
            templates = [
                f"Name one Python library mentioned in the AI/ML section.",
                f"What library is used for data science/machine learning?",
                f"List a library/framework mentioned in the material."
            ]
        elif category == 'ml_ai':
            templates = [
                f"What machine learning or AI concept is mentioned?",
                f"Name one AI/ML technology or concept from the material.",
                f"What AI/ML skill is listed?"
            ]
        else:
            templates = [
                f"What is '{concept}' in the context of the material?",
                f"Describe '{concept}' based on the skills listed.",
                f"Explain what '{concept}' refers to in the document."
            ]
        
        question_text = random.choice(templates)
        
        # Better explanation
        if category == 'other':
            explanation = f"A correct answer should identify '{concept}' which is mentioned in: {context[:200]}"
        else:
            explanation = f"A correct answer should mention '{concept}' which is a {category.replace('_', ' ')} listed in the material."
        
        return {
            'question_text': question_text,
            'question_type': 'SHORT',
            'options': json.dumps([]),
            'correct_answer': concept,
            'explanation': explanation
        }
    
    def generate_questions(self, num_questions: int = 5, question_types: List[str] = None) -> List[Dict]:
        """Generate a set of quiz questions."""
        if question_types is None:
            question_types = ['MCQ']
        
        # Extract key concepts with context
        concepts_with_context = self._extract_key_concepts(num_concepts=num_questions + 5)
        all_concept_names = [c[0] for c in concepts_with_context]
        
        questions = []
        used_concepts = set()
        
        for concept, context, score in concepts_with_context:
            if len(questions) >= num_questions:
                break
            
            if concept.lower() in used_concepts:
                continue
            
            used_concepts.add(concept.lower())
            
            # Choose question type
            q_type = random.choice(question_types)
            
            try:
                if q_type == 'MCQ':
                    question = self.generate_mcq_question(concept, context, all_concept_names)
                elif q_type == 'TF':
                    question = self.generate_tf_question(concept, context, all_concept_names)
                else:
                    question = self.generate_short_answer_question(concept, context)
                
                question['order'] = len(questions) + 1
                questions.append(question)
            except Exception as e:
                print(f"Error generating question for '{concept}': {e}")
                continue
        
        return questions


def generate_smart_quiz_questions(text: str, num_questions: int = 5, question_types: List[str] = None) -> List[Dict]:
    """
    Generate smart quiz questions from text.
    
    Args:
        text: The source text
        num_questions: Number of questions to generate
        question_types: Types of questions (MCQ, TF, SHORT)
    
    Returns:
        List of question dictionaries
    """
    generator = SmartQuizGenerator(text)
    return generator.generate_questions(num_questions, question_types)
