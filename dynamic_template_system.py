"""
DYNAMIC TEMPLATE PERSONALIZATION SYSTEM v1.0
=============================================
Intelligent email template adaptation based on research domains
"""

class DynamicTemplateSystem:
    """Dynamic email template personalization based on research analysis"""
    
    def __init__(self):
        self.domain_templates = {
            'machine_learning': {
                'subject_prefix': 'Research Collaboration Inquiry - ML & Data Science',
                'opening_style': 'technical'
            },
            'computer_vision': {
                'subject_prefix': 'Research Collaboration Inquiry - Computer Vision & AI',
                'opening_style': 'applied'
            }
        }
    
    def generate_personalized_template(self, research_analysis, professor_data, base_template):
        """Generate dynamically personalized email template"""
        
        professor_name = professor_data.get('name', 'Professor')
        primary_domain = research_analysis.get('primary_domain', 'machine_learning')
        
        # Select domain template or default
        domain_template = self.domain_templates.get(primary_domain, self.domain_templates.get('machine_learning'))
        
        # Generate personalized subject
        subject = domain_template.get('subject_prefix', 'Research Collaboration Inquiry') + ' - Data Science Engineering Student'
        
        # Create personalized template
        personalized_template = f"""Subject: {subject}

Dear Prof. {{name}},

I hope this email finds you in excellent health and high spirits. My name is Anamay Tripathy, and I am a dedicated Data Science Engineering student from MIT Manipal, India, with a profound passion for computational research and technological innovation.

Research Alignment and Academic Interest:
I am writing to explore potential research collaboration opportunities in your area of expertise. {{research_mention}}

The research environment at {{university_context}} represents exactly the kind of academic setting where I can contribute meaningfully while advancing my knowledge. Your research approach strongly resonates with my academic vision and career aspirations.

Technical Background and Expertise:
Programming Proficiency: Advanced skills in Python, R, SQL, and JavaScript with extensive experience in data manipulation, statistical analysis, and machine learning implementation

Machine Learning Frameworks: Hands-on experience with TensorFlow, PyTorch, scikit-learn, pandas, NumPy, and advanced ensemble methods

Research Methodologies: Strong foundation in experimental design, statistical hypothesis testing, computational modeling, and data visualization

Professional Experience:
Technical Head - YaanBarpe (Government of Karnataka Incubated):
Leading 12 developers creating sustainable tech solutions addressing environmental challenges. We've developed ML-powered waste management systems achieving 34% efficiency improvement.

Data Analyst Intern - Intellect Design Arena, Mumbai:
Developed automated dashboards processing 2.3M+ daily financial transactions. Implemented Python/Kafka pipelines reducing processing time by 67%, improving reliability to 99.8%.

Research Collaboration Objectives:
I am particularly excited about the opportunity to contribute to research projects involving:
- Advanced computational research and algorithm development
- Statistical analysis and modeling for research initiatives
- Development and optimization of algorithms for practical applications
- Interdisciplinary research that combines data science methodologies with domain-specific knowledge

Collaboration Vision:
I would be deeply honored to join your research team as a graduate research assistant, summer intern, or visiting researcher. My specific interests include:
- Contributing to ongoing research projects in your area of expertise
- Developing advanced technical skills under your expert mentorship
- Participating in academic publications and conference presentations
- Learning cutting-edge research methodologies and best practices
- Applying my technical expertise to advance your laboratory's research objectives

I have attached my comprehensive curriculum vitae, which provides detailed information about my academic achievements, technical projects, research experience, and relevant coursework. I believe my combination of strong technical skills, academic dedication, and genuine passion for research would make me a valuable addition to your research team.

Next Steps and Availability:
I would be extremely grateful for the opportunity to discuss potential research opportunities in your laboratory. I am available for a virtual meeting at your convenience to explore how my background, skills, and research interests align with your current and future research directions.

Thank you very much for considering my application and for the invaluable contributions you make to advancing computational research. I look forward to the possibility of learning from your expertise and contributing meaningfully to cutting-edge research under your distinguished guidance.

Best regards,

Anamay Tripathy
B.Tech Data Science Engineering
MIT Manipal, India
Technical Head, YaanBarpe
Email: tripathy.anamay23@gmail.com
Phone: +91-9877454747
Portfolio: anamay.vercel.app

P.S. I am particularly fascinated by the intersection of {{research_focus}} and real-world applications, and I believe your research group would provide an exceptional environment for academic growth and meaningful research contributions. I am fully committed to dedicating my time, energy, and technical skills to advancing research objectives and contributing to the scientific community.
"""
        
        return personalized_template


def get_dynamic_template_system():
    """Get dynamic template system instance"""
    return DynamicTemplateSystem()