import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats
import warnings
warnings.filterwarnings('ignore')


# Page Configuration
st.set_page_config(
    page_title="Health Care Analysis",
    page_icon="😴",
    layout="wide",
    initial_sidebar_state="expanded"
)
# place this near the top of your app (after st.set_page_config)

with st.sidebar:
    st.image("healthcare.png", caption=None, use_container_width=False)
    st.markdown("---")           # optional line separator
    st.subheader("Navigation & Filters")

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
    }
    h1 {
        color: #1f77b4;
        text-align: center;
    }
    h2 {
        color: #2c3e50;
    }
    </style>
""", unsafe_allow_html=True)

# Load Data Function
@st.cache_data
def load_data():
    """Load and preprocess the sleep health data"""

 #Load data

    Cities = pd.read_csv('cities.csv')
    Departments = pd.read_csv('departments.csv')
    Diagnoses = pd.read_csv('diagnoses.csv')
    Insurance = pd.read_csv('insurance.csv')
    Patients = pd.read_csv('patients.csv')
    Procedures = pd.read_csv('procedures.csv')
    Providers = pd.read_csv('providers.csv')
    Visits = pd.read_csv('visits.csv')

    # Make Calculations

    Visits[['Discharge Date','Admitted Date']] = Visits[['Discharge Date','Admitted Date']].apply(pd.to_datetime) #if conversion required
    Visits['Addmition Days'] = (Visits['Discharge Date'] - Visits['Admitted Date']).dt.days
    Visits['Addmition Days'] = Visits['Addmition Days'].fillna(0)
    Visits['Insurance Coverage'] = Visits['Insurance Coverage'].fillna(0)
    Visits['Room Cost']  = (Visits['Addmition Days'] * Visits['Room Charges(daily rate)'])
    Visits['Total Billing'] = (Visits['Medication Cost'] + Visits['Treatment Cost'])
    Visits['Net Billing'] = (Visits['Medication Cost'] + Visits['Treatment Cost'] + Visits['Room Cost'] - Visits['Insurance Coverage'])

    # Age Category

    def categorize_age(dfx):
        conditions = [
            (dfx['Age'] >= 18) & (dfx['Age'] < 30),
            (dfx['Age'] >= 30) & (dfx['Age'] < 40),
            (dfx['Age'] >= 40) & (dfx['Age'] < 50),
            (dfx['Age'] >= 50)
        ]
        results = ['From 18 - 30', 'From 30 - 40', 'From 40 - 50', '50 and Over']
        dfx['Age Category'] = np.select(conditions, results, default='Unknown')
        return dfx

    Patients = categorize_age(Patients.copy())

    #Merge tables

    df1 = pd.merge(Visits,Patients,on='Patient ID')
    df2 = pd.merge(df1,Providers,on='Provider ID')
    df3 = pd.merge(df2,Departments,on='Department ID')
    df4 = pd.merge(df3,Diagnoses,on='Diagnosis ID')
    df5 = pd.merge(df4,Procedures,on='Procedure ID')
    df6 = pd.merge(df5,Insurance,on='Insurance ID')
    df7 = pd.merge(df6,Cities,on='City ID')

    #Cleaning

    df = df7.drop(['Provider ID', 'Department ID', 'Diagnosis ID', 'Procedure ID', 'Insurance ID', 'City ID'], axis=1)
    df['Follow-Up Visit Date'] = df['Follow-Up Visit Date'].fillna('No F/U')
    df['Discharge Date'] = df['Discharge Date'].fillna('No Addmition')
    df['Admitted Date'] = df['Admitted Date'].fillna('No Addmition')
    df['Room Type'] = df['Room Type'].fillna('No Admittion')
 
     # add separate date fields

    df['Date of Visit'] = pd.to_datetime(df['Date of Visit'])
    df['Month Name'] = df['Date of Visit'].dt.month_name()
    df['Day Name'] = df['Date of Visit'].dt.day_name()
    df['Day of Month'] = df['Date of Visit'].dt.day
    df['Week of Month'] = df['Date of Visit'].dt.isocalendar().week.astype(int)
    df['Quarter of Year'] = df['Date of Visit'].dt.quarter
    
    # Clean column names
    df.columns = df.columns.str.strip()
    
   
    return df

# Load the data
df = load_data()

# Sidebar - Navigation and Filters
st.sidebar.title("🎯 Navigation & Filters")
page = st.sidebar.radio(
    "Select Analysis Page:",
    ["🏠 Overview", "📊 Financial Analysis", "🔍 Provider Analysis", "📋 Data Explorer"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("🔧 Filters")

# Filters
age_range = st.sidebar.slider(
    "Age Range:",
    int(df['Age_x'].min()),
    int(df['Age_x'].max()),
    (int(df['Age_x'].min()), int(df['Age_x'].max()))
)

gender_filter = st.sidebar.multiselect(
    "Gender:",
    options=df['Gender_x'].unique(),
    default=df['Gender_x'].unique()
)

city_filter = st.sidebar.multiselect(
    "City:",
    options=sorted(df['City'].unique()),
    default=sorted(df['City'].unique())
)

diagnosis_filter = st.sidebar.multiselect(
    "Diagnosis:",
    options=df['Diagnosis'].unique(),
    default=df['Diagnosis'].unique()
)

provider_filter = st.sidebar.multiselect(
    "Provider:",
    options=df['Provider Name'].unique(),
    default=df['Provider Name'].unique()
)

department_filter = st.sidebar.multiselect(
    "Department:",
    options=df['Department'].unique(),
    default=df['Department'].unique()
)

service_filter = st.sidebar.multiselect(
    "Service Type:",
    options=df['Service Type'].unique(),
    default=df['Service Type'].unique()
)


# Apply filters
filtered_df = df[
    (df['Age_x'] >= age_range[0]) & 
    (df['Age_x'] <= age_range[1]) &
    (df['Gender_x'].isin(gender_filter)) &
    (df['City'].isin(city_filter)) &
    (df['Diagnosis'].isin(diagnosis_filter)) &
    (df['Provider Name'].isin(provider_filter)) &
    (df['Department'].isin(department_filter)) &
    (df['Service Type'].isin(service_filter)) 
]

st.sidebar.markdown("---")
st.sidebar.info(f"**Filtered Records:** {len(filtered_df)} / {len(df)}")

# Download filtered data
@st.cache_data
def convert_df_to_csv(dataframe):
    return dataframe.to_csv(index=False).encode('utf-8')

csv = convert_df_to_csv(filtered_df)
st.sidebar.download_button(
    label="📥 Download Filtered Data",
    data=csv,
    file_name='filtered_Health_Care_data.csv',
    mime='text/csv',
)

# Main Content Area
if page == "🏠 Overview":
    st.title("😴  Health Care Analysis Dashboard")
    st.markdown("### Comprehensive Analysis of Patterns and Health Metrics")
   #for card color 
    st.markdown("""
