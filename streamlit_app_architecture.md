# Streamlit Email Marketing Automation Platform - Architecture Design

## Overall Application Structure

The application will use `st.sidebar` for main navigation with each page containing sub-sections using `st.tabs` where appropriate.

## Mermaid Diagram - Application Flow

```mermaid
graph TD
    A[App Entry Point] --> B[Sidebar Navigation]
    
    B --> C[Dashboard]
    B --> D[Campaign Builder]
    B --> E[Contact Management]
    B --> F[Real-time Monitoring]
    B --> G[Analytics & Reports]
    B --> H[Settings / API Keys]
    
    %% Dashboard Components
    C --> C1[KPI Overview]
    C --> C2[Recent Activity]
    C --> C3[Quick Actions]
    C --> C4[Performance Charts]
    
    %% Campaign Builder Flow
    D --> D1[Campaign Type Selection]
    D1 --> D2[Email Template Design]
    D2 --> D3[Audience Selection]
    D3 --> D4[Trigger Configuration]
    D4 --> D5[Schedule & Review]
    D5 --> D6[Campaign Launch]
    
    %% Contact Management
    E --> E1[Contact List View]
    E --> E2[Import/Export]
    E --> E3[Segmentation]
    E --> E4[Contact Details]
    
    %% Real-time Monitoring
    F --> F1[Live Campaign Status]
    F --> F2[Email Delivery Logs]
    F --> F3[Error Alerts]
    F --> F4[Performance Metrics]
    
    %% Analytics & Reports
    G --> G1[Campaign Performance]
    G --> G2[Audience Insights]
    G --> G3[Revenue Reports]
    G --> G4[Custom Reports]
    
    %% Settings
    H --> H1[API Configuration]
    H --> H2[Email Provider Settings]
    H --> H3[User Preferences]
    H --> H4[System Configuration]
    
    %% Interaction Flows
    D6 --> F1
    F3 --> D4
    G1 --> D1
    E3 --> D3
    
    classDef primary fill:#e1f5fe
    classDef secondary fill:#f3e5f5
    classDef action fill:#e8f5e8
    
    class A,B primary
    class C,D,E,F,G,H secondary
    class D6,F3,G1 action
```

## Page-by-Page UI Layout Design

### 1. Dashboard (KPIs)
```
├── Sidebar Navigation
└── Main Content
    ├── Metrics Row (4 columns)
    │   ├── Total Campaigns
    │   ├── Active Subscribers
    │   ├── Open Rate (30 days)
    │   └── Revenue (30 days)
    ├── Charts Section (2 columns)
    │   ├── Campaign Performance Timeline
    │   └── Audience Growth Chart
    └── Recent Activity Feed
```

### 2. Campaign Builder
```
├── Sidebar Navigation
└── Main Content (Stepper/Wizard Layout)
    ├── Progress Indicator
    ├── Step Content Area
    │   └── Tabs: [Template | Audience | Triggers | Schedule]
    └── Action Buttons [Back | Next | Save Draft | Launch]
```

### 3. Contact Management
```
├── Sidebar Navigation
└── Main Content
    ├── Action Bar
    │   ├── Search/Filter
    │   ├── Import Button
    │   └── Export Button
    ├── Tabs: [All Contacts | Segments | Import History]
    └── Contact Table/Grid
        └── Contact Detail Modal (on click)
```

### 4. Real-time Monitoring & Logs
```
├── Sidebar Navigation
└── Main Content
    ├── Status Overview Cards
    ├── Tabs: [Live Campaigns | Delivery Logs | Error Alerts | Performance]
    └── Auto-refreshing Data Tables/Charts
```

### 5. Analytics & Reports
```
├── Sidebar Navigation
└── Main Content
    ├── Date Range Selector
    ├── Tabs: [Campaign Analytics | Audience Insights | Revenue | Custom]
    └── Interactive Charts and Tables
```

### 6. Settings / API Keys
```
├── Sidebar Navigation
└── Main Content
    └── Tabs: [API Keys | Email Providers | Preferences | System]
        ├── Configuration Forms
        ├── Test Connection Buttons
        └── Save/Reset Actions
```

## Navigation Flow Diagram

```mermaid
stateDiagram-v2
    [*] --> Dashboard
    Dashboard --> CampaignBuilder: Create Campaign
    Dashboard --> Monitoring: View Active
    Dashboard --> Analytics: View Reports
    
    CampaignBuilder --> ContactManagement: Select Audience
    CampaignBuilder --> Monitoring: Launch Campaign
    CampaignBuilder --> Dashboard: Save Draft
    
    ContactManagement --> CampaignBuilder: Create Campaign for Segment
    ContactManagement --> Analytics: View Segment Performance
    
    Monitoring --> CampaignBuilder: Edit Campaign
    Monitoring --> Analytics: View Detailed Reports
    
    Analytics --> CampaignBuilder: Create Similar Campaign
    Analytics --> ContactManagement: Analyze Segments
    
    Settings --> Dashboard: Apply Changes
    
    Dashboard --> Settings: Configure
    CampaignBuilder --> Settings: Setup APIs
    ContactManagement --> Settings: Import Settings
    Monitoring --> Settings: Alert Configuration
    Analytics --> Settings: Report Preferences
```

## Streamlit Implementation Strategy

### Main Application Structure
```python
# app.py
import streamlit as st

def main():
    st.set_page_config(
        page_title="Email Marketing Platform",
        page_icon="📧",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Sidebar Navigation
    with st.sidebar:
        st.title("📧 Email Marketing")
        page = st.selectbox(
            "Navigate to:",
            ["Dashboard", "Campaign Builder", "Contact Management", 
             "Real-time Monitoring", "Analytics & Reports", "Settings"]
        )
    
    # Route to appropriate page
    if page == "Dashboard":
        show_dashboard()
    elif page == "Campaign Builder":
        show_campaign_builder()
    # ... etc
```

### Key UI Components Strategy

1. **Responsive Layout**: Use `st.columns()` for responsive grids
2. **State Management**: Leverage `st.session_state` for multi-step workflows
3. **Real-time Updates**: Use `st.rerun()` with timers for monitoring page
4. **Data Tables**: Implement `st.dataframe()` with filters and search
5. **Forms**: Use `st.form()` for complex input workflows
6. **Charts**: Integrate Plotly for interactive visualizations
7. **Progress Indicators**: Custom progress bars for campaign builder

### Navigation State Management
```python
# Maintain navigation state and workflow progress
if 'current_campaign' not in st.session_state:
    st.session_state.current_campaign = None
if 'campaign_step' not in st.session_state:
    st.session_state.campaign_step = 1
```

## User Experience Flow

1. **Entry Point**: Dashboard with key metrics and quick actions
2. **Campaign Creation**: Guided workflow with clear steps and validation
3. **Contact Management**: Bulk operations with immediate feedback
4. **Monitoring**: Real-time updates with alert system
5. **Analytics**: Interactive exploration with drill-down capabilities
6. **Settings**: Organized configuration with test/validation features

This architecture provides a clear separation of concerns while maintaining intuitive user flows between related features.
