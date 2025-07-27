import streamlit as st
from datetime import datetime, timedelta, time
from services import get_email_service
from services.campaign_service import get_campaign_service
from jinja2 import Template as JinjaTemplate
import pandas as pd
import json


def load_contact_segments():
    """Load available contact segments"""
    email_service = get_email_service()
    try:
        return email_service.get_contact_segments()
    except:
        return []


def render_template_preview(template, context):
    """Render template with Jinja2 and context data"""
    try:
        if template and template.get('body_template'):
            jinja_template = JinjaTemplate(template['body_template'])
            rendered = jinja_template.render(context)
            return rendered
        return "No template selected"
    except Exception as e:
        return f"Template render error: {str(e)}"


def save_draft(campaign_data):
    """Save campaign draft to session state and potentially to database"""
    if 'drafts' not in st.session_state:
        st.session_state['drafts'] = {}
    
    draft_id = f"draft_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    st.session_state['drafts'][draft_id] = {
        **campaign_data,
        'created_at': datetime.now().isoformat(),
        'status': 'draft'
    }
    return draft_id


def show_campaign_builder():
    st.title("📧 Build a New Campaign")
    
    # Initialize session state for drafts
    if 'campaign_draft' not in st.session_state:
        st.session_state['campaign_draft'] = {}
    
    email_service = get_email_service()
    
    # Campaign Builder Form
    with st.form("campaign_builder_form", clear_on_submit=False):
        st.subheader("Campaign Configuration")
        
        # Campaign Basic Info
        col1, col2 = st.columns(2)
        with col1:
            campaign_name = st.text_input(
                "Campaign Name", 
                value=st.session_state['campaign_draft'].get('name', ''),
                placeholder="Enter campaign name"
            )
        
        with col2:
            tenant_type = st.selectbox(
                "Campaign Type",
                options=["academic", "corporate"],
                index=0 if st.session_state['campaign_draft'].get('tenant_id') == 'academic' else 1
            )
        
        campaign_description = st.text_area(
            "Description (Optional)",
            value=st.session_state['campaign_draft'].get('description', ''),
            height=100
        )
        
        st.divider()
        
        # Contact Lists Section
        st.subheader("📋 Select or Upload Contact Lists")
        
        contact_source = st.radio(
            "Contact Source",
            options=["Upload CSV File", "Select from Existing Contacts", "Use Contact Segments"],
            horizontal=True
        )
        
        contacts_data = []
        
        if contact_source == "Upload CSV File":
            uploaded_file = st.file_uploader(
                "Upload CSV with contact information", 
                type="csv",
                help="CSV should contain columns: email, first_name, last_name, organization, etc."
            )
            
            if uploaded_file is not None:
                try:
                    contacts_df = pd.read_csv(uploaded_file)
                    st.write(f"Loaded {len(contacts_df)} contacts:")
                    st.dataframe(contacts_df.head())
                    contacts_data = contacts_df.to_dict('records')
                except Exception as e:
                    st.error(f"Error reading CSV: {str(e)}")
        
        elif contact_source == "Select from Existing Contacts":
            # Mock existing contacts - in real implementation, fetch from database
            existing_contacts = [
                "professor1@university.edu",
                "professor2@university.edu", 
                "hr@company.com",
                "recruiter@tech-company.com"
            ]
            selected_contacts = st.multiselect(
                "Choose contacts:", 
                existing_contacts,
                default=st.session_state['campaign_draft'].get('selected_contacts', [])
            )
            contacts_data = [{'email': email} for email in selected_contacts]
        
        elif contact_source == "Use Contact Segments":
            segments = load_contact_segments()
            if segments:
                selected_segments = st.multiselect(
                    "Choose contact segments:",
                    options=[seg['name'] for seg in segments],
                    default=st.session_state['campaign_draft'].get('selected_segments', [])
                )
                # In real implementation, would fetch contacts from selected segments
                contacts_data = [{'segment': seg} for seg in selected_segments]
            else:
                st.info("No contact segments available")
        
        st.write(f"Selected contacts: {len(contacts_data)}")
        
        st.divider()
        
        # Template Selection and Live Preview
        st.subheader("📝 Choose / Edit Templates with Live Preview")
        
        # Fetch templates
        templates = email_service.get_templates()
        
        if templates:
            template_options = [f"{t['name']} ({t.get('category', 'general')})" for t in templates]
            selected_template_idx = st.selectbox(
                "Select a template:",
                range(len(template_options)),
                format_func=lambda x: template_options[x],
                index=st.session_state['campaign_draft'].get('template_idx', 0)
            )
            
            selected_template = templates[selected_template_idx]
            
            # Template customization
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.write("**Template Editor**")
                
                # Subject line editing
                custom_subject = st.text_input(
                    "Subject Line",
                    value=selected_template.get('subject_template', ''),
                    help="Use {{variable_name}} for personalization"
                )
                
                # Body editing
                custom_body = st.text_area(
                    "Email Body",
                    value=selected_template.get('body_template', ''),
                    height=300,
                    help="Use Jinja2 syntax for dynamic content: {{first_name}}, {{organization}}, etc."
                )
                
                # Template variables
                if selected_template.get('variables'):
                    st.write("**Available Variables:**")
                    for var in selected_template['variables']:
                        st.code(f"{{{{{var}}}}}")
            
            with col2:
                st.write("**Live Preview**")
                
                # Sample context for preview
                sample_context = {
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'organization': 'Sample University',
                    'position': 'Professor',
                    'research_area': 'Machine Learning'
                }
                
                # Render preview
                preview_template = {
                    'subject_template': custom_subject,
                    'body_template': custom_body
                }
                
                rendered_subject = render_template_preview(
                    {'body_template': custom_subject}, sample_context
                )
                rendered_body = render_template_preview(preview_template, sample_context)
                
                st.write("**Subject:**")
                st.info(rendered_subject)
                
                st.write("**Body:**")
                st.markdown(rendered_body, unsafe_allow_html=True)
        
        else:
            st.warning("No templates available. Please create templates first.")
            selected_template = None
            custom_subject = ""
            custom_body = ""
        
        st.divider()
        
        # Schedule Options
        st.subheader("⏰ Schedule Send or Send Immediately")
        
        schedule_option = st.radio(
            "When to send:",
            options=["Send Immediately", "Schedule for Later"], 
            horizontal=True,
            index=0 if st.session_state['campaign_draft'].get('send_immediately', True) else 1
        )
        
        if schedule_option == "Schedule for Later":
            col1, col2 = st.columns(2)
            with col1:
                send_date = st.date_input(
                    "Send Date",
                    min_value=datetime.now().date(),
                    value=st.session_state['campaign_draft'].get('send_date', datetime.now().date())
                )
            with col2:
                send_time_input = st.time_input(
                    "Send Time",
                    value=st.session_state['campaign_draft'].get('send_time', time(9, 0))
                )
            
            send_datetime = datetime.combine(send_date, send_time_input)
            send_immediately = False
        else:
            send_datetime = datetime.now()
            send_immediately = True
        
        # Campaign Settings
        st.subheader("⚙️ Campaign Settings")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            daily_limit = st.number_input(
                "Daily Send Limit",
                min_value=1, max_value=1000, 
                value=st.session_state['campaign_draft'].get('daily_limit', 50)
            )
        
        with col2:
            time_between_emails = st.number_input(
                "Seconds Between Emails",
                min_value=1, max_value=3600,
                value=st.session_state['campaign_draft'].get('time_between', 300)
            )
        
        with col3:
            enable_followups = st.checkbox(
                "Enable Follow-ups",
                value=st.session_state['campaign_draft'].get('enable_followups', True)
            )
        
        if enable_followups:
            col1, col2 = st.columns(2)
            with col1:
                followup_delay = st.number_input(
                    "Follow-up Delay (days)",
                    min_value=1, max_value=30,
                    value=st.session_state['campaign_draft'].get('followup_delay', 7)
                )
            with col2:
                max_followups = st.number_input(
                    "Max Follow-ups",
                    min_value=0, max_value=5,
                    value=st.session_state['campaign_draft'].get('max_followups', 2)
                )
        else:
            followup_delay = 7
            max_followups = 0
        
        st.divider()
        
        # Form submission buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            save_draft_btn = st.form_submit_button(
                "💾 Save Draft", 
                help="Save campaign as draft for later"
            )
        
        with col2:
            create_campaign_btn = st.form_submit_button(
                "🚀 Create Campaign",
                type="primary",
                help="Create and optionally schedule the campaign"
            )
        
        with col3:
            clear_form_btn = st.form_submit_button(
                "🗑️ Clear Form",
                help="Reset all form fields"
            )
    
    # Handle form submissions outside the form
    if save_draft_btn:
        draft_data = {
            'name': campaign_name,
            'description': campaign_description,
            'tenant_id': tenant_type,
            'contacts_data': contacts_data,
            'template_id': selected_template['id'] if selected_template else None,
            'custom_subject': custom_subject,
            'custom_body': custom_body,
            'send_immediately': send_immediately,
            'send_datetime': send_datetime.isoformat() if not send_immediately else None,
            'daily_limit': daily_limit,
            'time_between': time_between_emails,
            'enable_followups': enable_followups,
            'followup_delay': followup_delay,
            'max_followups': max_followups
        }
        
        # Save to session state
        st.session_state['campaign_draft'] = draft_data
        
        # Save draft with timestamp
        draft_id = save_draft(draft_data)
        st.success(f"📝 Draft saved successfully! Draft ID: {draft_id}")
    
    elif create_campaign_btn:
        # Validation
        if not campaign_name:
            st.error("❌ Campaign name is required")
        elif not contacts_data:
            st.error("❌ Please select or upload contacts")
        elif not selected_template:
            st.error("❌ Please select a template")
        else:
            try:
                # Prepare campaign data for backend
                campaign_data = {
                    'name': campaign_name,
                    'description': campaign_description,
                    'tenant_id': tenant_type,
                    'template_id': selected_template['id'],
                    'target_criteria': {'contact_count': len(contacts_data)},
                    'contact_filters': {'source': contact_source},
                    'send_schedule': None if send_immediately else send_datetime.isoformat(),
                    'daily_send_limit': daily_limit,
                    'time_between_emails': time_between_emails,
                    'enable_followups': enable_followups,
                    'followup_delay_days': followup_delay,
                    'max_followups': max_followups
                }
                
                # Integration with backend CampaignService.create()
                campaign_service = get_campaign_service()
                result = campaign_service.create(campaign_data)
                
                if result:
                    st.success(f"🎉 Campaign '{campaign_name}' created successfully!")
                    st.balloons()
                    
                    # Clear draft after successful creation
                    st.session_state['campaign_draft'] = {}
                    
                    # Show campaign details
                    st.json(result)
                else:
                    st.error("❌ Failed to create campaign. Please try again.")
                    
            except Exception as e:
                st.error(f"❌ Error creating campaign: {str(e)}")
    
    elif clear_form_btn:
        st.session_state['campaign_draft'] = {}
        st.rerun()
    
    # Show existing drafts
    if 'drafts' in st.session_state and st.session_state['drafts']:
        st.subheader("📁 Saved Drafts")
        
        draft_names = list(st.session_state['drafts'].keys())
        selected_draft = st.selectbox("Load draft:", ["None"] + draft_names)
        
        if selected_draft != "None":
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📂 Load Draft"):
                    st.session_state['campaign_draft'] = st.session_state['drafts'][selected_draft]
                    st.success(f"Draft '{selected_draft}' loaded!")
                    st.rerun()
            
            with col2:
                if st.button("🗑️ Delete Draft"):
                    del st.session_state['drafts'][selected_draft]
                    st.success(f"Draft '{selected_draft}' deleted!")
                    st.rerun()

# Required for Streamlit page context management
if __name__ == '__main__':
    show_campaign_builder()