<style>
/* KPI card */
[data-testid="stMetric"] {
  background: rgba(050,050,050,0.06);   /* optional: subtle card bg on dark theme */
  border: 1px solid rgba(200,200,200,0.12);
  border-radius: 12px;
  padding: 14px 16px;
}

/* label (small text above) */
[data-testid="stMetricLabel"] > div {
  color: #000000 !important;
  opacity: 0.85;                         /* keep a bit dimmer than value */
}

/* main value */
[data-testid="stMetricValue"] {
  color: #000000 !important;
  opacity: 0.85;
  font-size: 1.4rem;  /* Smaller than 1.6rem */
  font-weight: 700;    
}

/* delta text + badge */
[data-testid="stMetricDelta"] {
  color: #000000 !important;             /* make delta text white */
}
[data-testid="stMetricDelta"] svg {      /* make the arrow white too */
  filter: brightness(0) invert(1);
}

/* optional: make all plotly charts stretch instead of using use_container_width */
.user-select-none svg { max-width: 100%; }
</style>
""", unsafe_allow_html=True)

    # Key Metrics Row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        no_patients_filtered = filtered_df['Patient ID'].nunique()
        no_patients = df['Patient ID'].nunique()
        st.metric(
            label="👥 No of Patients",
            value=f"{no_patients_filtered:,}",
            delta=f"{no_patients_filtered - no_patients:}" if no_patients_filtered != no_patients else None
        )
    
    with col2:
        total_billing_filtered = sum(filtered_df['Total Billing'])
        total_billing = sum(df['Total Billing'])
        st.metric(
            label="😴 Total Billing",
            value=f"{total_billing_filtered:,} £",
            delta=f"{total_billing_filtered - total_billing:} £" if total_billing_filtered != total_billing else None
        )
    
    with col3:
        insurance_coverage_filtered = sum(filtered_df['Insurance Coverage'])
        insurance_coverage = sum(df['Insurance Coverage'])
        st.metric(
            label="😴 Insurance Coverage",
            value=f"{insurance_coverage_filtered:,} £",
            delta=f"{insurance_coverage_filtered - insurance_coverage:} £" if insurance_coverage_filtered != insurance_coverage else None
        )
    
    with col4:
        room_revenue_filtered = sum(filtered_df['Room Cost'])
        room_revenue = sum(df['Room Cost'])
        st.metric(
            label="😴 Room Revenue",
            value=f"{room_revenue_filtered:,} £",
            delta=f"{room_revenue_filtered - room_revenue:} £" if room_revenue_filtered != room_revenue else None
        )
    
    with col5:
        net_billing_filtered = sum(filtered_df['Net Billing'])
        net_billing = sum(df['Net Billing'])
        st.metric(
            label="😴  Net Billing",
            value=f"{net_billing_filtered:,} £",
            delta=f"{net_billing_filtered - net_billing:} £" if net_billing_filtered != net_billing else None
        )
    
    st.markdown("---")
    
    # Overview Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Insurance Provider Distribution")
        insurance_counts = filtered_df['Insurance Provider'].value_counts()
        fig = px.pie(
            values=insurance_counts.values,
            names=insurance_counts.index,
            title="Insurance Provider Percentage",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Age Distribution")
        fig = px.histogram(
            filtered_df,
            x='Age_x',
            nbins=6,
            title="Patients Age Distribution",
           color_discrete_sequence=["#651fb4"]
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Gender Distribution by Procedure")
        Procedures = filtered_df.groupby(['Procedure', 'Gender_x']).size().reset_index(name='Count')
        fig = px.bar(
            Procedures,
            x='Procedure',
            y='Count',
            color='Gender_x',
            title="Procedure by Gender",
            barmode='group',
            color_discrete_map={'Male': '#3498db', 'Female': '#e74c3c'}
        )
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Referral Source Distribution")
        Referral = filtered_df['Referral Source'].value_counts()
        fig = px.bar(
            x=Referral.index,
            y=Referral.values,
            title="Referral Source Distribution",
            color=Referral.values,
            color_continuous_scale='Blues'
        )
        fig.update_layout(showlegend=False, xaxis_title="Referral Source", yaxis_title="Count")
        st.plotly_chart(fig, use_container_width=True)

elif page == "📊 Financial Analysis":
    st.title("📊 Financial Data Analysis")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Revenue", "Profitability", "Time Analysis", "Geographical"])
    
    with tab1:
        st.subheader("Revenue Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Total Billing by City
            total_billing_by_city = filtered_df.groupby('City')['Total Billing'].sum().sort_values(ascending=True)
            fig = px.bar(
                x=total_billing_by_city.values,
                y=total_billing_by_city.index,
                orientation='h',
                title="Total Billing by City",
                labels={'x': 'Bounds', 'y': 'City'},
                color=total_billing_by_city.values,
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Total Billing by Age Group
            filtered_df['Age_Group'] = pd.cut(filtered_df['Age_x'], bins=[0, 20, 30, 40, 50, 80], labels=['<20', '20-30','30-40', '40-50', '50+'])
            billing_by_age = filtered_df.groupby('Age_Group')['Total Billing'].sum()
            fig = px.line(
                x=billing_by_age.index.astype(str),
                y=billing_by_age.values,
                title="Total Billing by Age Group",
                markers=True,
                labels={'x': 'Age Group', 'y': 'Total Billing'}
            )
            st.plotly_chart(fig, use_container_width=True)

        full_width_col = st.columns(1)[0]
        with full_width_col:

            # Convert 'Date of Visit' to datetime
            filtered_df['Date of Visit'] = pd.to_datetime(filtered_df['Date of Visit'])

            # Group by date and sum Net Billing
            daily_net_billing = filtered_df.groupby('Date of Visit')['Net Billing'].sum().reset_index()

            # Plotting with Streamlit
            st.title("📈 Net Billing Timeline")

            fig, ax = plt.subplots(figsize=(15, 7))
            sns.lineplot(x='Date of Visit', y='Net Billing', data=daily_net_billing, ax=ax)
            ax.set_title('Net Billing Timeline')
            ax.set_xlabel('Date of Visit')
            ax.set_ylabel('Sum of Net Billing')
            ax.grid(True, linestyle='--', alpha=0.7)
            plt.tight_layout()

            # Display the plot in Streamlit
            st.pyplot(fig, use_container_width=True)


    with tab2:
        st.subheader("Profitability Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Department Profit")
            department_profit = filtered_df.groupby('Department')['Medication Cost'].sum().sort_values(ascending=True)
            fig = px.bar(
            x=department_profit.index,
            y=department_profit.values,
            title="Department Profit",
            color=department_profit.values,
            color_continuous_scale='Blues'
            )
            fig.update_layout(showlegend=False, xaxis_title="Department", yaxis_title="Profit")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Service Type Net Billing
            st.subheader("Service Type Net Billing")
            Service_profit = filtered_df.groupby('Service Type')['Net Billing'].sum().sort_values(ascending=True)
            fig = px.bar(
            x=Service_profit.index,
            y=Service_profit.values,
            title="Service Type Net Billing",
            color=Service_profit.values,
            color_continuous_scale='Reds'
            )
            fig.update_layout(showlegend=False, xaxis_title="Service Type", yaxis_title="Net Billing")
            st.plotly_chart(fig, use_container_width=True)
        
        # Net Billing By Insurance Provider"
        col1, col2 = st.columns(2)
        
        with col1:
            insurance_net_billing = filtered_df.groupby('Insurance Provider')['Net Billing'].sum().sort_values()
            fig = px.bar(
                x=insurance_net_billing.index,
                y=insurance_net_billing.values,
                title="Net Billing By Insurance Provider",
                color=insurance_net_billing.values,
                color_continuous_scale='RdYlGn_r'
            )
            fig.update_layout(xaxis_title="Insurance Provider", yaxis_title="Net Billing")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.violin(
                filtered_df,
                x='Room Type',
                y='Room Cost',
                color='Room Type',
                title="Room Revenue by Room Type",
                box=True
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.subheader("Time Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Net Billing Day Analysis
            #st.subheader("Net Billing Day Analysis")
            # Define the correct weekday order
            weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

            # Convert 'Day Name' to a categorical type with the correct order
            filtered_df['Day Name'] = pd.Categorical(filtered_df['Day Name'], categories=weekday_order, ordered=True)

            # Group and sort by the categorical index
            day_profit = filtered_df.groupby('Day Name')['Net Billing'].sum().sort_index()
            fig = px.bar(
            x=day_profit.index,
            y=day_profit.values,
            title="Week Days Net Billing",
            color=day_profit.values,
            color_continuous_scale='Greens'
            )
            fig.update_layout(showlegend=False, xaxis_title="Service Type", yaxis_title="Net Billing")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Net Billing Month Analysis
            #st.subheader("Net Billing Month Analysis")
            #total_billing_by_month = filtered_df.groupby('Month Name')['Total Billing'].sum().sort_values(ascending=True)
            # Define correct month order
            month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                        'July', 'August', 'September', 'October', 'November', 'December']

            # Convert 'Month Name' to categorical with correct order
            filtered_df['Month Name'] = pd.Categorical(filtered_df['Month Name'], categories=month_order, ordered=True)

            # Group and sort by month order
            total_billing_by_month = filtered_df.groupby('Month Name')['Total Billing'].sum().sort_index().iloc[::-1]
            
            fig = px.bar(
                x=total_billing_by_month.values,
                y=total_billing_by_month.index,
                orientation='h',
                title="Total Billing by Month",
                labels={'x': 'Bounds', 'y': 'Month Name'},
                color=total_billing_by_month.values,
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Daily Steps Analysis
        col1, col2 = st.columns(2)
        
        with col1:
            # Group data by 'Quarter of Year
            billing_by_state = filtered_df.groupby('Quarter of Year')['Total Billing'].sum()

            # Create pie chart
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.pie(
                billing_by_state,
                labels=billing_by_state.index,
                autopct='%1.1f%%',
                startangle=140,
                colors=sns.color_palette('pastel')
            )
            ax.set_title('Percentage Billing by Quarter of Year')
            ax.axis('equal')  # Ensures pie is drawn as a circle
            plt.tight_layout()

            # Display in Streamlit
            st.pyplot(fig)

        with col2:
            
            
            daily_net_billing = filtered_df.groupby('Day of Month')['Net Billing'].sum().reset_index()

            # Plotting with Streamlit
            #st.title("📈 Monthly Net Billing Analysis")

            fig, ax = plt.subplots(figsize=(15, 10))
            sns.lineplot(x='Day of Month', y='Net Billing', data=daily_net_billing, ax=ax)
            ax.set_title('Net Billing Monthly', fontsize=30)
            ax.set_xlabel('Day of Month', fontsize=24)
            ax.set_ylabel('Sum of Net Billing', fontsize=24)
            ax.grid(True, linestyle='--', alpha=0.7)
            plt.tight_layout()

            # Display the plot in Streamlit
            st.pyplot(fig, use_container_width=True)
    
    with tab4:
 
        unique_cities = df['City'].unique()
        data = {
            'City': unique_cities,
            'Latitude': [53.3811, 55.9533, 55.8642, 53.8008, 51.4545, 51.5074, 53.4084, 53.4808, 52.4862, 54.9783],
            'Longitude': [-1.4701, -3.1883, -4.2518, -1.5491, -2.5879, -0.1278, -2.9916, -2.2426, -1.8904, -1.6178]
        }
        cities_coordinates_df = pd.DataFrame(data)
        df_merged_geo = pd.merge(df, cities_coordinates_df, on='City', how='left')
        treatments_by_city_diagnosis = df_merged_geo.groupby(['City', 'Diagnosis']).size().reset_index(name='Treatment_Count')


        treatments_geo = pd.merge(treatments_by_city_diagnosis, cities_coordinates_df, on='City', how='left')


        # Create the mapbox scatter plot
        fig = px.scatter_mapbox(
            treatments_geo,
            lat="Latitude",
            lon="Longitude",
            hover_name="City",
            hover_data={"Diagnosis": True, "Treatment_Count": True},
            color="Diagnosis",
            size="Treatment_Count",
            zoom=5,
            height=600,
            title="Distribution for Different Diagnoses by City"
        )

        # Set map style
        fig.update_layout(mapbox_style="open-street-map")

        # Display in Streamlit
        st.plotly_chart(fig, use_container_width=True)

elif page == "🔍 Provider Analysis":
    st.title("🔍 Provider Analysis")
    Providers = pd.read_csv('providers.csv')
    provider_names = list(filtered_df['Provider Name'].unique())    
    provider_name = st.selectbox(
        "Select provider name:", provider_names 
        #["Occupation Analysis", "Gender Analysis", "Age Group Analysis", "Sleep Disorder Analysis"]
    )

    
    i = 0
    while i < len(provider_names):
        if provider_name == provider_names[i]:
            provider_row = Providers[Providers['Provider Name'] == provider_names[i]].iloc[0]
            filtered_df = filtered_df[filtered_df['Provider Name'] == provider_names[i]]
            st.subheader(provider_names[i])
            col1, col2, col3 = st.columns(3)

            with col1:
                        #st.write("🩺 Provider Info Column")
            #st.markdown("### Comprehensive Analysis of Patterns and Health Metrics")
        #for card color 
                        st.markdown("""
                <style>
                /* KPI card */
                [data-testid="stMetric"] {
                background: rgba(050,050,050,0.06);   /* optional: subtle card bg on dark theme */
                border: 1px solid rgba(200,200,200,0.12);
                border-radius: 12px;
                padding: 14px 16px;
                }

                /* label (small text above) */
                [data-testid="stMetricLabel"] > div {
                color: #000000 !important;
                opacity: 0.85;                         /* keep a bit dimmer than value */
                }

                /* main value */
                [data-testid="stMetricValue"] {
                color: #000000 !important;
                opacity: 0.85;
                font-size: 1.4rem;  /* Smaller than 1.6rem */
                font-weight: 700;    
                }

                /* delta text + badge */
                [data-testid="stMetricDelta"] {
                color: #000000 !important;             /* make delta text white */
                }
                [data-testid="stMetricDelta"] svg {      /* make the arrow white too */
                filter: brightness(0) invert(1);
                }

                /* optional: make all plotly charts stretch instead of using use_container_width */
                .user-select-none svg { max-width: 100%; }
                </style>
                """, unsafe_allow_html=True)

                    # Key Metrics Row
                    #row1, row2, row3 = st.rows(3)
                    

                        no_patients_filtered = filtered_df['Patient ID'].nunique()
                        no_patients = df['Patient ID'].nunique()
                        st.metric(
                            label="👥 No of Patients",
                            value=f"{no_patients_filtered:,}",
                            #delta=f"{no_patients_filtered - no_patients:}" if no_patients_filtered != no_patients else None
                        )
                    

                        total_billing_filtered = sum(filtered_df['Total Billing'])
                        total_billing = sum(df['Total Billing'])
                        st.metric(
                            label="😴 Total Billing",
                            value=f"{total_billing_filtered:,} £",
                            #delta=f"{total_billing_filtered - total_billing:} £" if total_billing_filtered != total_billing else None
                        )
                    
                    

                        net_billing_filtered = sum(filtered_df['Net Billing'])
                        net_billing = sum(df['Net Billing'])
                        st.metric(
                            label="😴  Net Billing",
                            value=f"{net_billing_filtered:,} £",
                            #delta=f"{net_billing_filtered - net_billing:} £" if net_billing_filtered != net_billing else None
                        )
                    
                        st.markdown("---")

                
            with col2:
                provider_info = Providers[Providers['Provider Name'] == provider_names[i]].iloc[0].drop(columns=['Image'])
                st.dataframe(provider_info)
            with col3:
#                st.write("📋 Additional Details Column")



                image_path = provider_row['Image']
                st.image(image_path, caption=f"{provider_names[i]}")

                break  # Exit loop after match

        i += 1


elif page == "📋 Data Explorer":
    st.title("📋 Data Explorer")
    
    tab1, tab2, tab3 = st.tabs(["Raw Data", "Summary Statistics", "Custom Analysis"])
    
    with tab1:
        st.subheader("Raw Data View")
        
        # Search and filter options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_col = st.selectbox("Search in column:", filtered_df.columns)
        
        with col2:
            search_term = st.text_input("Search term:", "")
        
        with col3:
            show_rows = st.slider("Rows to display:", 10, 100, 25)
        
        # Apply search
        display_df = filtered_df.copy()
        if search_term:
            display_df = display_df[
                display_df[search_col].astype(str).str.contains(search_term, case=False, na=False)
            ]
        
        # Display data
        st.dataframe(
            display_df.head(show_rows).style.highlight_max(axis=0, subset=['Total Billing', 'Net Billing']),
            use_container_width=True
        )
        
        # Data info
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Dataset Information")
            st.write(f"**Total rows:** {len(display_df)}")
            st.write(f"**Total columns:** {len(display_df.columns)}")
            st.write(f"**Memory usage:** {display_df.memory_usage(deep=True).sum() / 1024:.2f} KB")
        
        with col2:
            st.markdown("### Missing Values")
            missing_data = display_df.isnull().sum()
            missing_data = missing_data[missing_data > 0]
            if len(missing_data) > 0:
                st.dataframe(missing_data, use_container_width=True)
            else:
                st.success("No missing values!")
    
    with tab2:
        st.subheader("Summary Statistics")
        
        # Numeric summary
        st.markdown("### Numeric Variables")
        numeric_cols = filtered_df.select_dtypes(include=[np.number]).columns
        st.dataframe(
            filtered_df[numeric_cols].describe().T.style.background_gradient(cmap='coolwarm'),
            use_container_width=True
        )
        
        # Categorical summary
        st.markdown("### Categorical Variables")
        categorical_cols = filtered_df.select_dtypes(include=['object']).columns
        
        for col in categorical_cols:
            with st.expander(f"📊 {col}"):
                value_counts = filtered_df[col].value_counts()
                
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.dataframe(value_counts, use_container_width=True)
                
                with col2:
                    fig = px.bar(
                        x=value_counts.index,
                        y=value_counts.values,
                        title=f"Distribution of {col}",
                        labels={'x': col, 'y': 'Count'}
                    )
                    fig.update_xaxes(tickangle=45)
                    st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.subheader("Custom Analysis Builder")
        
        st.markdown("*Build your own visualizations*")
        
        chart_type = st.selectbox(
            "Select Chart Type:",
            ["Bar Chart", "Line Chart", "Scatter Plot", "Box Plot", "Histogram", "Pie Chart"]
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            x_axis = st.selectbox("X-axis:", filtered_df.columns, index=2)
        
        with col2:
            if chart_type not in ["Histogram", "Pie Chart"]:
                y_axis = st.selectbox("Y-axis:", filtered_df.columns, index=3)
        
        color_by = st.selectbox("Color by (optional):", ["None"] + list(filtered_df.columns))
        color_col = None if color_by == "None" else color_by
        
        # Generate chart
        st.markdown("---")
        
        try:
            if chart_type == "Bar Chart":
                if filtered_df[x_axis].dtype == 'object':
                    data = filtered_df.groupby(x_axis)[y_axis].mean().reset_index()
                    fig = px.bar(data, x=x_axis, y=y_axis, color=color_col, title=f"{y_axis} by {x_axis}")
                else:
                    fig = px.bar(filtered_df, x=x_axis, y=y_axis, color=color_col, title=f"{y_axis} vs {x_axis}")
                
            elif chart_type == "Line Chart":
                fig = px.line(filtered_df, x=x_axis, y=y_axis, color=color_col, title=f"{y_axis} over {x_axis}")
            
            elif chart_type == "Scatter Plot":
                fig = px.scatter(filtered_df, x=x_axis, y=y_axis, color=color_col, title=f"{y_axis} vs {x_axis}")
            
            elif chart_type == "Box Plot":
                fig = px.box(filtered_df, x=x_axis, y=y_axis, color=color_col, title=f"{y_axis} distribution by {x_axis}")
            
            elif chart_type == "Histogram":
                fig = px.histogram(filtered_df, x=x_axis, color=color_col, title=f"Distribution of {x_axis}")
            
            elif chart_type == "Pie Chart":
                value_counts = filtered_df[x_axis].value_counts()
                fig = px.pie(values=value_counts.values, names=value_counts.index, title=f"Distribution of {x_axis}")
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error creating chart: {str(e)}")
            st.info("Try selecting different columns or chart type.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #7f8c8d;'>
    <p>Sleep Health Analysis Dashboard | Built with Streamlit</p>
    <p>Data Source: Sleep Health and Lifestyle Dataset</p>
</div>
""", unsafe_allow_html=True)